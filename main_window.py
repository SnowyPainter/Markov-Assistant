import sys, datetime
import data, models, QTBacktest, resources.canvas as canvas
import handlers.window_handler as window_handler
import pandas as pd
import os, json
from train_result_window import *
from train_rlmodel_window import *
from monitor_stock_window import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MyApp(QMainWindow, window_handler.Handler):
    def __init__(self):
        super().__init__()
        self.windows = []
        self.addWidgets()
        self.dnn_train_result = None
        self.lstm_train_result = None
        self.backtest_model_path = None
        self.loadOptions()
        self.loadRecentNetWealth()
    
    def loadRecentNetWealth(self):
        try:
            with open('./log/backtest.json', 'r') as file:
                data = json.load(file)
                net_wealth = data[-1]["net_wealth"]
                self.backtest_option_amount_input.setText(str(net_wealth))
        except:
            self.backtest_option_amount_input.setText("10000")
        
    def loadOptions(self):
        if not os.path.exists('options.json'):
            default_values = {
                "trailing stop loss": "",
                "stop loss": "015",
                "take profit": "045",
                "fee": "0025"
            }
            with open('options.json', 'w') as file:
                json.dump(default_values, file, indent=2)
        with open('options.json', 'r') as file:
            data = json.load(file)
            self.backtest_tsl_input.setText(data.get("trailing stop loss", ""))
            self.backtest_sl_input.setText(data.get("stop loss", ""))
            self.backtest_tp_input.setText(data.get("take profit", ""))
            self.bakctest_fee_input.setText(data.get("fee", ""))
    
    def initLayouts(self):
        base_layout = QHBoxLayout()
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
        
        base_layout.addLayout(self.chart_layout)
        base_layout.addLayout(self.backtest_layout)
        
        return base_layout
    
    def createUI(self):
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
        self.backtest_realtime_monitor_btn = QPushButton("Monitor", self)
        
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
        self.backtest_sl_input.setValidator(val_int)
        self.backtest_tsl_input.setValidator(val_int)
        self.backtest_tp_input.setValidator(val_int)
        self.bakctest_fee_input.setValidator(val_int)
        self.backtest_sl_input.setPlaceholderText("Stop-loss %")
        self.backtest_tsl_input.setPlaceholderText("Trail Stop-loss %")
        self.backtest_tp_input.setPlaceholderText("Take-profit %")
        self.bakctest_fee_input.setPlaceholderText("Fee %")
        self.backtest_sl_input.setText("015")
        self.backtest_tsl_input.setText("")
        self.backtest_tp_input.setText("045")
        self.bakctest_fee_input.setText("0025")
        self.backtest_guarantee_checkbox.setChecked(True)
        self.backtest_trade_status_label.setFont(QFont('Arial', 13))
        self.backtest_simulate_checkbox.setChecked(self.backtest_simulate)
        self.backtest_simulate_day_before_input.setValidator(val_int)
        self.backtest_simulate_day_before_input.setText("10")
        self.backtest_simulate_day_before_input.setEnabled(self.backtest_simulate)
        self.backtest_simulate_period_input.setText("5m")
        self.backtest_simulate_period_input.setEnabled(self.backtest_simulate)

    def connectActions(self):
        self.dnn_run_btn.clicked.connect(self.dnn_run_btn_clicked)
        self.dnn_get_info_btn.clicked.connect(self.dnn_get_result_btn_clicked)
        self.lstm_run_btn.clicked.connect(self.lstm_run_btn_clicked)
        self.lstm_get_info_btn.clicked.connect(self.lstm_get_result_btn_clicked)
        self.backtest_stop_btn.clicked.connect(self.backtest_stop_btn_clicked)
        self.backtest_run_btn.clicked.connect(self.backtest_run_btn_clicked)
        self.backtest_new_model_btn.clicked.connect(self.backtest_new_model_btn_clicked)
        self.backtest_open_model_btn.clicked.connect(self.backtest_open_model_btn_clicked)
        self.backtest_simulate_checkbox.stateChanged.connect(self.toggle_simulation)
        self.backtest_realtime_monitor_btn.clicked.connect(self.backtest_realtime_monitor_btn_clicked)
        
    def addWidgets(self):
        self.setWindowTitle('Markov')
        self.resize(1600, 800)
        self.center()
        base_layout = self.initLayouts()
        self.createUI()
        self.setDetails()
        self.connectActions()
        
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
        self.backtest_control_simulate_layout.addWidget(self.backtest_realtime_monitor_btn)
        
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def _get_symbols(self, text):
        return list(map(lambda x: x.strip(), text.split(',')))
    def _show_finished_training_message(self):
        QMessageBox.information(self, "Training finished", "Check the result to click 'Get information' Button")
    
    def dnn_run_btn_clicked(self):
        lags = int(self.dnn_lags_input.text())
        symbols = self._get_symbols(self.dnn_stocks_input.text())
        target = self.dnn_target_stock_input.text().strip()
        if self.handle_train_init_error(lags, symbols, target) == -1:
            return
        if not target in symbols:
            self.show_error(f"Target({target}) must be in symbol list.")
            return
        df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
        if self.handle_flaw_dataset(df) == -1:
            return
        
        self.dnn_plot.clear_plot()
        X_train, X_test, y_train, y_test = data.dnn_prepare_dataset(df, lags, target+'_Price')
        dnn = models.DNN(X_train, X_test, y_train, y_test, verbose=2)
        dnn.compile()
        history = dnn.fit(100, './models/dnn.keras', skip_if_exist=False)
        df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
        df = data.dnn_prepare_for_prediction_dataset(df, lags)
        self.dnn_train_result = models.TrainResult(history.history, dnn.predict(df))
        self.dnn_plot.plot_static_data(df.index, self.dnn_train_result.predictions, "Date", target)
        self._show_finished_training_message()
        
    def dnn_get_result_btn_clicked(self):
        if self.dnn_train_result == None:
            return
        
        sub = TrainResultWindow()
        sub.initUI("DNN Training", self.dnn_train_result)
        self.windows.append(sub)
        sub.show()
        
    def lstm_run_btn_clicked(self):
        lags = int(self.lstm_lags_input.text())
        symbols = self._get_symbols(self.lstm_stocks_input.text())
        if self.handle_train_init_error(lags, symbols) == -1:
            return
        train = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
        if self.handle_flaw_dataset(train) == -1:
            return
        
        self.lstm_plot.clear_plot()
        mo1_5m = data.create_dataset(symbols, start=data.today_before(data.days_to_months(1)), end=data.today(), interval='1d')
        train_values = data.lstm_prepare_dataset(train).values
        test = data.lstm_prepare_dataset(mo1_5m)
        test_values = test.values
        lstm = models.LSTM_Sequential(lags, len(symbols), 10, 100, verbose=2)
        lstm.compile()
        history = lstm.fit(train_values, 100, 10, './models/lstm.keras', skip_if_exist=False)
        self.lstm_train_result = models.TrainResult(history.history, lstm.predict(test_values))
        self.lstm_plot.plot_static_data(test.index[lags:], self.lstm_train_result.predictions)
        self._show_finished_training_message()
    
    def lstm_get_result_btn_clicked(self):
        if self.lstm_train_result == None:
            return
        
        sub = TrainResultWindow()
        sub.initUI("LSTM Training", self.lstm_train_result)
        self.windows.append(sub)
        sub.show()
        
    def backtest_stop_btn_clicked(self):
        self.btt.stop_trade()
        QMessageBox.information(self, "Stop Trade", "Stopped Trading with realtime data.")
    
    def backtest_run_btn_clicked(self):
        if self.handle_model_path_error(self.backtest_model_path) == -1:
            return
        
        symbol = self.backtest_option_symbol_input.text().strip()
        amount = int(self.backtest_option_amount_input.text())
        lags = int(self.backtest_option_lags_input.text())
        if lags < 1:
            lags = 1
        sl = float("0."+self.backtest_sl_input.text())
        sl = None if sl == 0.0 else sl
        tsl = float("0."+self.backtest_tsl_input.text())
        tsl = None if tsl == 0.0 else tsl
        tp = float("0."+self.backtest_tp_input.text())
        tp = None if tp == 0.0 else tp
        fee = float("0."+self.bakctest_fee_input.text())

        target = symbol + '_Price'
        symbols = [symbol]
        features = [target, 'r', 's', 'm', 'v']
        df = pd.DataFrame({target:[], 'Datetime':[]})
        df.set_index('Datetime')
        if self.backtest_simulate:
            daybefore = int(self.backtest_simulate_day_before_input.text())
            period = self.backtest_simulate_period_input.text()
            df = data.create_dataset(symbols, start=data.today_before(daybefore), end=data.today(), interval=period)
            if self.handle_flaw_dataset(df) == -1:
                return
        self.backtest_plot.clear()
        self.backtest_plot.canvas.set_major_formatter('%H:%M:%S')
        self.backtest_trade_status_label.setText("TRADE STATUS")
        
        model = models.load(self.backtest_model_path)
        self.btt = QTBacktest.BacktestThread(target, features, df, symbols, 1, lags=lags)
        self.btt.signal.connect(self.handle_backtest_result)
        self.btt.set_backtest_strategy(model, amount, sl=sl, tsl=tsl, tp=tp, fee=fee, continue_to_realtime=(not self.backtest_simulate))
        self.btt.start()
    
    def backtest_new_model_btn_clicked(self):
        sub = TrainRLModelWindow()
        sub.exec_()
        
    def backtest_open_model_btn_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open .keras model', './', "Keras (*.keras)")[0]
        if fname == '':
            return
        self.backtest_opened_model_label.setText(fname)
        self.backtest_model_path = fname
        
    def toggle_simulation(self, state):
        if state == 2:
            self.backtest_simulate = True
            self.backtest_simulate_day_before_input.setEnabled(True)
            self.backtest_simulate_period_input.setEnabled(True)
        else:
            self.backtest_simulate = False
            self.backtest_simulate_day_before_input.setEnabled(False)
            self.backtest_simulate_period_input.setEnabled(False)
    
    def backtest_realtime_monitor_btn_clicked(self):
        window = MonitorStockWindow()
        self.windows.append(window)
        window.show()
    
if __name__ == '__main__':
   app = QApplication(sys.argv)
   app.setStyleSheet(open('./resources/style.qss', 'r').read())
   ex = MyApp()
   ex.show()
   sys.exit(app.exec_())