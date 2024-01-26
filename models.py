import matplotlib.pyplot as plt
import numpy as np
import os
import data
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

def dnn_prepare_dataset(df, lags, target_feature, split_ratio=0.8):
    df, cols = data.add_lags(df, lags)
    df['target'] = 0.8 * df[target_feature]
    df.dropna(inplace=True)
    train_size = int(len(df) * split_ratio)
    train = df.iloc[0:train_size]
    test = df.iloc[train_size:]
    m, std = train.mean(), train.std()
    train_ = (train - m) / std
    test_ = (test - m) / std
    return  train_[cols], test_[cols], train_['target'], test_['target']

def dnn_prepare_for_prediction_dataset(df, lags):
    df, lag_cols = data.add_lags(df, lags)
    return df[lag_cols]

def lstm_prepare_dataset(df):
    df, r_cols = data.add_rate_of_return(df)
    df = data.normalize_zscore(df)
    return df[r_cols]
    
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
        self.model.fit(self.X_train, self.y_train, epochs=epochs, validation_data=(self.X_test, self.y_test), verbose=self.verbose, callbacks=checkpoint_callback)

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
        self.model.fit(g, epochs=epochs, steps_per_epoch=steps_per_epoch, verbose=self.verbose, callbacks=[checkpoint_callback])
    
    def predict(self, values, batch_size=None):
        if batch_size == None:
            batch_size = self.batch_size
        values = values.reshape((len(values), -1))
        g = TimeseriesGenerator(values, values, length=self.lags, batch_size=batch_size)
        return load(self.save_path).predict(g)