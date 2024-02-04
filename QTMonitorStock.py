import data
import models
import riskmanager
import tradeinfo
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class QTMonitorStockThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, target_symbol, model, model_lags, interval_sec):
        super(QThread, self).__init__()
        target = target_symbol + '_Price'
        self.tickers = [target_symbol]
        features = [target, 'r', 's', 'm', 'v']
        df = pd.DataFrame({target:[], 'Datetime':[]})
        df.set_index('Datetime')
        
        self.env = models.FinanceEnv(df, target, features=features,
                                window=10,
                                lags=model_lags, data_preparing_func=data.prepare_RSMV_data,
                                leverage=1,
                                min_performance=0.0, min_accuracy=0.0,
                                start=0, end=None)
        self.model = model
        self.interval_sec = interval_sec
    
    def stop(self):
        self.monitor.stop_monitor()
    
    def run(self):
        self.monitor = riskmanager.MonitorStock(self.env, self.model)
        for info in self.monitor.monitor():
            self.monitor.env.append_raw(data.create_realtime_dataset(self.tickers))
            self.msleep(int(self.interval_sec * 1000))
            self.signal.emit(info)