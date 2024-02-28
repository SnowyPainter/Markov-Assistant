import data
import environment
import riskmanager
import tradeinfo
import pandas as pd
import time
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
        timer = time.time()
        self.monitor = riskmanager.MonitorStock(self.env)
        for info in self.monitor.monitor():
            timer_curr = time.time()
            if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
                self.monitor.env.append_raw(data.create_realtime_dataset([self.symbol]))
            
            if timer_curr - timer >= int(self.interval_sec):
                self.signal.emit(info)
                timer = timer_curr