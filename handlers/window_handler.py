import sys, datetime, os
import tradeinfo
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class Handler:
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
            self.backtest_trade_status_label.setText(f"{position} : {ttype} {units} for {price}, {p}")
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            self.backtest_plot.update_plot(date, net_wealth)
        elif(infotype == tradeinfo.InfoType.CLOSINGOUT):
            self.previous_net_wealth = net_wealth
            QMessageBox.information(self, 'CLOSED OUT', f'performance : {info.performance}, net : {net_wealth}')
    
    def show_error(self, message):
        QMessageBox.critical(self, "Error", f"{message}")
    
    def handle_train_init_error(self, lags, symbols, target=None):
        lags_limit = 13
        if lags > lags_limit:
            self.show_error(f"lags({lags}) value is too big.")
            return -1
        if len(symbols) < 2:
            self.show_error(f"Symbol list size must be more than 2.")
            return -1
        if target != None and target == "":
            self.show_error(f"Target shouldn't be empty.")
            return -1
        return 0
    def handle_flaw_dataset(self, df):
        if df.empty:
            self.show_error(f"Dataset made from your symbols is empty. Check your symbols")
            return -1
        return 0
    def handle_model_path_error(self, model_path):
        if model_path == None or not os.path.isfile(model_path):
            self.show_error(f"Model path {model_path} is not available.")
            return -1
        return 0
            