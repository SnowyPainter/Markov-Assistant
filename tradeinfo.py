from enum import Enum

class InfoType(Enum):
    STOPLOSS = 1
    TRAILSTOPLOSS = 2
    TAKEPROFIT = 3
    CLOSINGOUT = 4
    NETWEALTH = 5
class TradePosition(Enum):
    LONG = 1
    SHORT = 2

class TradeInfo:
    def __init__(self):
        self.units = -1
        self.balance = -1
    def set_stoploss(self, p, pos):
        self.trade_type = InfoType.STOPLOSS
        self.trade_position = pos
        self.stoploss = p
    def set_trailing_stoploss(self, p, pos):
        self.trade_type = InfoType.TRAILSTOPLOSS
        self.trade_position = pos
        self.stoploss = p
    def set_takeprofit(self, p, pos):
        self.trade_type = InfoType.TAKEPROFIT
        self.trade_position = pos
        self.takeprofit = p
    def set_price(self, price):
        self.price = price
    def set_units(self, units):
        self.units = units
    def set_balance(self, balance):
        self.balance = balance
    def set_performance(self, perf):
        self.performance = perf
    def set_trade_type(self, trade_type):
        self.trade_type = trade_type
    def set_trade_position(self, trade_position):
        self.trade_position = trade_position