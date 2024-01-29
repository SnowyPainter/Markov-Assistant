import matplotlib.pyplot as plt
import numpy as np
import os
import random
import math
from collections import deque
import pandas as pd
import tensorflow as tf
from pylab import plt, mpl
from tensorflow import keras
from tensorflow.keras.optimizers import RMSprop
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import mean_squared_error
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
from keras.layers import Dropout

def load(path):
    return load_model(path)

class TrainResult:
    def __init__(self, history, predictions):
        self.history = history
        self.predictions = predictions
    def get(self, key):
        if key in self.history:
            return self.history[key]
        return None

class EpisodeData:
    def __init__(self, episode=0, treward=0, max_treward=0, performance=0, epsilon=0):
        self.episode = episode
        self.treward = treward
        self.max_treward = max_treward
        self.performance = performance
        self.epsilon = epsilon

class DNN:
    def __init__(self, X_train, X_test, y_train, y_test, verbose=False):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.verbose = verbose
        
    def compile(self, lr=0.001, dop=0.2):
        self.model = Sequential()
        self.model.add(Dense(128, input_dim=self.X_train.shape[1], activation='relu'))
        self.model.add(Dropout(dop, seed=100))
        self.model.add(Dense(32, activation='relu'))
        self.model.add(Dropout(dop, seed=100))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer=Adam(learning_rate=lr), loss='mean_squared_error')
        
    def fit(self, epochs, save_path, skip_if_exist=False):
        self.save_path = save_path
        if os.path.exists(save_path) and skip_if_exist:
            return
        checkpoint_callback = ModelCheckpoint(save_path, save_best_only=True)
        return self.model.fit(self.X_train, self.y_train, epochs=epochs, validation_data=(self.X_test, self.y_test), verbose=self.verbose, callbacks=checkpoint_callback)

    def MSE(self):
        y_pred = self.model.predict(self.X_test)
        return mean_squared_error(self.y_test, y_pred)

    def predict(self, X):
        return load(self.save_path).predict(X)

class LSTM_Sequential:
    def __init__(self, lags, n_features, batch_size, LSTM_depth, verbose=False):
        self.lags = lags
        self.n_features = n_features
        self.batch_size = batch_size
        self.LSTM_depth = LSTM_depth
        self.verbose = verbose
        
    def compile(self):
        self.model = Sequential()
        self.model.add(LSTM(self.LSTM_depth, activation='relu', input_shape=(self.lags, self.n_features)))
        self.model.add(Dense(1))
        self.model.compile(optimizer='adam', loss='mse')
        
    def fit(self, values, epochs, steps_per_epoch, save_path, skip_if_exist=False):
        self.save_path = save_path
        if os.path.exists(save_path) and skip_if_exist:
            return
        g = TimeseriesGenerator(values, values, length=self.lags, batch_size=self.batch_size)
        checkpoint_callback = ModelCheckpoint(save_path)
        return self.model.fit(g, epochs=epochs, steps_per_epoch=steps_per_epoch, verbose=self.verbose, callbacks=[checkpoint_callback])
    
    def predict(self, values, batch_size=None):
        if batch_size == None:
            batch_size = self.batch_size
        values = values.reshape((len(values), -1))
        g = TimeseriesGenerator(values, values, length=self.lags, batch_size=batch_size)
        return load(self.save_path).predict(g)
    
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
    def __init__(self, raw, symbol, features, window, lags, data_preparing_func, leverage=1, min_performance=0.85, min_accuracy=0.5, start=0, end=None):
        self.symbol = symbol
        self.features = features
        self.n_features = len(features)
        self.window = window
        self.lags = lags
        self.leverage = leverage
        self.min_performance = min_performance
        self.min_accuracy = min_accuracy
        self.start = start
        self.end = end
        self.raw = raw
        self.observation_space = observation_space(self.lags)
        self.action_space = action_space(2)
        self.prepare_data = data_preparing_func
        self.data, self.data_ = self.prepare_data(self.raw, self.start, self.end, self.symbol, self.window)

    def append_raw(self, data):
        self.raw = pd.concat([self.raw, data])
        self.data, self.data_ = self.prepare_data(self.raw, self.start, self.end, self.symbol, self.window)

    def _get_state(self):
        return self.data_[self.features].iloc[self.bar -
                                              self.lags:self.bar]

    def get_state(self, bar):
        return self.data_[self.features].iloc[bar - self.lags:bar]

    def seed(self, seed):
        random.seed(seed)
        np.random.seed(seed)

    def reset(self):
        self.treward = 0
        self.accuracy = 0
        self.performance = 1
        self.bar = self.lags
        state = self.data_[self.features].iloc[self.bar -
                                               self.lags:self.bar]
        return state.values

    def step(self, action):
        correct = action == self.data['d'].iloc[self.bar]
        ret = self.data['r'].iloc[self.bar] * self.leverage
        reward_1 = 1 if correct else 0
        reward_2 = abs(ret) if correct else -abs(ret)
        self.treward += reward_1
        self.bar += 1
        self.accuracy = self.treward / (self.bar - self.lags)
        self.performance *= math.exp(reward_2)
        if self.bar >= len(self.data):
            done = True
        elif reward_1 == 1:
            done = False
        elif (self.performance < self.min_performance and
              self.bar > self.lags + 15):
            done = True
        elif (self.accuracy < self.min_accuracy and
              self.bar > self.lags + 15):
            done = True
        else:
            done = False
        state = self._get_state()
        info = {}
        return state.values, reward_1 + reward_2 * 5, done, info

class TradingBot:
    def __init__(self, hidden_units, learning_rate, learn_env,
                 valid_env, val=True):
        self.learn_env = learn_env
        self.valid_env = valid_env
        self.val = val
        self.epsilon = 1.0
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.99
        self.learning_rate = learning_rate
        self.gamma = 0.5
        self.batch_size = 128
        self.max_treward = 0
        self.averages = list()
        self.trewards = []
        self.performances = list()
        self.aperformances = list()
        self.vperformances = list()
        self.memory = deque(maxlen=2000)
        self.model = self._build_model(hidden_units, learning_rate)

    def _build_model(self, hu, lr):
        model = Sequential()
        model.add(Dense(hu, input_shape=(
            self.learn_env.lags, self.learn_env.n_features),
            activation='relu'))
        model.add(Dropout(0.3, seed=100))
        model.add(Dense(hu, activation='relu'))
        model.add(Dropout(0.3, seed=100))
        model.add(Dense(2, activation='linear'))
        model.compile(
            loss='mse',
            optimizer=RMSprop(learning_rate=lr)
        )
        return model

    def act(self, state):
        if random.random() <= self.epsilon:
            return self.learn_env.action_space.sample()
        action = self.model.predict(state, verbose=0)[0, 0]
        return np.argmax(action)

    def replay(self):
        batch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in batch:
            if not done:
                reward += self.gamma * np.amax(
                    self.model.predict(next_state, verbose=0)[0, 0])
            target = self.model.predict(state, verbose=0)
            target[0, 0, action] = reward
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def learn(self, episodes):
        for e in range(1, episodes + 1):
            state = self.learn_env.reset()
            state = np.reshape(state, [1, self.learn_env.lags,
                                       self.learn_env.n_features])
            for _ in range(10000):
                action = self.act(state)
                next_state, reward, done, info = self.learn_env.step(action)
                next_state = np.reshape(next_state,
                                        [1, self.learn_env.lags,
                                         self.learn_env.n_features])
                self.memory.append([state, action, reward,
                                    next_state, done])
                state = next_state
                if done:
                    treward = _ + 1
                    self.trewards.append(treward)
                    av = sum(self.trewards[-25:]) / 25
                    perf = self.learn_env.performance
                    self.averages.append(av)
                    self.performances.append(perf)
                    self.aperformances.append(
                        sum(self.performances[-25:]) / 25)
                    self.max_treward = max(self.max_treward, treward)
                    yield EpisodeData(e, treward, self.max_treward, perf)
                    break
            if self.val:
                yield self.validate(e, episodes)
            if len(self.memory) > self.batch_size:
                self.replay()
        print()

    def validate(self, e, episodes):
        state = self.valid_env.reset()
        state = np.reshape(state, [1, self.valid_env.lags,
                                   self.valid_env.n_features])
        for _ in range(10000):
            action = np.argmax(self.model.predict(state, verbose=0)[0, 0])
            next_state, reward, done, info = self.valid_env.step(action)
            state = np.reshape(next_state, [1, self.valid_env.lags,
                                            self.valid_env.n_features])
            if done:
                treward = _ + 1
                perf = self.valid_env.performance
                self.vperformances.append(perf)
                return EpisodeData(episode=e, epsilon=self.epsilon)