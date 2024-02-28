import data
import models
import riskmanager
import tradeinfo
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class BacktestThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, stock_symbol, env, wait_seconds, timezone):
        super(QThread, self).__init__()
        self.stock_symbol = stock_symbol
        self.wait_seconds = wait_seconds
        self.env = env
        self.stopped = False
        self.timezone = timezone

    def stop_trade(self):
        self.bt.waiting = False
        self.stopped = True
        
    def set_backtest_strategy(self, amount, fee=0.0025, sl=0.015, tsl=None, tp=0.045, guarantee=True, continue_to_realtime=False):
        self.bt = riskmanager.RiskManager(self.env, amount, fee, 0, self.timezone, waiting=continue_to_realtime)
        self.sl = sl
        self.tsl = tsl
        self.tp = tp
        self.guarantee = guarantee
    
    def run(self):
        for infos in self.bt.backtest_with_strategy(sl=self.sl, tsl=self.tsl, tp=self.tp, wait=5, guarantee=self.guarantee):
            if self.stopped:
                break
            elif len(infos) == 1 and infos[0].info_type == tradeinfo.InfoType.WAITFORNEWDATA and self.bt.waiting:
                self.bt.env.append_raw(data.create_realtime_dataset([self.stock_symbol]))
                self.msleep(int(self.wait_seconds*1000))
                continue
            for info in infos:
                self.signal.emit(info)