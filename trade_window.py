from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, datetime
import QTMonitorStock, QTMonitorStoploss, tradeinfo
from handlers.koreainvest import *
from secret import keys
import matplotlib.dates as mdates
import models, resources.canvas as canvas, data, QTLearn, environment, logger
from tensorflow import keras
import pandas as pd

class TradeWindow(QDialog):
    def __init__(self):
        super(TradeWindow, self).__init__(None)
        self.log_file = ""
        self.trading = False
        self.interval = 60 # 1min
        self.center()
    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.trading:
            self.montior_thread.stop()
        self.trading = False
        a0.accept()
    
    def initUI(self, symbol="", timezone='America/New_York'):
        self.symbol = symbol.upper()
        self.timezone = timezone
        '''
        if self.timezone == data.TIMEZONE_NYSE:
            exchange = "나스닥"
        elif self.timezone == data.TIMEZONE_KRX:
            exchange = "서울"
        
        self.broker = create_broker(keys.KEY, keys.APISECRET, keys.ACCOUNT_NO, exchange, True)
        '''
        
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
        self.start_trade_btn = QPushButton("Start Trade", self)
        self.stoploss_btn = QPushButton("Stoploss", self)
        asking_price_list_label = QLabel("Asking Prices")
        self.asking_price_list = QListWidget()
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
        self.start_trade_btn.clicked.connect(self.strat_trade_btn_clicked)
        self.stoploss_btn.clicked.connect(self.stoploss_btn_clicked)
        self.units_input.setValidator(val)
        self.canvas.canvas.set_major_formatter("%H:%M:%S")
        self.canvas.canvas.destroy_prev = False
        self.canvas.canvas.set_title(f"{self.symbol}")
        self.asking_price_list.itemClicked.connect(self.asking_price_list_item_clicked)
        self.price_list.itemClicked.connect(self.price_list_item_clicked)
        self.buy_btn.clicked.connect(self.buy_btn_clicked)
        self.sell_btn.clicked.connect(self.sell_btn_clicked)
        self.create_savepath_btn.clicked.connect(self.select_savepath_clicked)
        self.open_savepath_btn.clicked.connect(self.open_savepath_btn_clicked)
        self.calculate_profit_btn.clicked.connect(self.calculate_profit_btn_clicked)
        
        parameter_layout.addWidget(lags_label)
        parameter_layout.addWidget(self.lags_input)
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
        order_layout.addWidget(asking_price_list_label)
        order_layout.addWidget(self.asking_price_list)
        order_layout.addWidget(self.price_list)
        order_layout.addLayout(order_inputs_layout)
        order_layout.addLayout(order_btns_layout)
        order_layout.addWidget(self.profit_label)
        layout.addLayout(canvas_layout, stretch=3)
        layout.addLayout(order_layout, stretch=1)
        self.setLayout(layout)
    
    def set_asking_price(self, buys_p, sells_p, buys_n, sells_n, sum_of_buys, sum_of_sells):
        self.asking_price_list.clear()
        
        self.asking_price_list.addItem(f"Sum of Selling Asking Price Amount : {sum_of_sells}")
        i = len(sells_p)
        for aps in sells_p[::-1]:
            self.asking_price_list.addItem(f"Selling {i} | {sells_n[i-1]} | {aps}")
            i -= 1
        i = 1
        for apb in buys_p:
            self.asking_price_list.addItem(f"Buying {i} | {buys_n[i-1]} | {apb}")
            i += 1
        self.asking_price_list.addItem(f"Sum of Buying Asking Price Amount : {sum_of_buys}")
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def asking_price_list_item_clicked(self, item):
        txt = str(item.text())
        header = txt.split(' ')[0]
        if header == "Buying" or header == "Selling":
            price = txt.split(' | ')[2]
            units = txt.split(' | ')[1]
            self.price_input.setText(price)
            self.units_input.setText(units)
    
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
        
    def draw_assistant_lines(self, df, date, window):
        self.canvas.canvas.add_sub_line_data(self.upper_band_line, date, df['upper'].iloc[-1])
        self.canvas.canvas.add_sub_line_data(self.lower_band_line, date, df['lower'].iloc[-1])
    
    def monitor_thread_result_handler(self, info):
        if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
            return
        trade_type = info.trade_type
        info_type = info.info_type
        
        if info_type == tradeinfo.InfoType.ASKINGPRICE:
            info = info.infos
            self.set_asking_price(info["apb"], info["aps"], info["apb_n"], info["aps_n"], info["s_apb_n"], info["s_aps_n"])
            self.candlechart_prices.append(info["predicted_price"])
            if len(self.canvas.canvas.candlesticks) > 0:
                self.canvas.canvas.update_candlestick(self.candlechart_x, self.candlechart_prices, self.interval)
            if self.create_new_candle:
                self.canvas.canvas.add_candlestick(self.candlechart_x, self.candlechart_prices)
                self.create_new_candle = False
            
        elif info_type == tradeinfo.InfoType.SIGNED:
            info = info.infos
            QMessageBox.information(self, "Signed", f"Order no : {info['values'][2]}")
        else:
            date = info.date
            price = info.price
            today = data.today(self.timezone)
            self.candlechart_x = mdates.date2num([data.today_minus_seconds(today, self.interval), today])
            self.candlechart_prices = []
            self.create_new_candle = True
            self.canvas.update_plot(date, price)
            window = 20
            if len(self.env.df) > window:
                self.draw_assistant_lines(self.env.df, date, window)
            t = "View"
            if info_type == tradeinfo.InfoType.HOLDING:
                t = "Hold"
            elif trade_type != tradeinfo.TradeType.NONE:
                if trade_type == tradeinfo.TradeType.BUY:
                    t = "Buy"
                    self.canvas.canvas.plot_a_point(date, price, "go")
                elif trade_type == tradeinfo.TradeType.SELL:
                    if info.info_type == tradeinfo.InfoType.TAKEPROFIT:
                        t = "Sell - Take Profit"
                    elif info.info_type == tradeinfo.InfoType.STOPLOSS:
                        t = "Sell - Stop Loss"
                    if info.info_type == tradeinfo.InfoType.TAKEPROFIT or info.info_type == tradeinfo.InfoType.STOPLOSS:
                        self.canvas.canvas.plot_a_point(date, price, "ro")
                if t == "Buy" or "Sell" in t:
                    self.price_list.addItem(f"{t} / {price}")
                    self.price_list.scrollToBottom()

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
        
        self.upper_band_line = self.canvas.canvas.create_sub_line("--", "red")
        self.lower_band_line = self.canvas.canvas.create_sub_line("--", "green")
        
        str_lags = self.lags_input.text()
        if str_lags == "":
            QMessageBox.information(self, "Error", "Weierd inputs.")
            return
        lags = int(str_lags)
        target = f"{self.symbol}_Price"
        df = pd.DataFrame({target:[], 'Datetime':[]})
        df.set_index('Datetime')
        
        agents = []
        for i in range(0, len(self.model_paths)):
            agents.append(keras.models.load_model(self.model_paths[i]))
        self.env = environment.StockMarketEnvironment(agents, df, target, lags=lags)
        
        self.trading = True
        #FOR TEST
        #FOR TEST
        self.broker = ""
        #FOR TEST
        #FOR TEST
        today = data.today(self.timezone)
        self.create_new_candle = True
        self.candlechart_x = mdates.date2num([data.today_minus_seconds(today, self.interval), today])
        self.candlechart_prices = []
        self.montior_thread = QTMonitorStock.QTMonitorStockThread(self.symbol, self.broker, self.env, self.interval, self.timezone)
        self.montior_thread.signal.connect(self.monitor_thread_result_handler)
        self.montior_thread.start()
    def stoploss_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.stoploss_model_path = fname
        str_lags = self.lags_input.text()
        if str_lags == "":
            QMessageBox.information(self, "Error", "Weierd inputs.")
            return
        if not self.trading:
            QMessageBox.information(self, "Error", "Before running stoploss, Run Stock Monitoring.")
            return
        lags = int(str_lags)
        self.monitor_stoploss_thread = QTMonitorStoploss.QTMonitorStockThread(self.stoploss_model_path, self.symbol, lags, 60, self.timezone)
        self.monitor_stoploss_thread.signal.connect(self.monitor_stoploss_thread_handler)
        self.monitor_stoploss_thread.start()
    
    def calculate_profit_btn_clicked(self):
        if not os.path.exists(self.log_file):
            QMessageBox.information(self, "Error", "Log file not selected.")
            return
        profit = str(logger.calculate_trade(self.symbol, path=self.log_file))
        self.profit_label.setText(f"{datetime.datetime.now().strftime('%H:%M:%S')} : {profit}")