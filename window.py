import sys, datetime
import data, models,QTBacktest, canvas
import window_handler
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
        self.backtest_layout = QVBoxLayout()
        self.backtest_panel_layout = QVBoxLayout()
        self.backtest_control_btn_layout = QHBoxLayout()
        self.backtest_control_layout = QVBoxLayout()

        base_layout.addLayout(self.chart_layout)
        base_layout.addLayout(self.backtest_layout)
        self.backtest_control_layout.addLayout(self.backtest_control_btn_layout)
        self.backtest_layout.addLayout(self.backtest_panel_layout)
        self.backtest_layout.addLayout(self.backtest_control_layout)
        return base_layout
    
    def initUI(self):
        self.setWindowTitle('TESTING')
        self.resize(1600, 800)
        self.center()
        base_layout = self.initLayouts()
        
        self.trade_status_label = QLabel("TRADE STATUS", self)
        self.backtest_stop_btn = QPushButton("Stop", self)
        self.backtest_run_btn = QPushButton("Run", self)
        self.l1 = QLabel("Chart Layout", self)
        self.backtest_plot = canvas.RealTimePlot()
        
        self.trade_status_label.setFont(QFont('Arial', 13))
        self.backtest_run_btn.setStyleSheet("background-color : green; color:white")
        self.backtest_stop_btn.setStyleSheet("background-color : red; color:white")
        self.backtest_stop_btn.clicked.connect(self.stop_btn_clicked)
        self.backtest_run_btn.clicked.connect(self.run_btn_clicked)
        
        self.chart_layout.addWidget(self.l1)
        self.backtest_panel_layout.addWidget(self.backtest_plot)
        self.backtest_control_btn_layout.addWidget(self.backtest_run_btn)
        self.backtest_control_btn_layout.addWidget(self.backtest_stop_btn)
        self.backtest_control_layout.addWidget(self.trade_status_label)
        
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def stop_btn_clicked(self):
        self.btt.stop_trade()
        print("*** stop trade ***")
    
    def run_btn_clicked(self):
        self.backtest_plot.clear()
        self.trade_status_label.setText("TRADE STATUS")
        
        symbol = 'nvda_Price'
        symbols = ["nvda", "amd", "intc"]
        features = [symbol, 'r', 's', 'm', 'v']
        amount = 10000
        df = data.create_dataset(symbols, start=data.today_before(20), end=data.today(), interval='5m')
        model = models.load('./models/agent.keras')
        self.btt = QTBacktest.BacktestThread(symbol, features, df, symbols, 0.1)
        self.btt.signal.connect(self.handle_backtest_result)
        self.btt.set_backtest_strategy(model, amount)
        self.btt.start()
    
if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   ex.show()
   sys.exit(app.exec_())