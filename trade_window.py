from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, datetime
import QTMonitorStock, QTMonitorStoploss, tradeinfo
import models, resources.canvas as canvas, data, QTLearn, environment, logger
from tensorflow import keras
import pandas as pd

class TradeWindow(QDialog):
    def __init__(self):
        super(TradeWindow, self).__init__(None)
        self.log_file = ""
        self.trading = False
        self.center()
    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.trading:
            self.montior_thread.stop()
        self.trading = False
        a0.accept()
    
    def initUI(self, symbol=""):
        self.symbol = symbol.upper()
        self.setWindowTitle(f"Trade {self.symbol}")
        layout = QHBoxLayout()
        canvas_layout = QVBoxLayout()
        parameter_layout = QHBoxLayout()
        order_layout = QVBoxLayout()
        order_inputs_layout = QHBoxLayout()
        order_btns_layout = QHBoxLayout()
        
        val = QIntValidator()
        self.canvas = canvas.RealTimePlot()
        lags_label = QLabel("Lags : ")
        self.lags_input = QLineEdit(self)
        update_interval_label = QLabel("Update Interval : ")
        self.update_interval_input = QLineEdit(self)
        self.start_trade_btn = QPushButton("Start Trade", self)
        self.stoploss_btn = QPushButton("Stoploss", self)
        self.price_list = QListWidget()
        price_label = QLabel("Price : ")
        self.price_input = QLineEdit(self)
        units_label = QLabel("Units : ")
        self.units_input = QLineEdit(self)
        self.buy_btn = QPushButton("Buy", self)
        self.sell_btn = QPushButton("Sell", self)
        self.create_savepath_btn = QPushButton("Select Save File", self)
        self.open_savepath_btn = QPushButton("Open Save File", self)
        self.calculate_profit_btn = QPushButton("Calculate Profit", self)
        self.profit_label = QLabel("Profit")
        
        self.lags_input.setValidator(val)
        self.lags_input.setText("3")
        self.update_interval_input.setValidator(val)
        self.update_interval_input.setText("1")
        self.start_trade_btn.clicked.connect(self.strat_trade_btn_clicked)
        self.stoploss_btn.clicked.connect(self.stoploss_btn_clicked)
        self.units_input.setValidator(val)
        self.canvas.canvas.set_major_formatter("%H:%M:%S")
        self.canvas.canvas.destroy_prev = False
        self.canvas.canvas.set_title(f"{self.symbol}")
        self.price_list.itemClicked.connect(self.price_list_item_clicked)
        self.buy_btn.clicked.connect(self.buy_btn_clicked)
        self.sell_btn.clicked.connect(self.sell_btn_clicked)
        self.create_savepath_btn.clicked.connect(self.select_savepath_clicked)
        self.open_savepath_btn.clicked.connect(self.open_savepath_btn_clicked)
        self.calculate_profit_btn.clicked.connect(self.calculate_profit_btn_clicked)
        
        parameter_layout.addWidget(lags_label)
        parameter_layout.addWidget(self.lags_input)
        parameter_layout.addWidget(update_interval_label)
        parameter_layout.addWidget(self.update_interval_input)
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addLayout(parameter_layout)
        hdiv = QHBoxLayout()
        hdiv.addWidget(self.start_trade_btn)
        hdiv.addWidget(self.stoploss_btn)
        canvas_layout.addLayout(hdiv)
        
        order_inputs_layout.addWidget(price_label)
        order_inputs_layout.addWidget(self.price_input)
        order_inputs_layout.addWidget(units_label)
        order_inputs_layout.addWidget(self.units_input)
        order_btns_layout.addWidget(self.buy_btn)
        order_btns_layout.addWidget(self.sell_btn)
        order_btns_layout.addWidget(self.create_savepath_btn)
        order_btns_layout.addWidget(self.open_savepath_btn)
        order_btns_layout.addWidget(self.calculate_profit_btn)
        order_layout.addWidget(self.price_list)
        order_layout.addLayout(order_inputs_layout)
        order_layout.addLayout(order_btns_layout)
        order_layout.addWidget(self.profit_label)
        layout.addLayout(canvas_layout, stretch=3)
        layout.addLayout(order_layout, stretch=1)
        self.setLayout(layout)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def price_list_item_clicked(self, item):
        price = str(item.text().split(' / ')[1])
        self.price_input.setText(price)
    def select_savepath_clicked(self):
        fname = QFileDialog.getSaveFileName(self, '.json save file', f"./my {self.symbol} trade 001.json", "Json (*.json)")[0]
        if fname == "":
            return
        self.log_file = fname
    def open_savepath_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .json trade log', './', "Json (*.json)")[0]
        if fname == '':
            return
        self.log_file = fname
    def _log_trade(self, action):
        if self.log_file == "":
            QMessageBox.information(self, "Error", "Select Your Trading Log File First.")
            return
        units = self.units_input.text()
        price = self.price_input.text()
        logger.log_trade(self.symbol, action, units, price, path=self.log_file)
    def buy_btn_clicked(self):
        self._log_trade("buy")
    def sell_btn_clicked(self):
    
    
        self._log_trade("sell")
    def monitor_thread_result_handler(self, info):
        if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
            return
        trade_type = info.trade_type
        date = info.date
        price = info.price
        self.canvas.update_plot(date, price)
        t = "*"
        if info.info_type == tradeinfo.InfoType.HOLDING:
            t = "Hold"
        elif trade_type != tradeinfo.TradeType.NONE:
            if trade_type == tradeinfo.TradeType.BUY:
                t = "Buy"
                self.canvas.canvas.add_text_at_value("Buy", date, price, color="green")    
            elif trade_type == tradeinfo.TradeType.SELL:
                if info.info_type == tradeinfo.InfoType.TAKEPROFIT:
                    t = "Sell - Take Profit"
                elif info.info_type == tradeinfo.InfoType.STOPLOSS:
                    t = "Sell - Stop Loss"
                self.canvas.canvas.add_text_at_value("Sell", date, price, color="red")
        
        self.price_list.addItem(f"{t} / {price}")
    def monitor_stoploss_thread_handler(self, info):
        #date = info.date
        price = info.price
        if info.trade_type == tradeinfo.TradeType.SELL:
            self.canvas.canvas.add_axhline_at_value(price.iloc[0], "r")
    
    def strat_trade_btn_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(None, "Folder For New Model", "", QFileDialog.ShowDirsOnly)
        if folder_path:
            self.model_paths = [os.path.join(folder_path, f"sideway.keras"), os.path.join(folder_path, f"trade.keras")]
        else:
            return
        for i in range(0, len(self.model_paths)):
            if not os.path.exists(self.model_paths[i]):
                QMessageBox.information(self, "Error", "Select your agent please.")
                return
        
        self.canvas.clear()
        self.canvas.canvas.set_major_formatter("%H:%M:%S")
        self.canvas.canvas.destroy_prev = False
        
        str_lags = self.lags_input.text()
        str_update_interval = self.update_interval_input.text()
        if str_lags == "" or str_update_interval == "":
            QMessageBox.information(self, "Error", "Weierd inputs.")
            return
        lags = int(str_lags)
        interval = int(str_update_interval)
        target = f"{self.symbol}_Price"
        df = pd.DataFrame({target:[], 'Datetime':[]})
        df.set_index('Datetime')
        
        agents = []
        for i in range(0, len(self.model_paths)):
            agents.append(keras.models.load_model(self.model_paths[i]))
        env = environment.StockMarketEnvironment(agents, df, target, lags=lags)
        
        self.trading = True
        self.montior_thread = QTMonitorStock.QTMonitorStockThread(self.symbol, env, interval)
        self.montior_thread.signal.connect(self.monitor_thread_result_handler)
        self.montior_thread.start()
    def stoploss_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.stoploss_model_path = fname
        str_lags = self.lags_input.text()
        str_update_interval = self.update_interval_input.text()
        if str_lags == "" or str_update_interval == "":
            QMessageBox.information(self, "Error", "Weierd inputs.")
            return
        if not self.trading:
            QMessageBox.information(self, "Error", "Before running stoploss, Run Stock Monitoring.")
            return
        lags = int(str_lags)
        interval = int(str_update_interval)
        self.monitor_stoploss_thread = QTMonitorStoploss.QTMonitorStockThread(self.stoploss_model_path, self.symbol, lags, interval)
        self.monitor_stoploss_thread.signal.connect(self.monitor_stoploss_thread_handler)
        self.monitor_stoploss_thread.start()
    
    def calculate_profit_btn_clicked(self):
        if not os.path.exists(self.log_file):
            QMessageBox.information(self, "Error", "Log file not selected.")
            return
        profit = str(logger.calculate_trade(self.symbol, path=self.log_file))
        self.profit_label.setText(f"{datetime.datetime.now().strftime('%H:%M:%S')} : {profit}")