from tensorflow import keras
import tradeinfo, environment, riskmanager, data
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class QTMonitorStockThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, model_path, target_symbol, lags, wait_interval):
        super(QThread, self).__init__()
        self.target_symbol = target_symbol
        self.model = keras.models.load_model(model_path)
        self.wait_interval = wait_interval
        column = target_symbol+"_Price"
        df = pd.DataFrame({column:[], "Datetime": []})
        df.set_index('Datetime', inplace=True)
        self.env = environment.StoplossEnv(df, column, lags=lags)
    
    def stop(self):
        self.monitor.stop_monitor()
    
    def run(self):
        self.monitor = riskmanager.MonitorStoploss(self.env, self.model)
        for info in self.monitor.monitor():
            if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA:
                self.monitor.env.append_raw(data.create_realtime_dataset([self.target_symbol]))
            self.msleep(int(self.wait_interval * 1000))
            self.signal.emit(info)