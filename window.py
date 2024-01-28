import sys
import data
import models
import QTBacktest
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
    
        # 타이틀바 내용 설정
        self.setWindowTitle('TESTING')
        self.center()
        self.resize(800, 600)

        stop_btn = QPushButton("Stop", self)
        run_btn = QPushButton("Run", self)
        stop_btn.move(600, 500)
        run_btn.move(400, 500)
        stop_btn.clicked.connect(self.stop_btn_clicked)
        run_btn.clicked.connect(self.run_btn_clicked)
        
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def update_status(self, info):
        print(info)
        
    def stop_btn_clicked(self):
        self.btt.stop_trade()
        print("***STOP TRADE****")
    def run_btn_clicked(self):
        symbol = 'nvda_Price'
        symbols = ["nvda", "amd", "intc"]
        features = [symbol, 'r', 's', 'm', 'v']
        df = data.create_dataset(symbols, start=data.today_before(20), end=data.today(), interval='5m')
        model = models.load('./models/agent.keras')
        self.btt = QTBacktest.BacktestThread(symbol, features, df, 1)
        self.btt.signal.connect(self.update_status)
        self.btt.set_backtest_strategy(model, 10000)
        self.btt.start()
    
if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   ex.show()
   sys.exit(app.exec_())