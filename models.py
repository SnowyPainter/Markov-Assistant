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
from environment import *

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

class SARSA:
    def __init__(self, env, epsilon=1.0, epsilon_min=0.1, epsilon_decay=0.999, discount_factor=0.8):
        self.env = env
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.discount_factor = discount_factor
        self.max_treward = 0
        self.averages = list()
        self.total_rewards = []
        self.performances = list()
        self.memory = deque(maxlen=2000)
        self.model = self._build_model()

    def _build_model(self):
        model = Sequential()
        model.add(Dense(48, input_shape=(self.env.lags, self.env.n_features), activation='relu'))
        model.add(Dropout(0.2, seed=100))
        model.add(Dense(24, activation='relu'))
        model.add(Dropout(0.2, seed=100))
        model.add(Dense(self.env.action_space.n, activation='linear'))
        model.compile(loss='mse',optimizer=RMSprop(learning_rate=0.001))
        return model

    def get_action(self, state):
        if random.random() <= self.epsilon:
            return self.env.action_space.sample()
        action = self.model.predict(state, verbose=0)[0, 0]
        return np.argmax(action)

    def fit(self):
        batch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in batch:
            if not done:
                reward += self.discount_factor * np.amax(self.model.predict(next_state, verbose=0)[0, 0])
            target = self.model.predict(state, verbose=0)
            target[0, 0, action] = reward
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def learn(self, episodes, batch_size):
        self.batch_size = batch_size
        for e in range(1, episodes + 1):
            state = self.env.reset()
            state = np.reshape(state, [1, self.env.lags,
                                       self.env.n_features])
            for _ in range(10000):
                action = self.get_action(state)
                next_state, reward, done, info = self.env.step(action)
                next_state = np.reshape(next_state,[1, self.env.lags, self.env.n_features])
                self.memory.append([state, action, reward, next_state, done])
                state = next_state
                if done:
                    treward = _ + 1
                    self.total_rewards.append(treward)
                    perf = self.env.performance
                    self.performances.append(perf)
                    self.max_treward = max(self.max_treward, treward)
                    yield EpisodeData(e, treward, self.max_treward, perf)
                    break
            if len(self.memory) > self.batch_size:
                self.fit()

def build_model(input_shape, output_size):
    model = Sequential()
    model.add(Dense(48, input_shape=input_shape, activation='relu'))
    model.add(Dropout(0.2, seed=100))
    model.add(Dense(24, activation='relu'))
    model.add(Dropout(0.2, seed=100))
    model.add(Dense(output_size, activation='linear'))
    model.compile(loss='mse', optimizer=RMSprop(learning_rate=0.001))
    return model

class QLearningAgent:
    def __init__(self, env, build_model, learning_rate=0.1, discount_factor=0.99, epsilon=0.7, epsilon_decay=0.999, epsilon_min=0.1):
        self.env = env
        self.step_size = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.model = build_model((self.env.lags, 1), self.env.action_space.n)

    def get_action(self, state):
        if random.random() <= self.epsilon:
            return self.env.action_space.sample()
        else:
            q_table = self.model.predict(np.array([state]), verbose=0)[0,0]
            return np.argmax(q_table)

    def update_q_values(self, state, action, reward, next_state):
        self.q_table = self.model.predict(np.array([state]), verbose=0)
        next_q_table = self.model.predict(np.array([next_state]), verbose=0)
        best_next_action = np.argmax(next_q_table)
        td_target = reward + self.discount_factor * next_q_table.flatten()[best_next_action]
        td_error = td_target - self.q_table.flatten()[action]
        self.q_table[np.unravel_index(action, self.q_table.shape)] += self.step_size * td_error
        self.model.fit(np.array([state]), self.q_table, verbose=0)
    
    def fit(self, batch_states, batch_q_tables):
        for state, q_table in zip(batch_states, batch_q_tables):
            self.model.fit(np.array(state), np.array(q_table), epochs=1, verbose=0)
    
    def learn(self, episodes, batch_size):
        batch_states, batch_q_tables = [], []
        for episode in range(episodes):
            state = self.env.reset()
            done = False
            while not done:
                action = self.get_action(state)
                next_state, reward, done, _ = self.env.step(action)
                self.update_q_values(state, action, reward, next_state)
                batch_states.append([next_state])
                batch_q_tables.append(self.model.predict(np.array([state]), verbose=0))
                if len(batch_states) >= batch_size:
                    self.fit(batch_states, batch_q_tables)
                    batch_states, batch_q_tables = [], []
                    if self.epsilon > self.epsilon_min:
                        self.epsilon *= self.epsilon_decay
            yield EpisodeData(episode+1, treward=self.env.total_reward, performance=self.env.performance)