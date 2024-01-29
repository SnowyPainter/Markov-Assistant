import sys, datetime
import data, models,QTBacktest, resources.canvas as canvas
import handlers.window_handler as window_handler
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MyApp(QMainWindow, window_handler.Handler):
    def __init__(self):
        super().__init__()
        self.initUI()
        
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
        self.backtest_control_btn_layout = QHBoxLayout()
        self.backtest_control_input_layout = QHBoxLayout()
        self.backtest_control_layout = QVBoxLayout()
        
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
        self.backtest_control_layout.addLayout(self.backtest_control_input_layout)
        self.backtest_layout.addLayout(self.backtest_panel_layout)
        self.backtest_layout.addLayout(self.backtest_control_layout)
        
        base_layout.addLayout(self.chart_layout)
        base_layout.addLayout(self.backtest_layout)
        
        return base_layout
    
    def createUI(self):
        self.dnn_run_btn = QPushButton("Run", self)
        self.dnn_get_info_btn = QPushButton("Get Information", self)
        self.dnn_stocks_input = QLineEdit(self)
        self.dnn_plot = canvas.StaticPlot()
        
        self.lstm_run_btn = QPushButton("Run", self)
        self.lstm_get_info_btn = QPushButton("Get Information", self)
        self.lstm_stocks_input = QLineEdit(self)
        self.lstm_plot = canvas.StaticPlot()
        
        self.backtest_trade_status_label = QLabel("TRADE STATUS", self)
        self.backtest_stop_btn = QPushButton("Stop", self)
        self.backtest_run_btn = QPushButton("Run", self)
        self.backtest_sl_input = QLineEdit(self)
        self.backtest_tsl_input = QLineEdit(self)
        self.backtest_tp_input = QLineEdit(self)
        self.backtest_guarantee_checkbox = QCheckBox('Guarantee', self)
        self.backtest_plot = canvas.RealTimePlot()
    
    def setDetails(self):
        self.dnn_stocks_input.setPlaceholderText("Split stock code with comma.")
        self.lstm_stocks_input.setPlaceholderText("Split stock code with comma.")
        val_int = QIntValidator()
        self.backtest_sl_input.setValidator(val_int)
        self.backtest_tsl_input.setValidator(val_int)
        self.backtest_tp_input.setValidator(val_int)
        self.backtest_sl_input.setPlaceholderText("Stop-loss %")
        self.backtest_tsl_input.setPlaceholderText("Trail Stop-loss %")
        self.backtest_tp_input.setPlaceholderText("Take-profit %")
        self.backtest_guarantee_checkbox.setChecked(True)
        self.backtest_trade_status_label.setFont(QFont('Arial', 13))
    
    def connectActions(self):
        self.dnn_run_btn.clicked.connect(self.dnn_run_btn_clicked)
        self.dnn_get_info_btn.clicked.connect(self.dnn_get_result_btn_clicked)
        self.lstm_run_btn.clicked.connect(self.lstm_run_btn_clicked)
        self.lstm_get_info_btn.clicked.connect(self.lstm_get_result_btn_clicked)
        self.backtest_stop_btn.clicked.connect(self.backtest_stop_btn_clicked)
        self.backtest_run_btn.clicked.connect(self.backtest_run_btn_clicked)
        
    def initUI(self):
        self.setWindowTitle('TESTING')
        self.resize(1600, 800)
        self.center()
        base_layout = self.initLayouts()
        self.createUI()
        self.setDetails()
        self.connectActions()
        
        self.dnn_control_btns_layout.addWidget(self.dnn_run_btn)
        self.dnn_control_btns_layout.addWidget(self.dnn_get_info_btn)
        self.dnn_control_inputs_layout.addWidget(self.dnn_stocks_input)
        self.dnn_panel_layout.addWidget(self.dnn_plot)

        self.lstm_control_btns_layout.addWidget(self.lstm_run_btn)
        self.lstm_control_btns_layout.addWidget(self.lstm_get_info_btn)
        self.lstm_control_inputs_layout.addWidget(self.lstm_stocks_input)
        self.lstm_panel_layout.addWidget(self.lstm_plot)
        
        self.backtest_panel_layout.addWidget(self.backtest_plot)
        self.backtest_control_btn_layout.addWidget(self.backtest_run_btn)
        self.backtest_control_btn_layout.addWidget(self.backtest_stop_btn)
        self.backtest_control_input_layout.addWidget(self.backtest_sl_input)
        self.backtest_control_input_layout.addWidget(self.backtest_tsl_input)
        self.backtest_control_input_layout.addWidget(self.backtest_tp_input)
        self.backtest_control_input_layout.addWidget(self.backtest_guarantee_checkbox)
        self.backtest_control_layout.addWidget(self.backtest_trade_status_label)
        
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def dnn_run_btn_clicked(self):
        print("d")
    def dnn_get_result_btn_clicked(self):
        print('r')
    def lstm_run_btn_clicked(self):
        print("l")
    def lstm_get_result_btn_clicked(self):
        print('r')
    
        
    def backtest_stop_btn_clicked(self):
        self.btt.stop_trade()
        print("*** stop trade ***")
    
    def backtest_run_btn_clicked(self):
        self.backtest_plot.clear()
        self.backtest_trade_status_label.setText("TRADE STATUS")
        
        symbol = 'nvda_Price'
        symbols = ["nvda", "amd", "intc"]
        features = [symbol, 'r', 's', 'm', 'v']
        amount = 10000
        df = data.create_dataset(symbols, start=data.today_before(10), end=data.today(), interval='5m')
        model = models.load('./models/agent.keras')
        self.btt = QTBacktest.BacktestThread(symbol, features, df, symbols, 0.1)
        self.btt.signal.connect(self.handle_backtest_result)
        self.btt.set_backtest_strategy(model, amount)
        self.btt.start()
    
if __name__ == '__main__':
   app = QApplication(sys.argv)
   #app.setStyleSheet(open('./resources/style.qss', 'r').read())
   ex = MyApp()
   ex.show()
   sys.exit(app.exec_())