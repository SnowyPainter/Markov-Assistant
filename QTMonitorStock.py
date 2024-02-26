import data
import environment
import riskmanager
import tradeinfo
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class QTMonitorStockThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, symbol, env, interval_sec):
        super(QThread, self).__init__()
        self.env = env
        self.symbol = symbol
        df = pd.DataFrame({env.target:[], 'Datetime':[]})
        df.set_index('Datetime', inplace=True)
        self.interval_sec = interval_sec
    
    def stop(self):
        self.monitor.stop_monitor()
        self.quit()
        self.wait(500)
    
    def run(self):
        self.monitor = riskmanager.MonitorStock(self.env)
        for info in self.monitor.monitor():
            if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
                self.monitor.env.append_raw(data.create_realtime_dataset([self.symbol]))
            self.msleep(int(self.interval_sec * 1000))
            self.signal.emit(info)