import data
import models
import backtester
import tradeinfo
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class BacktestThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, symbol, features, df, wait_seconds):
        super(QThread, self).__init__()
        self.wait_seconds = wait_seconds
        self.env =  models.FinanceEnv(df, symbol, features=features,
                                window=10,
                                lags=3, data_preparing_func=data.prepare_RSMV_data,
                                leverage=1,
                                min_performance=0.0, min_accuracy=0.0,
                                start=0, end=None)

    def stop_trade(self):
        self.bt.waiting = False
        
    def set_backtest_strategy(self, model, amount, fee=0.0025, sl=0.015, tsl=None, tp=0.045, guarantee=True):
        self.bt = backtester.RiskManager(self.env, model, amount, fee, 0, waiting=True)
        self.sl = sl
        self.tsl = tsl
        self.tp = tp
        self.guarantee = guarantee
    
    def run(self):
        for infos in self.bt.backtest_strategy(sl=self.sl, tsl=self.tsl, tp=self.tp, wait=5, guarantee=self.guarantee):
            if infos == "waiting" and self.bt.waiting:
                print("STOP BUTTON PLEASE")
                self.msleep(self.wait_seconds*1000)
                continue
            else:
                for info in infos:
                    self.signal.emit(info)