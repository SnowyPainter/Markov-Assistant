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

    def __init__(self, env, amount, ptc, ftc, timezone, waiting=False):
        self.env = env
        self.timezone = timezone
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

    def place_buy_order(self, bar, amount=None, units=None, gprice=None):
        date, price = self.get_date_price(bar)
        info = tradeinfo.TradeInfo(date)
        if gprice is not None:
            price = gprice
        if units is None:
            units = int(amount / price)
        self.units += units
        self.trades += 1
        self.set_prices(price)
        info.set_units(units)
        info.set_trade_type(tradeinfo.TradeType.BUY)
        info.set_price(price)
        return info, (1 + self.ptc) * units * price + self.ftc

    def place_sell_order(self, bar, amount=None, units=None, gprice=None):
        date, price = self.get_date_price(bar)
        info = tradeinfo.TradeInfo(date)
        if gprice is not None:
            price = gprice
        if units is None:
            units = int(amount / price)
        self.units -= units
        self.trades += 1
        self.set_prices(price)
        info.set_units(units)
        info.set_trade_type(tradeinfo.TradeType.SELL)
        info.set_price(price)
        return info, (1 - self.ptc) * units * price - self.ftc

    def close_out(self, bar):
        infos = []
        if self.units < 0:
            info, cost = self.place_buy_order(bar, units=-self.units)
            infos.append(info)
        else:
            info, cost = self.place_sell_order(bar, units=self.units)
            infos.append(info)
        perf = ((self.stgy_1_balance + self.stgy_2_balance) / self.initial_amount - 1) * 100
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
        self.entry_price = 0
        
        self.stgy_1_balance = self.initial_amount / 2
        self.stgy_2_balance = self.initial_amount / 2
        
        self.net_wealths = list()
        self.rsi_trade_units = 0
        self.sma_trade_units = 0
        
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
                
                sideway_agent = self.env.agents[environment.Agent.SIDEWAY]
                rsi_agent = self.env.agents[environment.Agent.RSI_TRADE]
                sma_agent = self.env.agents[environment.Agent.SMA_TRADE]
                
                trading = True if np.argmax(sideway_agent.predict(state, verbose=0)[0, 0]) == 1 else False
                rsi_action = np.argmax(rsi_agent.predict(state, verbose=0)[0, 0])
                sma_action = np.argmax(sma_agent.predict(state, verbose=0)[0, 0])
                
                if trading:
                    if rsi_action == 0:
                        info, cost = self.place_buy_order(bar, self.stgy_1_balance)
                        self.stgy_1_balance -= cost
                        self.rsi_trade_units += info.units
                        if info.units > 0:
                            infos.append(info)
                    if sma_action == 0:
                        info, cost = self.place_buy_order(bar, self.stgy_2_balance)
                        self.stgy_2_balance -= cost
                        self.rsi_trade_units += info.units
                        if info.units > 0:
                            infos.append(info)
                    if rsi_action == 1 and self.rsi_trade_units > 0:
                        loss = (price - self.entry_price) / self.entry_price
                        if loss >= self.tp:
                            tpinfo, cost = self.place_sell_order(bar, units=self.rsi_trade_units, gprice=price)
                            self.stgy_1_balance += cost
                            self.rsi_trade_units -= tpinfo.units
                            if guarantee:
                                price = self.entry_price * (1 + self.tp)
                                tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.LONG)
                                tpinfo.set_price(price)
                            else:
                                tpinfo.set_takeprofit(loss, tradeinfo.TradePosition.LONG)
                            infos.append(tpinfo)
                        elif loss <= -self.sl:
                            slinfo, cost = self.place_sell_order(bar, units=self.rsi_trade_units, gprice=price)
                            self.stgy_1_balance += cost
                            self.rsi_trade_units -= slinfo.units
                            slinfo.set_stoploss(loss, tradeinfo.TradePosition.LONG)
                            infos.append(slinfo)
                    if sma_action == 1 and self.sma_trade_units > 0:
                        loss = (price - self.entry_price) / self.entry_price
                        if loss >= self.tp:
                            tpinfo, cost = self.place_sell_order(bar, units=self.sma_trade_units, gprice=price)
                            self.stgy_2_balance += cost
                            self.sma_trade_units -= tpinfo.units
                            if guarantee:
                                price = self.entry_price * (1 + self.tp)
                                tpinfo.set_takeprofit(self.tp, tradeinfo.TradePosition.LONG)
                                tpinfo.set_price(price)
                            else:
                                tpinfo.set_takeprofit(loss, tradeinfo.TradePosition.LONG)
                            infos.append(tpinfo)
                        elif loss <= -self.sl:
                            slinfo, cost = self.place_sell_order(bar, units=self.sma_trade_units, gprice=price)
                            self.stgy_2_balance += cost
                            self.sma_trade_units -= slinfo.units
                            slinfo.set_stoploss(loss, tradeinfo.TradePosition.LONG)
                            infos.append(slinfo)
                else:
                    holdinfo = tradeinfo.holding(price, self.timezone)
                    infos.append(holdinfo)
                
                net_wealth = self.stgy_1_balance + self.stgy_2_balance + self.units * price
                self.net_wealths.append([date, net_wealth])
                bar += 1
                if len(infos) > 0:
                    yield infos
        
        bar -= 1

        self.stgy_1_balance += self.rsi_trade_units * price
        self.stgy_2_balance += self.sma_trade_units * price
        yield self.close_out(bar)

class StatelessStockMonitor:
    def __init__(self, env, timezone):
        self.env = env
        self.timezone = timezone
        self.bar = env.lags
        self.units = 0
        self.entry = 0
    def _reshape(self, state):
        return np.reshape(state, [1, self.env.lags, self.env.n_features])
    
    def get_price(self, bar):
        return self.env.df[self.env.target].iloc[bar]
    
    def get_monitor(self, stoploss=-0.02, takeprofit=0.04):
        if self.bar >= len(self.env.df_):
            return tradeinfo.wait_for_data(self.timezone)
        price = self.get_price(self.bar)
        state = self.env.get_state(self.bar)
        ti = tradeinfo.none(self.timezone)
        ti.set_price(price)
        trading = True if np.argmax(self.env.agents[environment.Agent.SIDEWAY].predict(self._reshape(state), verbose=0)[0, 0]) == 1 else False
        if trading:
            rsi_action = np.argmax(self.env.agents[environment.Agent.RSI_TRADE].predict(self._reshape(state), verbose=0)[0, 0])
            sma_action = np.argmax(self.env.agents[environment.Agent.SMA_TRADE].predict(self._reshape(state), verbose=0)[0, 0])
            if rsi_action == 0 or sma_action:
                self.entry = price
                self.units = 1
                ti.set_trade_type(tradeinfo.TradeType.BUY)
            elif (rsi_action == 1 or sma_action == 1) and self.units > 0:
                loss = (price - self.entry) / self.entry
                self.units = 0
                ti.set_trade_type(tradeinfo.TradeType.SELL)
                if loss > takeprofit:
                    ti.set_info_type(tradeinfo.InfoType.TAKEPROFIT)
                elif loss < stoploss:
                    ti.set_info_type(tradeinfo.InfoType.STOPLOSS)
                else:
                    ti.set_trade_type(tradeinfo.TradeType.NONE)
                    ti.set_info_type(tradeinfo.InfoType.HOLDING)
            else:
                ti.set_info_type(tradeinfo.InfoType.NONE)
        else:
            ti.set_trade_type(tradeinfo.TradeType.NONE)
            ti.set_info_type(tradeinfo.InfoType.HOLDING)
            
        self.bar += 1
        return ti
#FOR TEST
class MonitorStock:
    def __init__(self, env, timezone):
        self.env = env
        self.timezone = timezone
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
            infos = []
            if sec1_timer_curr - sec1_timer >= 1:
                sec1_timer = sec1_timer_curr
                infos.append(tradeinfo.wait_for_data(self.timezone))
                yield infos
                continue
            if self.bar >= len(self.env.df_) or len(self.env.df_) < self.env.lags:
                continue
            
            date, price = self.get_date_price(self.bar)
            state = self.env.get_state(self.bar)

            ti = tradeinfo.none(self.timezone)
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
                    elif loss < -0.02:
                        ti.set_info_type(tradeinfo.InfoType.STOPLOSS)
                    else:
                        ti.set_trade_type(tradeinfo.TradeType.NONE)
                else:
                    ti.set_info_type(tradeinfo.InfoType.NONE)
            else:
                ti.set_trade_type(tradeinfo.TradeType.NONE)
                ti.set_info_type(tradeinfo.InfoType.HOLDING)
            infos.append(ti)
            self.bar += 1
            yield infos
            
class MonitorStoploss:
    def __init__(self, env, model, timezone):
        self.env = env
        self.timezone = timezone
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
                yield tradeinfo.wait_for_data(self.timezone)
            elif order == 0 and i < len(self.env.data) - lags - 1:
                order = np.argmax(self.model.predict(np.array([self.env.data.iloc[i:i+lags]]), verbose=0))
                if order == 1:
                    self.stop = True
                    break
                ti = tradeinfo.none(self.timezone)
                ti.set_price(self.env.data.iloc[i])
                yield ti
                i += 1
        if order == 1:
            yield tradeinfo.sell(self.env.data.iloc[i+lags], self.timezone)
        else:
            ti = tradeinfo.none(self.timezone)
            ti.set_price(self.env.data.iloc[i])
            yield ti
            
        