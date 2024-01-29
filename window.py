import sys, datetime
import data, tradeinfo, models,QTBacktest, canvas
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon

class MyApp(QMainWindow):
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
        
        self.status_label = QLabel("TRADE STATUS", self)
        
        self.l1 = QLabel("Chart Layout", self)
        self.backtest_plot = canvas.RealTimePlot()

        self.stop_btn = QPushButton("Stop", self)
        self.run_btn = QPushButton("Run", self)
        self.stop_btn.clicked.connect(self.stop_btn_clicked)
        self.run_btn.clicked.connect(self.run_btn_clicked)
        
        self.chart_layout.addWidget(self.l1)
        self.backtest_panel_layout.addWidget(self.backtest_plot)
        
        self.backtest_control_btn_layout.addWidget(self.run_btn)
        self.backtest_control_btn_layout.addWidget(self.stop_btn)
        self.backtest_control_layout.addWidget(self.status_label)
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def handle_backtest_result(self, info):
        net_wealth = self.btt.bt.net_wealths[-1][1]
        date = self.btt.bt.net_wealths[-1][0]
        infotype = info.info_type
        position = info.trade_position
        
        if infotype == tradeinfo.InfoType.TAKEPROFIT or infotype == tradeinfo.InfoType.STOPLOSS or infotype == tradeinfo.InfoType.TRAILSTOPLOSS:
            units = info.units
            price = info.price
            action = info.trade_type
            ttype = "buy" if action == tradeinfo.TradeType.BUY else "sell"
            p = 0
            if infotype == tradeinfo.InfoType.TAKEPROFIT:
                p = info.takeprofit
            elif infotype == tradeinfo.InfoType.STOPLOSS:
                p = info.stoploss
            elif infotype == tradeinfo.InfoType.TRAILSTOPLOSS:
                p = info.stoploss
            position = "LONG" if position == tradeinfo.TradePosition.LONG else "SHORT"
            self.status_label.setText(f"{position} : {ttype} {units} for {price}, {p}")
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            self.backtest_plot.update_plot(date, net_wealth)
        elif(infotype == tradeinfo.InfoType.CLOSINGOUT):
            self.previous_net_wealth = net_wealth
            QMessageBox.information(self, 'CLOSED OUT', f'performance : {info.performance}, net : {net_wealth}')
        
    def stop_btn_clicked(self):
        self.btt.stop_trade()
        print("***WAIT FALSE TRADE****")
        
    def run_btn_clicked(self):
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
   ex = MyApp()
   ex.show()
   sys.exit(app.exec_())