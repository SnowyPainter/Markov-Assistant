import tensorflow as tf
import numpy as np
import random
import math
import pandas as pd

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
    def __init__(self, raw, symbol, features, window, lags, data_preparing_func, min_performance=0.85, start=0, end=None):
        self.symbol = symbol
        self.features = features
        self.n_features = len(features)
        self.window = window
        self.lags = lags
        self.min_performance = min_performance
        self.start = start
        self.end = end
        self.raw = raw
        self.action_space = action_space(2)
        self.prepare_data = data_preparing_func
        self.data, self.data_ = self.prepare_data(self.raw, self.start, self.end, self.symbol, self.window)

    def append_raw(self, data):
        self.raw = pd.concat([self.raw, data])
        self.data, self.data_ = self.prepare_data(self.raw, self.start, self.end, self.symbol, self.window)

    def _get_state(self):
        return self.data_[self.features].iloc[self.bar - self.lags:self.bar]

    def get_state(self, bar):
        return self.data_[self.features].iloc[bar - self.lags:bar]

    def reset(self):
        self.total_reward = 0
        self.performance = 1
        self.bar = self.lags
        state = self.data_[self.features].iloc[self.bar -
                                               self.lags:self.bar]
        return state.values

    def step(self, action):
        correct = action == self.data['d'].iloc[self.bar]
        ret = self.data['r'].iloc[self.bar]
        pos_reward = 1 if correct else 0
        penalty_reward = abs(ret) if correct else -abs(ret)
        self.total_reward += pos_reward
        self.bar += 1
        self.performance *= math.exp(penalty_reward)
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
    def __init__(self, purchased_price, historical_data, column_name, lags):
        self.column = column_name
        self.lags = lags
        self.observation_space = observation_space(self.lags)
        self.action_space = action_space(2)
        self.data = historical_data
        self.purchased_price = purchased_price

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
        self.performance = 1
        self.holding = 0
        self.bar = self.lags
        self.prev_profit = []
        self.prev_price = self.get_price(self.bar)
        state = self.data[self.column].iloc[self.bar - self.lags:self.bar]
        return state.values

    def _calculate_profit(self, p1, p2):
        if p1 > p2:
            return (p2 - p1) / p1
        else:
            return (p1 - p2) / p1
    
    def step(self, action):
        current_price = self.get_price(self.bar)
        self.bar += 1
        positive_reward = 1 if action == 0 and self.prev_price <= current_price else 0
        profit = self._calculate_profit(current_price, self.purchased_price)
        penalty_reward = np.exp(profit) if profit >= 0 else -np.exp(profit)

        self.prev_profit.append(profit)
        if action == 1 and profit < min(self.prev_profit):
            penalty_reward *= 2
        
        self.total_reward += positive_reward
        self.performance *= math.exp(penalty_reward)
        
        if self.bar >= len(self.data) - 1:
            done = True
        if action == 0: #hold
            done = False
        elif action == 1: #sell
            done = True
        self.prev_price = current_price
        state = self._get_state()
        self.holding += 1
        return state.values, positive_reward + penalty_reward, done, {}