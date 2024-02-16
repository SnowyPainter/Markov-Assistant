from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import QTMonitorStock, QTMonitorStoploss
from placeorder_window import *
import datetime, os
import models, resources.canvas as canvas, tradeinfo, logger
from train_stoploss_model_window import *

class MonitorStoplossWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1024, 600)
        self.windows = []
        self.stoploss_model_path = ""
        
    def initUI(self, init_symbol=""):
        self.setWindowTitle("Monitor Stoploss")
        val_int = QIntValidator()
        base_layout = QHBoxLayout()
        self.prev_price_list = QListWidget()
        
        self.monitor_canvas = canvas.RealTimePlot()
        self.monitor_canvas.canvas.set_major_formatter("%H:%M:%S")
        self.monitor_canvas.canvas.destroy_prev = False
        self.monitor_canvas.canvas.set_title("Stoploss Monitoring")
        
        self.symbol_input = QLineEdit(self)
        self.model_lags_input = QLineEdit(self)
        self.update_interval_input = QLineEdit(self)
        self.stoploss_btn = QPushButton("Stop Loss", self)
        self.stop_btn = QPushButton("Stop Monitoring", self)
        self.load_stoploss_model_btn = QPushButton("Load", self)
        self.train_new_stoploss_model_btn = QPushButton("Train New Stoploss Model", self)
        
        controls_layout = QVBoxLayout()
        interact_layout = QHBoxLayout()
        env_info_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        
        self.symbol_input.setText(init_symbol)
        self.model_lags_input.setText("3")
        self.update_interval_input.setText("1")
        self.model_lags_input.setValidator(val_int)
        self.update_interval_input.setValidator(val_int)
        self.train_new_stoploss_model_btn.clicked.connect(self.train_new_stoploss_model_btn_clicked)
        self.stoploss_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.monitor_canvas)
        env_info_layout.addWidget(self.symbol_input)
        env_info_layout.addWidget(self.load_stoploss_model_btn)
        env_info_layout.addWidget(self.model_lags_input)
        env_info_layout.addWidget(self.update_interval_input)
        bottom_layout.addWidget(self.stoploss_btn)
        bottom_layout.addWidget(self.stop_btn)
        bottom_layout.addWidget(self.train_new_stoploss_model_btn)
        controls_layout.addLayout(interact_layout)
        controls_layout.addLayout(env_info_layout)
        controls_layout.addLayout(bottom_layout)
        base_layout.addLayout(controls_layout, stretch=3)
        base_layout.addWidget(self.prev_price_list, stretch=1)
        self.stoploss_btn.clicked.connect(self.stoploss_btn_clicked)
        self.stop_btn.clicked.connect(self.stop_btn_clicked)
        self.load_stoploss_model_btn.clicked.connect(self.load_stoploss_model_btn_clicked)
        
        self.setLayout(base_layout)

    def load_stoploss_model_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.stoploss_model_path = fname
    
    def stop_btn_clicked(self):
        self.stoploss_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.monitor_stoploss_thread.stop()
    
    def stoploss_btn_clicked(self):
        if not os.path.exists(self.stoploss_model_path):
            QMessageBox.information(self, "Error", "Select your agent for stop-loss please.")
            return
        symbol = self.symbol_input.text().strip()
        lags = int(self.model_lags_input.text())
        wait_interval = int(self.update_interval_input.text().strip())
        if symbol == "":
            QMessageBox.information(self, "Error", "Weired inputs.")
            return
        self.stoploss_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.monitor_stoploss_thread = QTMonitorStoploss.QTMonitorStockThread(self.stoploss_model_path, symbol, lags, wait_interval)
        self.monitor_stoploss_thread.signal.connect(self.monitor_stoploss_thread_handler)
        self.monitor_stoploss_thread.start()
        
    def monitor_stoploss_thread_handler(self, info):
        date = info.date
        price = info.price
        if info.info_type != tradeinfo.InfoType.WAITFORNEWDATA:
            self.prev_price_list.addItem(f"{date.strftime('%Y-%m-%d %H:%M:%S')} : {price.iloc[0]}")
            self.monitor_canvas.update_plot(date, price)    
        if info.trade_type == tradeinfo.TradeType.SELL:
            self.monitor_canvas.canvas.add_text_at_value("Stop Loss", date, price, color="red")
            QMessageBox.information(self, "STOP LOSS", f"Stop loss for {price.iloc[0]}")
            
    def train_new_stoploss_model_btn_clicked(self):
        window = TrainStoplossModelWindow()
        window.initUI(self.symbol_input.text().strip())
        self.windows.append(window)
        window.show()