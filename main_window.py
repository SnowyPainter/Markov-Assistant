import sys, datetime
import data, models, QTBacktest, resources.canvas as canvas
import handlers.window_handler as window_handler
import pandas as pd
import os, json
import portfolio
from tensorflow import keras
from train_result_window import *
from trade_window import *
from train_rlmodel_window import *
from monitor_stoploss_window import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MyApp(QMainWindow, window_handler.Handler):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.windows = []
        self.dnn_train_result = None
        self.selected_stock = ""
        self.lstm_train_result = None
        self.backtest_model_path = None
        self.backtesting = False
        self.backtest_trade_model_path = ""
        self.portfolio_file = "./portfolio.json"
        self.load_portfolio()
        self.addWidgets()
        self.loadRecentNetWealth()
    
    def loadRecentNetWealth(self):
        try:
            with open('./log/backtest.json', 'r') as file:
                data = json.load(file)
                net_wealth = data[-1]["net_wealth"]
                self.backtest_option_amount_input.setText(str(net_wealth))
        except:
            self.backtest_option_amount_input.setText("10000")

    def initLayouts(self):
        base_layout = QHBoxLayout()
        self.portfolio_layout = QVBoxLayout()
        self.portfolio_add_layout = QHBoxLayout()
        self.portfolio_list_layout = QVBoxLayout()
        self.portfolio_evaluate_layout = QVBoxLayout()
        
        self.chart_layout = QVBoxLayout()
        self.lstm_layout = QVBoxLayout()
        self.lstm_panel_layout = QVBoxLayout()
        self.lstm_control_btns_layout = QHBoxLayout()
        self.lstm_control_inputs_layout = QHBoxLayout()
        self.lstm_control_layout = QVBoxLayout()
        
        self.dnn_layout = QVBoxLayout()
        self.dnn_panel_layout = QVBoxLayout()
        self.dnn_control_btns_layout = QHBoxLayout()
        self.dnn_control_inputs_layout = QHBoxLayout()
        self.dnn_control_layout = QVBoxLayout()
        
        self.backtest_layout = QVBoxLayout()
        self.backtest_panel_layout = QVBoxLayout()
        self.backtest_control_layout = QVBoxLayout()
        self.backtest_control_option_layout = QHBoxLayout()
        self.backtest_control_btn_layout = QHBoxLayout()
        self.backtest_control_input_layout = QHBoxLayout()
        self.backtest_control_simulate_layout = QHBoxLayout()
        
        self.portfolio_layout.addLayout(self.portfolio_add_layout)
        self.portfolio_layout.addLayout(self.portfolio_list_layout)
        self.portfolio_layout.addLayout(self.portfolio_evaluate_layout)
        self.lstm_layout.addLayout(self.lstm_panel_layout)
        self.lstm_layout.addLayout(self.lstm_control_layout)
        self.lstm_control_layout.addLayout(self.lstm_control_btns_layout)
        self.lstm_control_layout.addLayout(self.lstm_control_inputs_layout)
        self.chart_layout.addLayout(self.lstm_layout)
        
        self.dnn_layout.addLayout(self.dnn_panel_layout)
        self.dnn_layout.addLayout(self.dnn_control_layout)
        self.dnn_control_layout.addLayout(self.dnn_control_btns_layout)
        self.dnn_control_layout.addLayout(self.dnn_control_inputs_layout)
        self.chart_layout.addLayout(self.dnn_layout)
        
        self.backtest_control_layout.addLayout(self.backtest_control_btn_layout)
        self.backtest_control_layout.addLayout(self.backtest_control_option_layout)
        self.backtest_control_layout.addLayout(self.backtest_control_input_layout)
        self.backtest_control_layout.addLayout(self.backtest_control_simulate_layout)
        self.backtest_layout.addLayout(self.backtest_panel_layout)
        self.backtest_layout.addLayout(self.backtest_control_layout)
        
        base_layout.addLayout(self.portfolio_layout, stretch=1)
        base_layout.addLayout(self.chart_layout, stretch=4)
        base_layout.addLayout(self.backtest_layout, stretch=3)
        
        return base_layout
    
    def createUI(self):
        self.portfolio_trade_btn = QPushButton("Trade", self)
        
        self.portfolio_stock_add_label = QLabel("Add Stock:")
        self.portfolio_stock_add_input = QLineEdit(self)
        self.portfolio_add_stock_btn = QPushButton("Add", self)
        self.portfolio_add_stock_btn.clicked.connect(self.add_stock_btn_clicked)

        self.portfolio_stock_list_label = QLabel("My Portfolio Stock List:")
        self.portfolio_stock_list = QListWidget()
        self.portfolio_stock_list.addItems(self.portfolio.keys())
        
        self.portfolio_evaluate_title_label = QLabel("Portfolio Evaluate")
        self.portfolio_evaluate_optimize_btn = QPushButton("Optimal Weights", self)
        self.portfolio_evaluate_vol_btn = QPushButton("Volatility", self)
        self.portfolio_evaluate_weights_label = QLabel("Weights")
        self.portfolio_evaluate_vol_label = QLabel("Volatility")
        
        self.dnn_title_label = QLabel("Long-Term Stock Price Prediction", self)
        self.dnn_run_btn = QPushButton("Run", self)
        self.dnn_get_info_btn = QPushButton("Get Information", self)
        self.dnn_stocks_input = QLineEdit(self)
        self.dnn_lags_input = QLineEdit(self)
        self.dnn_target_stock_input = QLineEdit(self)
        self.dnn_plot = canvas.StaticPlot()
        
        self.lstm_title_label = QLabel("Short-Term Stock Price Prediction", self)
        self.lstm_run_btn = QPushButton("Run", self)
        self.lstm_get_info_btn = QPushButton("Get Information", self)
        self.lstm_stocks_input = QLineEdit(self)
        self.lstm_lags_input = QLineEdit(self)
        self.lstm_plot = canvas.StaticPlot()
        
        self.backtest_opened_model_label = QLabel("There's no opened any model", self)
        self.backtest_trade_status_label = QLabel("TRADE STATUS", self)
        self.backtest_stop_btn = QPushButton("Stop", self)
        self.backtest_run_btn = QPushButton("Run", self)
        self.backtest_new_model_btn = QPushButton("New", self)
        self.backtest_open_model_btn = QPushButton("Open", self)
        self.backtest_option_symbol_input = QLineEdit(self)
        self.backtest_option_amount_input = QLineEdit(self)
        self.backtest_option_lags_input = QLineEdit(self)
        self.backtest_sl_input = QLineEdit(self)
        self.backtest_tsl_input = QLineEdit(self)
        self.backtest_tp_input = QLineEdit(self)
        self.bakctest_fee_input = QLineEdit(self)
        self.backtest_guarantee_checkbox = QCheckBox('Guarantee', self)
        self.backtest_plot = canvas.RealTimePlot()
        self.backtest_simulate_checkbox = QCheckBox('Simulate')
        self.backtest_simulate_day_before_label = QLabel('Day Before:')
        self.backtest_simulate_day_before_input = QLineEdit()
        self.backtest_simulate_period_label = QLabel('Period:')
        self.backtest_simulate_period_input = QLineEdit()
        
        self.realtime_stoploss_monitor_btn = QPushButton("Stoploss", self)
        
    def setDetails(self):
        self.backtest_simulate = True
        val_int = QIntValidator()

        self.dnn_stocks_input.setPlaceholderText("Split stock code with comma.")
        self.lstm_stocks_input.setPlaceholderText("Split stock code with comma.")
        self.dnn_target_stock_input.setPlaceholderText("Prediction target stock (only 1)")
        self.dnn_stocks_input.setText("nvda, ^vix, tqqq, xsd, eurusd=x")
        self.lstm_stocks_input.setText("nvda, amd, intc")
        self.dnn_target_stock_input.setText("nvda")
        
        self.dnn_lags_input.setPlaceholderText("Lags(Fomer data)")
        self.lstm_lags_input.setPlaceholderText("Lags(Fomer data)")
        self.dnn_lags_input.setText("3")
        self.lstm_lags_input.setText("10")
        self.dnn_lags_input.setValidator(val_int)
        self.lstm_lags_input.setValidator(val_int)
        
        self.backtest_plot.canvas.set_major_formatter('%H:%M:%S')
        self.backtest_option_symbol_input.setPlaceholderText("Target symbol for Backtesting")
        self.backtest_option_symbol_input.setText("nvda")
        self.backtest_option_amount_input.setText("10000")
        self.backtest_option_lags_input.setValidator(val_int)
        self.backtest_option_lags_input.setPlaceholderText("Lags")
        self.backtest_option_lags_input.setText("3")
        self.backtest_sl_input.setPlaceholderText("Stop-loss % / 100")
        self.backtest_tsl_input.setPlaceholderText("Trail Stop-loss % / 100")
        self.backtest_tp_input.setPlaceholderText("Take-profit % / 100")
        self.bakctest_fee_input.setPlaceholderText("Fee % / 100")
        self.backtest_sl_input.setText("0.015")
        self.backtest_tsl_input.setText("0.0")
        self.backtest_tp_input.setText("0.045")
        self.bakctest_fee_input.setText("0.0025")
        self.backtest_guarantee_checkbox.setChecked(True)
        self.backtest_trade_status_label.setFont(QFont('Arial', 13))
        self.backtest_simulate_checkbox.setChecked(self.backtest_simulate)
        self.backtest_simulate_day_before_input.setValidator(val_int)
        self.backtest_simulate_day_before_input.setText("10")
        self.backtest_simulate_day_before_input.setEnabled(self.backtest_simulate)
        self.backtest_simulate_period_input.setText("5m")
        self.backtest_simulate_period_input.setEnabled(self.backtest_simulate)

    def connectActions(self):
        self.portfolio_stock_list.itemClicked.connect(self.handle_click_stock_list)
        self.portfolio_trade_btn.clicked.connect(self.trade_btn_clicked)
        self.portfolio_evaluate_optimize_btn.clicked.connect(self.get_optimal_weights)
        self.portfolio_evaluate_vol_btn.clicked.connect(self.get_portfolio_vol)
        self.dnn_run_btn.clicked.connect(self.dnn_run_btn_clicked)
        self.dnn_get_info_btn.clicked.connect(self.dnn_get_result_btn_clicked)
        self.lstm_run_btn.clicked.connect(self.lstm_run_btn_clicked)
        self.lstm_get_info_btn.clicked.connect(self.lstm_get_result_btn_clicked)
        self.backtest_stop_btn.clicked.connect(self.backtest_stop_btn_clicked)
        self.backtest_run_btn.clicked.connect(self.backtest_run_btn_clicked)
        self.backtest_new_model_btn.clicked.connect(self.backtest_new_model_btn_clicked)
        self.backtest_open_model_btn.clicked.connect(self.backtest_open_model_btn_clicked)
        self.backtest_simulate_checkbox.stateChanged.connect(self.toggle_simulation)
        self.realtime_stoploss_monitor_btn.clicked.connect(self.realtime_stoploss_monitor_btn_clicked)

    def addWidgets(self):
        self.setWindowTitle('Markov')
        self.resize(1600, 800)
        self.center()
        base_layout = self.initLayouts()
        self.createUI()
        self.setDetails()
        self.connectActions()
        
        self.portfolio_add_layout.addWidget(self.portfolio_stock_add_label)
        self.portfolio_add_layout.addWidget(self.portfolio_stock_add_input)
        self.portfolio_add_layout.addWidget(self.portfolio_add_stock_btn)
        self.portfolio_list_layout.addWidget(self.portfolio_stock_list_label)
        self.portfolio_list_layout.addWidget(self.portfolio_stock_list)
        self.portfolio_list_layout.addWidget(self.portfolio_trade_btn)
        self.portfolio_evaluate_layout.addWidget(self.portfolio_evaluate_title_label)
        self.portfolio_evaluate_layout.addWidget(self.portfolio_evaluate_optimize_btn)
        self.portfolio_evaluate_layout.addWidget(self.portfolio_evaluate_weights_label)
        self.portfolio_evaluate_layout.addWidget(self.portfolio_evaluate_vol_btn)
        self.portfolio_evaluate_layout.addWidget(self.portfolio_evaluate_vol_label)
        
        self.dnn_control_btns_layout.addWidget(self.dnn_run_btn)
        self.dnn_control_btns_layout.addWidget(self.dnn_get_info_btn)
        self.dnn_control_inputs_layout.addWidget(self.dnn_target_stock_input)
        self.dnn_control_inputs_layout.addWidget(self.dnn_stocks_input)
        self.dnn_control_inputs_layout.addWidget(self.dnn_lags_input)
        self.dnn_panel_layout.addWidget(self.dnn_title_label)
        self.dnn_panel_layout.addWidget(self.dnn_plot)

        self.lstm_control_btns_layout.addWidget(self.lstm_run_btn)
        self.lstm_control_btns_layout.addWidget(self.lstm_get_info_btn)
        self.lstm_control_inputs_layout.addWidget(self.lstm_stocks_input)
        self.lstm_control_inputs_layout.addWidget(self.lstm_lags_input)
        self.lstm_panel_layout.addWidget(self.lstm_title_label)
        self.lstm_panel_layout.addWidget(self.lstm_plot)
        
        self.backtest_panel_layout.addWidget(self.backtest_opened_model_label)
        self.backtest_panel_layout.addWidget(self.backtest_plot)
        self.backtest_control_btn_layout.addWidget(self.backtest_run_btn)
        self.backtest_control_btn_layout.addWidget(self.backtest_stop_btn)
        self.backtest_control_btn_layout.addWidget(self.backtest_new_model_btn)
        self.backtest_control_btn_layout.addWidget(self.backtest_open_model_btn)
        self.backtest_control_option_layout.addWidget(self.backtest_option_symbol_input)
        self.backtest_control_option_layout.addWidget(self.backtest_option_amount_input)
        self.backtest_control_option_layout.addWidget(self.backtest_option_lags_input)
        self.backtest_control_input_layout.addWidget(self.backtest_sl_input)
        self.backtest_control_input_layout.addWidget(self.backtest_tsl_input)
        self.backtest_control_input_layout.addWidget(self.backtest_tp_input)
        self.backtest_control_input_layout.addWidget(self.bakctest_fee_input)
        self.backtest_control_input_layout.addWidget(self.backtest_guarantee_checkbox)
        self.backtest_control_layout.addWidget(self.backtest_trade_status_label)
        self.backtest_control_simulate_layout.addWidget(self.backtest_simulate_checkbox)
        self.backtest_control_simulate_layout.addWidget(self.backtest_simulate_day_before_label)
        self.backtest_control_simulate_layout.addWidget(self.backtest_simulate_day_before_input)
        self.backtest_control_simulate_layout.addWidget(self.backtest_simulate_period_label)
        self.backtest_control_simulate_layout.addWidget(self.backtest_simulate_period_input)
        self.backtest_control_simulate_layout.addWidget(self.realtime_stoploss_monitor_btn)
        
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def load_portfolio(self):
        try:
            with open(self.portfolio_file, 'r') as file:
                self.portfolio = json.load(file)
        except FileNotFoundError:
            self.portfolio = {}
    def save_portfolio(self):
        with open(self.portfolio_file, 'w') as file:
            json.dump(self.portfolio, file)
        
        self.load_portfolio()
    
    def _str_symbols(self, symbols):
        return ", ".join(symbols)
    def _get_symbols(self, text):
        return list(map(lambda x: x.strip(), text.split(',')))
    def _show_finished_training_message(self):
        QMessageBox.information(self, "Training finished", "Check the result to click 'Get information' Button")
    
    def add_stock_btn_clicked(self):
        stock_name = self.portfolio_stock_add_input.text().strip().upper()
        
        info = data.create_info(stock_name)
        if info['quoteType'] == 'NONE':
            QMessageBox.warning(self, "Error", "Stock is not available.")
            return
        
        if stock_name:
            if stock_name not in self.portfolio:
                self.portfolio[stock_name] = {}
                self.portfolio[stock_name]['timezone'] = info['timeZoneFullName']
                self.portfolio_stock_list.addItem(stock_name)
                self.save_portfolio()
            else:
                QMessageBox.warning(self, "Warning", "Stock already exists!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter a stock name!")

    def handle_click_stock_list(self, item):
        selected_stock = item.text()
        self.selected_stock = selected_stock
        
        stock_info = self.portfolio[self.selected_stock]
        if "dnn" in stock_info:
            dnn_info = stock_info["dnn"]
            self.dnn_lags_input.setText(str(dnn_info["lags"]))
            self.dnn_stocks_input.setText(self._str_symbols(dnn_info["symbols"]))
            self.dnn_target_stock_input.setText(selected_stock)
        if "lstm" in self.portfolio[self.selected_stock]:
            lstm_info = stock_info["lstm"]
            self.lstm_lags_input.setText(str(lstm_info["lags"]))
            self.lstm_stocks_input.setText(self._str_symbols(lstm_info["symbols"]))
        if "backtest" in self.portfolio[self.selected_stock]:
            bt_info = stock_info["backtest"]
            self.backtest_option_lags_input.setText(str(bt_info["lags"]))
            self.backtest_option_amount_input.setText(str(bt_info["amount"]))
            self.backtest_option_symbol_input.setText(selected_stock)
            self.backtest_guarantee_checkbox.setChecked(bt_info["guarantee"])
            self.backtest_sl_input.setText(str(bt_info["sl"]))
            self.backtest_tsl_input.setText(str(bt_info["tsl"]))
            self.backtest_tp_input.setText(str(bt_info["tp"]))
            self.bakctest_fee_input.setText(str(bt_info["fee"]))
    
    def trade_btn_clicked(self):
        if(self.selected_stock == ""):
            QMessageBox.information(self, "Error", "Please select stock to trade.")
            return
        
        window = TradeWindow()
        window.initUI(self.user_info, self.selected_stock, self.portfolio[self.selected_stock]['timezone'])
        self.windows.append(window)
        window.showMaximized()
        
    def get_optimal_weights(self):
        today, tomorrow = portfolio.get_today_tomorrow_prices(self.portfolio)
        if len(today) <= 0 or len(tomorrow) <= 0:
            return
        w = portfolio.optimal_portfolio_weights(today, tomorrow, risk_free_rate=0.3)
        self.portfolio_evaluate_weights_label.setText("\n".join([f"{info[0]}: {(round(info[1]*100, 2))}%" for info in zip(portfolio.get_names(self.portfolio), w)]))
    def get_portfolio_vol(self):
        today, tomorrow = portfolio.get_today_tomorrow_prices(self.portfolio)
        if len(today) <= 0 or len(tomorrow) <= 0:
            return
        vol = portfolio.portfolio_volatility(portfolio.optimal_portfolio_weights(today, tomorrow, risk_free_rate=0.3), today, tomorrow)
        self.portfolio_evaluate_vol_label.setText(str(round(vol, 2)))
    def dnn_run_btn_clicked(self):
        if self.selected_stock == "":
            QMessageBox(self, "Error", "Select a stock to analyze.")
        
        lags = int(self.dnn_lags_input.text())
        symbols = self._get_symbols(self.dnn_stocks_input.text())
        target = self.dnn_target_stock_input.text().strip()
        if self.handle_train_init_error(lags, symbols, target) == -1:
            return
        if not target in symbols:
            self.show_error(f"Target({target}) must be in symbol list.")
            return
        tz = self.portfolio[self.selected_stock]["timezone"]
        df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3), tz=tz), end=data.today(tz=tz), interval='1d')
        if self.handle_flaw_dataset(df) == -1:
            return
        
        self.dnn_plot.clear_plot()
        X_train, X_test, y_train, y_test = data.dnn_prepare_dataset(df, lags, target+'_Price')
        dnn = models.DNN(X_train, X_test, y_train, y_test, verbose=2)
        dnn.compile()
        history = dnn.fit(100, './models/dnn.keras', skip_if_exist=False)
        df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3), tz=tz), end=data.today(tz=tz), interval='1d')
        df = data.dnn_prepare_for_prediction_dataset(df, lags)
        self.dnn_train_result = models.TrainResult(history.history, dnn.predict(df))
        self.dnn_plot.plot_static_data(df.index, self.dnn_train_result.predictions, "Date", target)
        
        self.portfolio[self.selected_stock]["dnn"] = {}
        self.portfolio[self.selected_stock]["dnn"]["lags"] = lags
        self.portfolio[self.selected_stock]["dnn"]['symbols'] = symbols
        self.portfolio[self.selected_stock]["dnn"]['result'] = {
            "date" : df.index[-1].strftime("%Y-%m-%d"),
            "prediction" : float(self.dnn_train_result.predictions[-1][0])
        }
        self.save_portfolio()
        
        self._show_finished_training_message()
        
    def dnn_get_result_btn_clicked(self):
        if self.dnn_train_result == None:
            return
        
        sub = TrainResultWindow()
        sub.initUI("DNN Training", self.dnn_train_result)
        self.windows.append(sub)
        sub.show()
        
    def lstm_run_btn_clicked(self):
        if self.selected_stock == "":
            QMessageBox(self, "Error", "Select a stock to analyze.")
        tz = self.portfolio[self.selected_stock]["timezone"]
        
        lags = int(self.lstm_lags_input.text())
        symbols = self._get_symbols(self.lstm_stocks_input.text())
        if self.handle_train_init_error(lags, symbols) == -1:
            return
        train = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3), tz), end=data.today(tz), interval='1d')
        if self.handle_flaw_dataset(train) == -1:
            return

        self.lstm_plot.clear_plot()
        mo1_5m = data.create_dataset(symbols, start=data.today_before(data.days_to_months(1), tz), end=data.today(tz), interval='1d')
        train_values = data.lstm_prepare_dataset(train).values
        test = data.lstm_prepare_dataset(mo1_5m)
        test_values = test.values
        lstm = models.LSTM_Sequential(lags, len(symbols), 10, 100, verbose=2)
        lstm.compile()
        history = lstm.fit(train_values, 100, 10, './models/lstm.keras', skip_if_exist=False)
        self.lstm_train_result = models.TrainResult(history.history, lstm.predict(test_values))
        self.lstm_plot.plot_static_data(test.index[lags:], self.lstm_train_result.predictions)
        
        self.portfolio[self.selected_stock]["lstm"] = {}
        self.portfolio[self.selected_stock]["lstm"]["lags"] = lags
        self.portfolio[self.selected_stock]["lstm"]['symbols'] = symbols
        self.portfolio[self.selected_stock]["lstm"]['result'] = {
            "date" : test.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
            "prediction" : float(self.lstm_train_result.predictions[-1][0])
        }
        self.save_portfolio()
        self._show_finished_training_message()
    
    def lstm_get_result_btn_clicked(self):
        if self.lstm_train_result == None:
            return
        
        sub = TrainResultWindow()
        sub.initUI("LSTM Training", self.lstm_train_result)
        self.windows.append(sub)
        sub.show()
        
    def backtest_stop_btn_clicked(self):
        if not self.backtesting:
            return
        self.btt.stop_trade()
        self.backtesting = False
        QMessageBox.information(self, "Stop Trade", "Stopped Trading with realtime data.")
    
    def backtest_run_btn_clicked(self):
        if self.selected_stock == "":
            QMessageBox.information(self, "Error", "Select a stock to analyze.")
            return
        if self.backtest_trade_model_path == "":
            QMessageBox.information(self, "Error", "Open your model.")
            return
        if self.backtesting or self.handle_model_path_error(self.backtest_trade_model_path) == -1 or self.handle_model_path_error(self.backtest_sideway_model_path) == -1:
            return
        tz = self.portfolio[self.selected_stock]["timezone"]
        
        symbol = self.backtest_option_symbol_input.text().strip()
        amount = float(self.backtest_option_amount_input.text())
        guarantee = self.backtest_guarantee_checkbox.isChecked()
        lags = int(self.backtest_option_lags_input.text())
        if lags < 1:
            lags = 1
        sl = float(self.backtest_sl_input.text())
        tsl = float(self.backtest_tsl_input.text())
        tp = float(self.backtest_tp_input.text())
        fee = float(self.bakctest_fee_input.text())
        
        self.portfolio[self.selected_stock]["backtest"] = {}
        self.portfolio[self.selected_stock]["backtest"]["amount"] = amount
        self.portfolio[self.selected_stock]["backtest"]['guarantee'] = guarantee
        self.portfolio[self.selected_stock]["backtest"]['lags'] = lags
        self.portfolio[self.selected_stock]["backtest"]['sl'] = sl
        self.portfolio[self.selected_stock]["backtest"]['tsl'] = tsl
        self.portfolio[self.selected_stock]["backtest"]['tp'] = tp
        self.portfolio[self.selected_stock]["backtest"]['fee'] = fee
        self.save_portfolio()
        
        sl = None if sl == 0.0 else sl
        tsl = None if tsl == 0.0 else tsl
        tp = None if tp == 0.0 else tp
        target = symbol + '_Price'
        df = pd.DataFrame({target:[], 'Datetime':[]})
        df.set_index('Datetime')
        if self.backtest_simulate:
            daybefore = int(self.backtest_simulate_day_before_input.text())
            period = self.backtest_simulate_period_input.text()
            df = data.create_dataset([symbol], start=data.today_before(daybefore, tz), end=data.today(tz), interval=period)
            if self.handle_flaw_dataset(df) == -1:
                return
        self.backtest_plot.clear()
        self.backtest_stock_price_plot = self.backtest_plot.canvas.create_new_y_axis('--', 'green')
        self.backtest_plot.canvas.set_major_formatter('%H:%M:%S')
        self.backtest_plot.canvas.destroy_prev = False
        self.backtest_trade_status_label.setText("TRADE STATUS")
        agents = [self.trade_sideway_model, self.trade_model]
        env = environment.StockMarketEnvironment(agents, df, target, lags=lags)
        self.btt = QTBacktest.BacktestThread(symbol, env, 1, tz)
        self.btt.signal.connect(self.handle_backtest_result)
        self.btt.set_backtest_strategy(amount, sl=sl, tsl=tsl, tp=tp, fee=fee, continue_to_realtime=(not self.backtest_simulate), guarantee=guarantee)
        self.backtesting = True
        self.btt.start()
    
    def backtest_new_model_btn_clicked(self):
        sub = TrainRLModelWindow()
        sub.initUI(self.selected_stock)
        sub.exec_()
        
    def backtest_open_model_btn_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(None, "Folder For New Model", "", QFileDialog.ShowDirsOnly)
        if folder_path:
            self.backtest_trade_model_path = os.path.join(folder_path, f"trade.keras")
            self.backtest_sideway_model_path = os.path.join(folder_path, f"sideway.keras")
        else:
            return
        self.backtest_opened_model_label.setText(f"{self.backtest_trade_model_path}")
        self.trade_model = keras.models.load_model(self.backtest_trade_model_path)
        self.trade_sideway_model = keras.models.load_model(self.backtest_sideway_model_path)
        
    def toggle_simulation(self, state):
        if state == 2:
            self.backtest_simulate = True
            self.backtest_simulate_day_before_input.setEnabled(True)
            self.backtest_simulate_period_input.setEnabled(True)
        else:
            self.backtest_simulate = False
            self.backtest_simulate_day_before_input.setEnabled(False)
            self.backtest_simulate_period_input.setEnabled(False)
    
    def realtime_stoploss_monitor_btn_clicked(self):
        window = MonitorStoplossWindow()
        window.initUI(self.selected_stock)
        self.windows.append(window)
        window.show()
        
if __name__ == '__main__':
   app = QApplication(sys.argv)
   app.setStyleSheet(open('./resources/style.qss', 'r').read())
   ex = MyApp({
            "apikey": keys.KEY,
            "apisecret": keys.APISECRET,
            "htsid": keys.HTS_ID,
            "accno" : keys.ACCOUNT_NO,
            "accpwd" : keys.ACCOUNT_PWD,
            "mock": True
        })
   ex.showMaximized()
   sys.exit(app.exec_())