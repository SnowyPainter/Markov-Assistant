import numpy as np
import tradeinfo
import datetime

class RiskManager():
    def _reshape(self, state):
        return np.reshape(state, [1, self.env.lags, self.env.n_features])

    def set_prices(self, price):
        self.entry_price = price
        self.min_price = price
        self.max_price = price

    def __init__(self, env, model, amount, ptc, ftc, verbose=True, waiting=False):
        self.env = env
        self.model = model
        self.initial_amount = amount
        self.current_balance = amount
        self.ptc = ptc
        self.ftc = ftc
        self.verbose = verbose
        self.units = 0
        self.trades = 0
        self.waiting = waiting

    def get_date_price(self, bar):
        date = str(self.env.data.index[bar])[:10]
        price = self.env.data[self.env.symbol].iloc[bar]
        return date, price

    def calculate_net_wealth(self, price):
        return self.current_balance + self.units * price

    def place_buy_order(self, bar, amount=None, units=None, gprice=None):
        date, price = self.get_date_price(bar)
        info = tradeinfo.TradeInfo(date)
        if gprice is not None:
            price = gprice
        if units is None:
            units = int(amount / price)
        self.current_balance -= (1 + self.ptc) * units * price + self.ftc
        self.units += units
        self.trades += 1
        self.set_prices(price)
        info.set_units(units)
        info.set_trade_type(tradeinfo.TradeType.BUY)
        info.set_price(price)
        return info

    def place_sell_order(self, bar, amount=None, units=None, gprice=None):
        date, price = self.get_date_price(bar)
        info = tradeinfo.TradeInfo(date)
        if gprice is not None:
            price = gprice
        if units is None:
            units = int(amount / price)
        self.current_balance += (1 - self.ptc) * units * price - self.ftc
        self.units -= units
        self.trades += 1
        self.set_prices(price)
        info.set_units(units)
        info.set_trade_type(tradeinfo.TradeType.SELL)
        info.set_price(price)
        return info

    def close_out(self, bar):
        infos = []
        if self.units < 0:
            infos.append(self.place_buy_order(bar, units=-self.units))
        else:
            infos.append(self.place_sell_order(bar, units=self.units))
        perf = (self.current_balance / self.initial_amount - 1) * 100
        info = tradeinfo.TradeInfo(datetime.datetime.now())
        info.set_info_type(tradeinfo.InfoType.CLOSINGOUT)
        info.set_balance(self.current_balance)
        info.set_performance(perf)
        infos.append(info)
        return infos

    def backtest_strategy(self, sl=None, tsl=None, tp=None, wait=5, guarantee=False):
        self.units = 0
        self.position = 0
        self.trades = 0
        self.sl = sl
        self.tsl = tsl
        self.tp = tp
        self.wait = 0
        self.current_balance = self.initial_amount
        self.net_wealths = list()
        
        bar = self.env.lags
        while bar < len(self.env.data) or self.waiting:
            if bar >= len(self.env.data): #data size is less than bar, wait for appending data or just waiting realtime data. for start.
                info = tradeinfo.TradeInfo(datetime.datetime.now())
                info.set_info_type(tradeinfo.InfoType.WAITFORNEWDATA)
                yield [info]
            elif bar < len(self.env.data):
                infos = []
                self.wait = max(0, self.wait - 1)
                date, price = self.get_date_price(bar)

                if sl is not None and self.position != 0:
                    rc = (price - self.entry_price) / self.entry_price
                    if self.position == 1 and rc < -self.sl:
                        tpinfo = self.place_sell_order(bar, units=self.units, gprice=price)
                        if guarantee:
                            price = self.entry_price * (1 - self.sl)
                            tpinfo.set_stoploss(-self.sl, tradeinfo.TradePosition.LONG)
                        else:
                            tpinfo.set_stoploss(rc, tradeinfo.TradePosition.LONG)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0
                    elif self.position == -1 and rc > self.sl:
                        tpinfo = self.place_buy_order(bar, units=-self.units, gprice=price)
                        if guarantee:
                            price = self.entry_price * (1 + self.sl)
                            tpinfo.set_stoploss(-self.sl, tradeinfo.TradePosition.SHORT)
                        else:
                            tpinfo.set_stoploss(rc, tradeinfo.TradePosition.SHORT)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0

                if tsl is not None and self.position != 0:
                    self.max_price = max(self.max_price, price)
                    self.min_price = min(self.min_price, price)
                    sell_rc = (price - self.max_price) / self.entry_price
                    buy_rc = (self.min_price - price) / self.entry_price
                    if self.position == 1 and sell_rc < -self.tsl:
                        tpinfo = self.place_sell_order(bar, units=self.units)
                        tpinfo.set_trailing_stoploss(sell_rc, tradeinfo.TradePosition.LONG)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0
                    elif self.position == -1 and buy_rc < -self.tsl:
                        tpinfo = self.place_buy_order(bar, units=-self.units)
                        tpinfo.set_trailing_stoploss(buy_rc, tradeinfo.TradePosition.SHORT)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0

                if tp is not None and self.position != 0:
                    rc = (price - self.entry_price) / self.entry_price
                    if self.position == 1 and rc > self.tp:
                        tpinfo = self.place_sell_order(bar, units=self.units, gprice=price)
                        if guarantee:
                            price = self.entry_price * (1 + self.tp)
                            tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.LONG)
                        else:
                            tpinfo.set_takeprofit(rc, tradeinfo.TradePosition.LONG)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0
                    elif self.position == -1 and rc < -self.tp:
                        tpinfo = self.place_buy_order(bar, units=-self.units, gprice=price)
                        if guarantee:
                            price = self.entry_price * (1 - self.tp)
                            tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.SHORT)
                        else:
                            tpinfo.set_takeprofit(-rc, tradeinfo.TradePosition.SHORT)
                        infos.append(tpinfo)
                        self.wait = wait
                        self.position = 0

                state = self.env.get_state(bar)
                action = np.argmax(self.model.predict(self._reshape(state.values), verbose=0)[0, 0])
                position = 1 if action == 1 else -1
                if self.position in [0, -1] and position == 1 and self.wait == 0:
                    if self.position == -1:
                        tpinfo = self.place_buy_order(bar - 1, units=-self.units)
                        tpinfo.set_trade_position(tradeinfo.TradePosition.LONG)
                        infos.append(tpinfo)
                    tpinfo = self.place_buy_order(bar - 1, amount=self.current_balance)
                    tpinfo.set_trade_position(tradeinfo.TradePosition.LONG)
                    infos.append(tpinfo)
                    self.position = 1
                elif self.position in [0, 1] and position == -1 and self.wait == 0:
                    if self.position == 1:
                        tpinfo = self.place_sell_order(bar - 1, units=self.units)
                        tpinfo.set_trade_position(tradeinfo.TradePosition.SHORT)
                        infos.append(tpinfo)
                    tpinfo = self.place_sell_order(bar - 1, amount=self.current_balance)
                    tpinfo.set_trade_position(tradeinfo.TradePosition.SHORT)
                    infos.append(tpinfo)
                    self.position = -1
                    
                self.net_wealths.append([date, self.calculate_net_wealth(price)])
                bar += 1
                if len(infos) > 0:
                    yield infos
        
        bar -= 1

        yield self.close_out(bar)
        
class MonitorStock:
    def __init__(self, env, model):
        self.env = env
        self.model = model
        self.stop = False
    def _reshape(self, state):
        return np.reshape(state, [1, self.env.lags, self.env.n_features])
    
    def get_date_price(self, bar):
        date = str(self.env.data.index[bar])[:10]
        price = self.env.data[self.env.symbol].iloc[bar]
        return date, price
    
    def stop_monitor(self):
        self.stop = True
    
    def monitor(self):
        self.position = 0 # none
        self.bar = self.env.lags
        
        while not self.stop:
            if self.bar >= len(self.env.data) or len(self.env.data) < self.env.lags:
                yield tradeinfo.wait_for_data()
                continue
            
            state = self.env.get_state(self.bar)
            action = np.argmax(self.model.predict(self._reshape(state.values), verbose=0)[0, 0])
            position = 1 if action == 1 else -1 #1 = buy, -1 = sell
            
            date, price = self.get_date_price(self.bar)
            ti = tradeinfo.none()
            ti.set_price(price)
            
            if self.position in [0, -1] and position == 1:
                self.position = 1
                ti = tradeinfo.buy(price)
            elif self.position in [0, 1] and position == -1:
                self.position = -1
                ti = tradeinfo.sell(price)
            
            self.bar += 1
            yield ti
            
        