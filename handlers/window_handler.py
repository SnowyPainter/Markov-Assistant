import sys, datetime, os
import tradeinfo
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logger

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
            pos = "LONG" if position == tradeinfo.TradePosition.LONG else "SHORT"
            self.backtest_trade_status_label.setText(f"{pos} : {ttype} {units} for {price}, {p}")
            str_date = date
            date = datetime.datetime.strptime(str_date, '%Y-%m-%d').strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            self.backtest_plot.update_plot(date, net_wealth)
            logger.log_backtest(net_wealth, str_date, infotype=int(infotype), position=int(position), tradetype=int(action), p=p, units=units, price=price)
        elif(infotype == tradeinfo.InfoType.CLOSINGOUT or self.btt.stopped):
            self.previous_net_wealth = net_wealth
            logger.log_backtest(net_wealth, date, infotype=infotype)
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
            