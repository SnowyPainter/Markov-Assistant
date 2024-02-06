from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import QTMonitorStock, QTMonitorStoploss
from placeorder_window import *
import datetime, os
import models, resources.canvas as canvas, tradeinfo, logger

class MonitorStockWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Stock")
        self.resize(1024, 600)
        self.initUI()
        self.windows = []
        self.monitor_model_path = ""
        self.stoploss_model_path = ""
        
    def initUI(self, init_symbol=""):
        val_int = QIntValidator()
        base_layout = QVBoxLayout()
        self.monitor_canvas = canvas.RealTimePlot()
        self.monitor_canvas.canvas.set_major_formatter("%H:%M:%S")
        self.monitor_canvas.canvas.destroy_prev = False
        self.monitor_canvas.canvas.set_title("Realtime Monitoring")
        
        self.symbol_input = QLineEdit(self)
        self.load_model_btn = QPushButton("Load Model", self)
        self.model_lags_input = QLineEdit(self)
        self.update_interval_input = QLineEdit(self)
        
        self.placeorder_btn = QPushButton("Place Order", self)
        self.aggregate_btn = QPushButton("Aggregate", self)
        
        self.run_btn = QPushButton("Run", self)
        self.stop_btn = QPushButton("Stop", self)
        self.purchased_price_input = QLineEdit(self)
        self.stoploss_btn = QPushButton("Stop Loss", self)
        self.load_stoploss_model_btn = QPushButton("Load", self)
        
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stoploss_btn.setEnabled(False)
        
        controls_layout = QVBoxLayout()
        interact_layout = QHBoxLayout()
        env_info_layout = QHBoxLayout()
        runstop_layout = QHBoxLayout()
        
        self.symbol_input.setText(init_symbol)
        self.purchased_price_input.setPlaceholderText("Purchased Price")
        self.model_lags_input.setText("3")
        self.update_interval_input.setText("1")
        self.model_lags_input.setValidator(val_int)
        self.update_interval_input.setValidator(val_int)
        
        controls_layout.addWidget(self.monitor_canvas)
        interact_layout.addWidget(self.placeorder_btn)
        interact_layout.addWidget(self.aggregate_btn)
        env_info_layout.addWidget(self.symbol_input)
        env_info_layout.addWidget(self.load_model_btn)
        env_info_layout.addWidget(self.model_lags_input)
        env_info_layout.addWidget(self.update_interval_input)
        runstop_layout.addWidget(self.run_btn)
        runstop_layout.addWidget(self.stop_btn)
        runstop_layout.addWidget(self.purchased_price_input)
        runstop_layout.addWidget(self.stoploss_btn)
        runstop_layout.addWidget(self.load_stoploss_model_btn)
        
        controls_layout.addLayout(interact_layout)
        controls_layout.addLayout(env_info_layout)
        controls_layout.addLayout(runstop_layout)
        base_layout.addLayout(controls_layout)
        
        self.placeorder_btn.clicked.connect(self.placeorder_btn_cliked)
        self.aggregate_btn.clicked.connect(self.aggregate_btn_clicked)
        self.load_model_btn.clicked.connect(self.load_model_btn_clicked)
        self.run_btn.clicked.connect(self.run_btn_clicked)
        self.stop_btn.clicked.connect(self.stop_btn_clicked)
        self.stoploss_btn.clicked.connect(self.stoploss_btn_clicked)
        self.load_stoploss_model_btn.clicked.connect(self.load_stoploss_model_btn_clicked)
        
        self.setLayout(base_layout)
    
    def placeorder_btn_cliked(self):
        symbol = self.symbol_input.text().strip()
        window = PlaceOrderWindow()
        window.initUI(symbol)
        self.windows.append(window)
        window.show()
    
    def aggregate_btn_clicked(self):
        logs = logger.read_all_trades()
        if logs == []:
            QMessageBox.information(None, "Error", "There's no trades you did.")
            return
        
        stock = self.symbol_input.text().strip()
        logs = [item for item in logs if item.get("stock") == stock]
        profit = 0
        for item in logs:
            action = item.get("action")
            units = float(item.get('units'))
            price = float(item.get("price"))
            if action == "buy":
                profit -= (units * price)
            if action == "sell":
                profit += ((units * price) * (1-float("0."+self.bakctest_fee_input.text())))
                
        QMessageBox.information(self, "Self-Trading Profit", f"Profit: {profit}")
    
    def load_model_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.monitor_model_path = fname
      
    def run_btn_clicked(self):
        self.monitor_canvas.clear()
        self.monitor_canvas.canvas.set_major_formatter("%H:%M:%S")
        
        symbol = self.symbol_input.text().strip()
        lags = int(self.model_lags_input.text())
        interval = int(self.update_interval_input.text())
        if symbol == "":
            QMessageBox.information(self, "Error", "Symbol must be not empty.")
            return
        if not os.path.exists(self.monitor_model_path):
            QMessageBox.information(self, "Error", "Select your agent please.")
            return
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.stoploss_btn.setEnabled(True)
        
        self.montior_thread = QTMonitorStock.QTMonitorStockThread(symbol, models.load(self.monitor_model_path), lags, interval)
        self.montior_thread.signal.connect(self.monitor_thread_result_handler)
        self.montior_thread.start()
        
    def stop_btn_clicked(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stoploss_btn.setEnabled(False)
        self.montior_thread.stop()
        
    def monitor_thread_result_handler(self, info):
        if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
            return
        trade_type = info.trade_type
        date = info.date
        price = info.price
        self.monitor_canvas.update_plot(date, price)
        if trade_type != tradeinfo.TradeType.NONE:
            logger.log_monitor(date.strftime("%Y-%m-%d %H:%M:%S"), price, trade_type)
            if trade_type == tradeinfo.TradeType.BUY:
                self.monitor_canvas.canvas.add_text_at_value("Buy", date, price, color="green")    
            elif trade_type == tradeinfo.TradeType.SELL:
                self.monitor_canvas.canvas.add_text_at_value("Sell", date, price, color="red")
    
    def load_stoploss_model_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.stoploss_model_path = fname
    
    def stoploss_btn_clicked(self):
        if self.run_btn.isEnabled():
            QMessageBox.information(self, "Error", "Before using it, run monitoring.")
            return
        if not os.path.exists(self.stoploss_model_path):
            QMessageBox.information(self, "Error", "Select your agent for stop-loss please.")
            return
        price = float(self.purchased_price_input.text().strip())
        symbol = self.symbol_input.text().strip()
        if price == 0 or symbol == "":
            QMessageBox.information(self, "Error", "Weired inputs.")
            return
        
        self.monitor_stoploss_thread = QTMonitorStoploss.QTMonitorStockThread(self.stoploss_model_path, price, symbol,3)
        self.monitor_stoploss_thread.signal.connect(self.monitor_stoploss_thread_handler)
        self.monitor_stoploss_thread.start()
        
    def monitor_stoploss_thread_handler(self, info):
        if info.info_type == tradeinfo.TradeType.SELL:
            print(info.price)