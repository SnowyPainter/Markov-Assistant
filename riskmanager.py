import numpy as np
import tradeinfo, environment
import datetime, time

class RiskManager():
    def _reshape(self, state):
        return np.reshape(state, [1, self.env.lags, self.env.n_features])

    def set_prices(self, price):
        self.entry_price = price
        self.min_price = price
        self.max_price = price

    def __init__(self, env, amount, ptc, ftc, waiting=False):
        self.env = env
        self.initial_amount = amount
        self.current_balance = amount
        self.ptc = ptc
        self.ftc = ftc
        self.units = 0
        self.trades = 0
        self.waiting = waiting

    def get_date_price(self, bar):
        date = str(self.env.df.index[bar])[:10]
        price = self.env.df[self.env.target].iloc[bar]
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
        info.set_trade_type(tradeinfo.TradeType.NONE)
        info.set_balance(self.current_balance)
        info.set_performance(perf)
        infos.append(info)
        return infos

    def backtest_with_strategy(self, sl=None, tsl=None, tp=None, wait=10, guarantee=False):
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
        units = 0
        # 공매도 금지 설정
        while bar < len(self.env.df_) or self.waiting:
            if bar >= len(self.env.df_): #data size is less than bar, wait for appending data or just waiting realtime data. for start.
                info = tradeinfo.TradeInfo(datetime.datetime.now())
                info.set_info_type(tradeinfo.InfoType.WAITFORNEWDATA)
                yield [info]
            elif bar < len(self.env.df_):
                infos = []
                self.wait = max(0, self.wait - 1)
                date, price = self.get_date_price(bar)

                state = self.env.get_state(bar)
                state = self._reshape(state)
                trading = True if np.argmax(self.env.agents[environment.Agent.SIDEWAY].predict(state, verbose=0)[0, 0]) == 1 else False
                if trading:
                    action = np.argmax(self.env.agents[environment.Agent.TRADE].predict(state, verbose=0)[0, 0])
                    if action == 0:
                        info = self.place_buy_order(bar, self.current_balance)
                        if info.units > 0:
                            infos.append(info)
                    elif action == 1 and self.units > 0:
                        loss = (price - self.entry_price) / self.entry_price
                        
                        if loss >= self.tp:
                            tpinfo = self.place_sell_order(bar, units=self.units, gprice=price)
                            if guarantee:
                                price = self.entry_price * (1 + self.tp)
                                tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.LONG)
                                tpinfo.set_price(price)
                            else:
                                tpinfo.set_takeprofit(loss, tradeinfo.TradePosition.LONG)
                            infos.append(tpinfo)
                        #elif loss > self.ptc:
                        #    tpinfo = self.place_sell_order(bar, units=self.units, gprice=price)
                        #    tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.LONG)
                        #    infos.append(tpinfo)
                        elif loss <= -self.sl:
                            slinfo = self.place_sell_order(bar, units=self.units, gprice=price)
                            slinfo.set_stoploss(loss, tradeinfo.TradePosition.LONG)
                            infos.append(slinfo)
                else:
                    holdinfo = tradeinfo.holding(price)
                    infos.append(holdinfo)
                self.net_wealths.append([date, self.calculate_net_wealth(price)])
                bar += 1
                if len(infos) > 0:
                    yield infos
        
        bar -= 1

        yield self.close_out(bar)
        
class MonitorStock:
    def __init__(self, env):
        self.env = env
        self.stop = False
    def _reshape(self, state):
        return np.reshape(state, [1, self.env.lags, self.env.n_features])
    
    def get_date_price(self, bar):
        date = str(self.env.df.index[bar])[:10]
        price = self.env.df[self.env.target].iloc[bar]
        return date, price
    
    def stop_monitor(self):
        self.stop = True
    
    def monitor(self):
        self.position = 0 # none
        self.bar = self.env.lags
        entry = 0
        units = 0
        
        sec1_timer = time.time()
        
        while not self.stop:
            sec1_timer_curr = time.time()

            if sec1_timer_curr - sec1_timer >= 1:
                sec1_timer = sec1_timer_curr
                yield tradeinfo.wait_for_data()
            if self.bar >= len(self.env.df_) or len(self.env.df_) < self.env.lags:
                continue

            date, price = self.get_date_price(self.bar)
            state = self.env.get_state(self.bar)

            ti = tradeinfo.none()
            ti.set_price(price)
            
            trading = True if np.argmax(self.env.agents[environment.Agent.SIDEWAY].predict(self._reshape(state), verbose=0)[0, 0]) == 1 else False
            if trading:
                action = np.argmax(self.env.agents[environment.Agent.TRADE].predict(self._reshape(state), verbose=0)[0, 0])
                if action == 0:
                    entry = price
                    units += 1
                    ti.set_trade_type(tradeinfo.TradeType.BUY)
                elif action == 1 and units > 0:
                    loss = (price - entry) / entry
                    units -= 1
                    ti.set_trade_type(tradeinfo.TradeType.SELL)
                    if loss > 0.0025:
                        ti.set_info_type(tradeinfo.InfoType.TAKEPROFIT)
                    else:
                        ti.set_info_type(tradeinfo.InfoType.STOPLOSS)
                        
            else:
                ti.set_trade_type(tradeinfo.TradeType.NONE)
                ti.set_info_type(tradeinfo.InfoType.HOLDING)
            
            self.bar += 1
            yield ti
            
class MonitorStoploss:
    def __init__(self, env, model):
        self.env = env
        self.model = model
        self.stop = False
    
    def stop_monitor(self):
        self.stop = True
    
    def monitor(self):
        order = 0
        i = 0
        lags = self.env.lags
        while not self.stop:
            if i >= len(self.env.data) - lags - 1:
                yield tradeinfo.wait_for_data()
            elif order == 0 and i < len(self.env.data) - lags - 1:
                order = np.argmax(self.model.predict(np.array([self.env.data.iloc[i:i+lags]]), verbose=0))
                if order == 1:
                    self.stop = True
                    break
                ti = tradeinfo.none()
                ti.set_price(self.env.data.iloc[i])
                yield ti
                i += 1
        if order == 1:
            yield tradeinfo.sell(self.env.data.iloc[i+lags])
        else:
            ti = tradeinfo.none()
            ti.set_price(self.env.data.iloc[i])
            yield ti
            
        