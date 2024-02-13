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
        self.windows = []
        self.placeorder_window = None
        self.monitor_model_path = ""
        self.stoploss_model_path = ""
        
    def initUI(self, init_symbol=""):
        val_int = QIntValidator()
        base_layout = QHBoxLayout()
        self.monitor_canvas = canvas.RealTimePlot()
        self.monitor_canvas.canvas.set_major_formatter("%H:%M:%S")
        self.monitor_canvas.canvas.destroy_prev = False
        self.monitor_canvas.canvas.set_title("Realtime Monitoring")
        
        self.prev_price_list = QListWidget()
        
        self.symbol_input = QLineEdit(self)
        self.load_model_btn = QPushButton("Load Model", self)
        self.model_lags_input = QLineEdit(self)
        self.update_interval_input = QLineEdit(self)
        
        self.placeorder_btn = QPushButton("Place Order", self)
        self.aggregate_btn = QPushButton("Aggregate", self)
        
        self.run_btn = QPushButton("Run", self)
        self.stop_btn = QPushButton("Stop", self)

        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        controls_layout = QVBoxLayout()
        interact_layout = QHBoxLayout()
        env_info_layout = QHBoxLayout()
        runstop_layout = QHBoxLayout()
        
        self.symbol_input.setText(init_symbol)
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
        
        controls_layout.addLayout(interact_layout)
        controls_layout.addLayout(env_info_layout)
        controls_layout.addLayout(runstop_layout)
        base_layout.addLayout(controls_layout)
        base_layout.addWidget(self.prev_price_list)
        
        self.prev_price_list.itemClicked.connect(self.prev_price_list_item_clicked)
        self.placeorder_btn.clicked.connect(self.placeorder_btn_cliked)
        self.aggregate_btn.clicked.connect(self.aggregate_btn_clicked)
        self.load_model_btn.clicked.connect(self.load_model_btn_clicked)
        self.run_btn.clicked.connect(self.run_btn_clicked)
        self.stop_btn.clicked.connect(self.stop_btn_clicked)
        
        self.setLayout(base_layout)
    
    def prev_price_list_item_clicked(self, item):
        if self.placeorder_window != None and self.placeorder_window.closed != True:
            text = item.text()
            price = float(text.split(" : ")[1])
            self.placeorder_window.set_price(price)
    
    def placeorder_btn_cliked(self):
        symbol = self.symbol_input.text().strip()
        self.placeorder_window = PlaceOrderWindow()
        self.placeorder_window.initUI(symbol)
        self.windows.append(self.placeorder_window)
        self.placeorder_window.show()
    
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
                profit += ((units * price) - ((units * price) * (0.0025)))
                
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
        
        self.montior_thread = QTMonitorStock.QTMonitorStockThread(symbol, models.load(self.monitor_model_path), lags, interval)
        self.montior_thread.signal.connect(self.monitor_thread_result_handler)
        self.montior_thread.start()
        
    def stop_btn_clicked(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.montior_thread.stop()
        
    def monitor_thread_result_handler(self, info):
        if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
            return
        trade_type = info.trade_type
        date = info.date
        price = info.price
        self.monitor_canvas.update_plot(date, price)
        t = ""
        if trade_type != tradeinfo.TradeType.NONE:
            logger.log_monitor(date.strftime("%Y-%m-%d %H:%M:%S"), price, trade_type)
            if trade_type == tradeinfo.TradeType.BUY:
                t = "Buy"
                self.monitor_canvas.canvas.add_text_at_value("Buy", date, price, color="green")    
            elif trade_type == tradeinfo.TradeType.SELL:
                t = "Sell"
                self.monitor_canvas.canvas.add_text_at_value("Sell", date, price, color="red")
        
        self.prev_price_list.addItem(f"{t}{date.strftime('%Y-%m-%d %H:%M:%S')} : {price}")