from enum import IntEnum
import data

class InfoType(IntEnum):
    STOPLOSS = 1
    TRAILSTOPLOSS = 2
    TAKEPROFIT = 3
    CLOSINGOUT = 4
    NONE = 5
    WAITFORNEWDATA = 6
class TradeType(IntEnum):
    BUY = 1
    SELL = 2
    NONE = 3
class TradePosition(IntEnum):
    LONG = 1
    SHORT = 2
    NONE = 3

def wait_for_data():
    ti = TradeInfo(data.today())
    ti.set_info_type(InfoType.WAITFORNEWDATA)
    return ti

class TradeInfo:
    def __init__(self, date):
        self.date = date
        self.units = -1
        self.balance = -1
        self.info_type = InfoType.NONE
        self.trade_position = TradePosition.NONE
        self.takeprofit = -1
        self.stoploss = -1
        self.price = -1
        self.performance = -1
        
    def set_stoploss(self, p, pos):
        self.info_type = InfoType.STOPLOSS
        self.trade_position = pos
        self.stoploss = p
    def set_trailing_stoploss(self, p, pos):
        self.info_type = InfoType.TRAILSTOPLOSS
        self.trade_position = pos
        self.stoploss = p
    def set_takeprofit(self, p, pos):
        self.info_type = InfoType.TAKEPROFIT
        self.trade_position = pos
        self.takeprofit = p
    def set_trade_type(self, trade_type):
        self.trade_type = trade_type
    def set_price(self, price):
        self.price = price
    def set_units(self, units):
        self.units = units
    def set_balance(self, balance):
        self.balance = balance
    def set_performance(self, perf):
        self.performance = perf
    def set_info_type(self, info_type):
        self.info_type = info_type
    def set_trade_position(self, trade_position):
        self.trade_position = trade_position