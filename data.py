import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, timedelta, time
import os

def a2c_filename(fname):
    dirname, filename = os.path.split(fname)
    name, ext = os.path.splitext(filename)
    actor_path = os.path.join(dirname, f'{name}_actor.keras')
    critic_path = os.path.join(dirname, f'{name}_critic.keras')
    return actor_path, critic_path

def days_to_years(years):
    return 365.25 * years
def days_to_months(months):
    return 30.44 * months
def is_market_open():
    return time(9, 30) < datetime.now(pytz.timezone('US/Eastern')).time() < time(16, 0)
def today():
    return datetime.now(pytz.timezone('US/Eastern'))
def today_before(day):
    return datetime.now(pytz.timezone('US/Eastern')) - timedelta(days=day)
def date_day_range(start, end):
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]

def get_local_period_day_csv(filename):
    df = pd.read_csv(filename)
    df.drop(["Vol.","Change %","Open","Low","High"], axis=1, inplace=True)
    df["Price"] = df["Price"].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    df = df.sort_values(by='Date')
    df.set_index('Date', inplace=True)
    return df

def get_symbol_historical(symbol, start, end, period,interval):
    d = yf.download(symbol, start=start, end=end, period=period, interval=interval)
    d.rename(columns={'Open': symbol+'_Price'}, inplace=True)
    d.index = pd.to_datetime(d.index, format="%Y-%m-%d %H:%M:%S%z")
    d.dropna(inplace=True)
    return d[[symbol+'_Price']]

def get_realtime_price(ticker):
    t = yf.Ticker(ticker)
    return t.info.get('currentPrice')

def merge_dfs(dfs, on):
    merged = dfs[0]
    for i in range(1, len(dfs)):
        merged = merged.merge(dfs[i], on=on)
    return merged

def add_lags(df, lags, features=None):
    if features == None:
        features = list(df.columns)
    cols = []
    for lag in range(1, lags + 1):
        for feature in features:
            col = f'{feature}_lag{lag}'
            df[col] = df[feature].shift(lag)
            cols.append(col)
    return df, cols

#log rate of return
def add_rate_of_return(df, features=None):
    if features == None:
        features = list(df.columns)
    cols = []
    for feature in features:
        col = f'{feature}_r'
        df[col] = np.log(df[feature] / df[feature].shift(1))
        cols.append(col)
    df.dropna(inplace=True)
    return df, cols

def after_lags(df, lags):
    return df.iloc[lags:]

def normalize_zscore(original):
    m, s = original.mean(), original.std()
    return (original - m) / s

# target, features-lag
def split_train_test(df, target_feature, features, lags=0, split_ratio=0.8):
    df['target'] = split_ratio * df[target_feature]
    train_size = int(len(df) * split_ratio)
    train = df.iloc[0:train_size]
    test = df.iloc[train_size:]
    m, std = train.mean(), train.std()
    train_ = (train - m) / std
    test_ = (test - m) / std
    return  train_[features], test_[features], train_['target'], test_['target']

def create_dataset(symbols, start, end, interval):
    dfs = []
    for symbol in symbols:
        dfs.append(get_symbol_historical(symbol, start=start, end=end, period="max", interval=interval))
    return merge_dfs(dfs, on=dfs[0].index.name)

def create_realtime_dataset(tickers):
    df = pd.DataFrame()
    for ticker in tickers:
        df[ticker+'_Price'] = [get_realtime_price(ticker)]
    df['Datetime'] = [pd.to_datetime(today(), format="%Y-%m-%d %H:%M:%S%z")]
    df.set_index('Datetime', inplace=True)
    return df

def dnn_prepare_dataset(df, lags, target_feature, split_ratio=0.8):
    df, cols = add_lags(df, lags)
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
    df, lag_cols = add_lags(df, lags)
    return df[lag_cols]

def lstm_prepare_dataset(df):
    df, r_cols = add_rate_of_return(df)
    df = normalize_zscore(df)
    return df[r_cols]

def prepare_RSMV_data(df, start, end, symbol, window):
    data = pd.DataFrame(df[symbol])
    data = data.iloc[start:]
    data['r'] = np.log(data / data.shift(1))
    data.dropna(inplace=True)
    data['s'] = data[symbol].rolling(window).mean()
    data['m'] = data['r'].rolling(window).mean()
    data['v'] = data['r'].rolling(window).std()
    data.dropna(inplace=True)
    data_ = (data - data.mean()) / data.std()
    data['d'] = np.where(data['r'] > 0, 1, 0)
    data['d'] = data['d'].astype(int)
    if end is not None:
        data = data.iloc[:end - start]
        data_ = data_.iloc[:end - start]
    return data, data_