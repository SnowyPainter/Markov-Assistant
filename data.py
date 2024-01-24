import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader as web
import pytz
from datetime import datetime, timedelta

def days_to_years(years):
    return 365.25 * years
def days_to_months(months):
    return 30.44 * months
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
    return t.info["currentPrice"]

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