import tensorflow as tf
import numpy as np
import random
import math, os
import pandas as pd
from enum import IntEnum
import data, models

def set_seeds(seed=100):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

class observation_space:
    def __init__(self, n):
        self.shape = (n,)
class action_space:
    def __init__(self, n):
        self.n = n
    def sample(self):
        return random.randint(0, self.n - 1)

class FinanceEnv:
    def __init__(self, raw, symbol, features, lags, data_preparing_func, min_performance=0.85, start=0, end=None):
        self.symbol = symbol
        self.features = features
        self.n_features = len(features)
        self.lags = lags
        self.min_performance = min_performance
        self.start = start
        self.end = end
        self.raw = raw
        self.observation_space = observation_space(self.lags)
        self.action_space = action_space(2)
        self.prepare_data = data_preparing_func
        self.data, self.data_, cols = self.prepare_data(self.raw)

    def append_raw(self, data):
        self.raw = pd.concat([self.raw, data])
        self.data, self.data_, cols = self.prepare_data(self.raw)

    def _get_state(self):
        return self.data_[self.features].iloc[self.bar - self.lags:self.bar]

    def get_state(self, bar):
        return self.data_[self.features].iloc[bar - self.lags:bar]

    def reset(self):
        self.total_reward = 0
        self.performance = 1
        self.bar = self.lags
        state = self.data_[self.features].iloc[self.bar - self.lags:self.bar]
        return state.values

    def step(self, action):
        correct = action == self.data['d'].iloc[self.bar]
        ret = self.data['r'].iloc[self.bar]
        pos_reward = 1 if correct else 0
        penalty_reward = abs(ret) if correct else -abs(ret)
        
        sma = self.data['sma'].iloc[self.bar]
        ema = self.data['ema'].iloc[self.bar]
        rsi = self.data['rsi'].iloc[self.bar]
        # 이동평균선 상향돌파 시 보상, 하향돌파 시 패널티
        if self.data[self.symbol].iloc[self.bar] > sma:
            pos_reward += 1
        else:
            pos_reward -= 1
        # 지수 이동평균상 상향돌파 시 보상, 하향돌파 시 패널티
        if self.data[self.symbol].iloc[self.bar] > ema:
            pos_reward += 1
        else:
            pos_reward -= 1
        # RSI가 70 이상이면 과매수, 30 이하이면 과매도로 패널티
        if rsi > 70 or rsi < 30:
            pos_reward -= 1
        
        self.bar += 1
        self.performance *= math.exp(penalty_reward)
        self.total_reward += pos_reward
        if self.bar >= len(self.data):
            done = True
        elif pos_reward == 1:
            done = False
        elif (self.performance < self.min_performance and self.bar > self.lags + 15):
            done = True
        else:
            done = False
        state = self._get_state()
        info = {}
        return state.values, pos_reward + penalty_reward * 5, done, info
    
class StoplossEnv:
    def __init__(self, historical_data, column_name, lags, stoploss=-0.02):
        self.column = column_name
        self.lags = lags
        self.observation_space = observation_space(self.lags)
        self.action_space = action_space(2)
        self.data = historical_data
        self.stoploss = stoploss

    def append_raw(self, data):
        self.data = pd.concat([self.data, data])
        
    def _get_state(self):
        return self.data[self.column].iloc[self.bar - self.lags:self.bar]
    
    def get_state(self, bar):
        return self.data[self.column].iloc[bar - self.lags:bar]

    def get_price(self, bar):
        return self.data[self.column].iloc[bar]
    
    def seed(self, seed):
        random.seed(seed)
        np.random.seed(seed)

    def reset(self):
        self.total_reward = 0
        self.bar = self.lags
        self.prev_price = self.get_price(self.bar)
        state = self.data[self.column].iloc[self.bar - self.lags:self.bar]
        return state.values

    def _calculate_profit(self, p1, p2):
        if p1 > p2:
            return (p2 - p1) / p1
        else:
            return (p1 - p2) / p2
    
    def step(self, action):
        current_price = self.get_price(self.bar)
        self.bar += 1
        reward = 1 if action == 0 and self.prev_price <= current_price else 0
        profit = self._calculate_profit(current_price, self.prev_price)

        if self.bar >= len(self.data):
            done = True
        elif action == 1 and profit >= self.stoploss:
            reward += 1    
            done = True
        else:
            reward -= 1
            done = False
            
        self.total_reward += reward        
        self.prev_price = current_price
        state = self._get_state()
        return state.values, reward, done, {}


class Agent(IntEnum):
    SIDEWAY = 0
    RSI_TRADE = 1
    SMA_TRADE = 2
    
def get_model_paths(dir):
    models = ["sideway.keras", "rsi trade.keras", "sma trade.keras"]
    paths = []
    for model in models:
        paths.append(os.path.join(dir, model))
    return paths
    
class StockMarketEnvironment:
    def __init__(self, agents, df, target, window=20, lags=3):
        self.agents = agents
        self.target = target
        self.bar = 0 
        self.min_performance = 0.75
        self.lags = lags
        self.window = window
        self._prepare_data = data.prepare_stock_data
        self.raw = df
        self.df, self.df_, self.features = self._prepare_data(df, target)
        self.n_features = len(self.features)
    
    def _get_state(self):
        return np.array([[self.df_.iloc[self.bar-self.lags:self.bar]]])
    def get_state(self, bar):
        return np.array([[self.df_.iloc[bar-self.lags:bar]]])
    
    def append_raw(self, d):
        self.raw = pd.concat([self.raw, d])
        self.df, self.df_, self.features = self._prepare_data(self.raw, self.target)

    def reset(self):
        self.total_reward = 0
        self.bar = self.lags
        state = self.df_.iloc[self.bar - self.lags:self.bar]
        return [state.values, state.values, state.values]

    def _detect_low_volatility_signal(self, data, window=20, threshold=0.07):
        rolling_std = data.rolling(window=window).std()
        return rolling_std < threshold
    
    def step(self, acts):
        #sideway trading/holding rewarding
        is_low = self._detect_low_volatility_signal(self.df_[self.target][self.bar:self.bar + self.window], self.window, 0.07)
        sideway_reward = 0 if is_low.iloc[-1] == True else 1
        
        low_upper = self._detect_low_volatility_signal(self.df_['upper'][self.bar:self.bar + self.window], self.window, 0.05)
        low_lower = self._detect_low_volatility_signal(self.df_['lower'][self.bar:self.bar + self.window], self.window, 0.05)
        if low_upper.iloc[-1] or low_lower.iloc[-1]:
            sideway_reward -= 1
    
    #trade rewarding
    
        d = self.df['d'].iloc[self.bar]
        price = self.df_[self.target].iloc[self.bar]
        rsi_trade_reward = 0
        sma_trade_reward = 1 if acts[Agent.SMA_TRADE] == d else 0
        sma = self.df_['sma'].iloc[self.bar]
        ema = self.df_['ema'].iloc[self.bar]
        rsi = self.df['rsi'].iloc[self.bar]
        
        if price > sma or price > ema:
            sma_trade_reward += 1
        else:
            sma_trade_reward -= 1
        
        if (rsi < 70) and (price < self.df_['lower'].iloc[self.bar]):
            rsi_trade_reward -= 1
        elif (rsi > 30) and (price > self.df_['upper'].iloc[self.bar]):
            rsi_trade_reward += 1
        
        if rsi > 70 or rsi < 30:
            rsi_trade_reward -= 1
    
        self.total_reward += sma_trade_reward + rsi_trade_reward + sideway_reward
        
        self.bar += 1        
        if self.bar >= len(self.df_):
            done = True
        else:
            done = False
        info = {}
        
        sideway_state = self._get_state()
        rsi_trade_state = self._get_state()
        sma_trade_state = self._get_state()
        return [sideway_state, rsi_trade_state, sma_trade_state], [sideway_reward, rsi_trade_reward, sma_trade_reward], done, info