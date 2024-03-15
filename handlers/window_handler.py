import sys, datetime, os
import tradeinfo
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logger

class Handler:
    def handle_backtest_result(self, info):
        net_wealth = round(self.btt.bt.net_wealths[-1][1], 4)
        date = self.btt.bt.net_wealths[-1][0]
        price = round(info.price, 2)
        str_date = date
        dt = datetime.datetime.strptime(str_date, '%Y-%m-%d').strftime("%Y-%m-%d %H:%M:%S")
        dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        infotype = info.info_type
        position = info.trade_position
        self.backtest_plot.update_plot(dt, net_wealth)
        if price > 0:
            self.backtest_plot.canvas.add_multi_y_line_data(self.backtest_stock_price_plot, dt, price)
        if info.trade_type == tradeinfo.TradeType.BUY or info.trade_type == tradeinfo.TradeType.SELL:
            units = info.units
            action = info.trade_type
            ttype = "Buy" if action == tradeinfo.TradeType.BUY else "Sell"
            p = 0
            if infotype == tradeinfo.InfoType.TAKEPROFIT:
                p = info.takeprofit
            elif infotype == tradeinfo.InfoType.STOPLOSS:
                p = info.stoploss
            elif infotype == tradeinfo.InfoType.TRAILSTOPLOSS:
                p = info.stoploss
            self.backtest_trade_status_label.setText(f"{ttype} {units} for {price}, {p}")
            
            logger.log_backtest(net_wealth, str_date, infotype=int(infotype), position=int(position), tradetype=int(action), p=p, units=units, price=price)
        elif(infotype == tradeinfo.InfoType.HOLDING):
            price = round(info.price, 4)
            self.backtest_trade_status_label.setText(f"Holding {price}")
        elif(infotype == tradeinfo.InfoType.CLOSINGOUT or self.btt.stopped):
            self.previous_net_wealth = net_wealth
            self.backtesting = False
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
    def handle_model_path_error(self, model_paths):
        result = -1
        for path in model_paths:
            if not os.path.isfile(path):
                self.show_error(f"Model path {path} is not available.")
                result = -1
            else:
                result = 0
        return result
            