import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, timedelta, time
import os

def days_to_years(years):
    return 365.25 * years
def days_to_months(months):
    return 30.44 * months

TIMEZONE_KRX = 'Asia/Seoul'
TIMEZONE_NYSE = 'America/New_York'

def today(tz = 'America/New_York'):
    return datetime.now(pytz.timezone(tz))
def today_minus_seconds(day, seconds=1):
    return day - timedelta(seconds=seconds)
def today_before(day, tz = 'America/New_York'):
    return datetime.now(pytz.timezone(tz)) - timedelta(days=day)

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

def create_info(symbol):
    return yf.Ticker(symbol).info

def create_dataset(symbols, start, end, interval):
    dfs = []
    for symbol in symbols:
        dfs.append(get_symbol_historical(symbol, start=start, end=end, period="max", interval=interval))
    return merge_dfs(dfs, on=dfs[0].index.name)

def create_realtime_dataset_by_price(symbol, price, tz=TIMEZONE_NYSE):
    df = pd.DataFrame()
    df[f"{symbol}_Price"] = [price]
    df['Datetime'] = [pd.to_datetime(today(tz=tz), format="%Y-%m-%d %H:%M:%S%z")]
    df.set_index('Datetime', inplace=True)
    return df

def create_realtime_dataset(tickers, tz=TIMEZONE_NYSE):
    df = pd.DataFrame()
    for ticker in tickers:
        df[ticker+'_Price'] = [get_realtime_price(ticker)]
    df['Datetime'] = [pd.to_datetime(today(tz=tz), format="%Y-%m-%d %H:%M:%S%z")]
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

pd.options.mode.chained_assignment = None

def calculate_sma(prices, period=20):
    return prices.rolling(window=period).mean()

def calculate_ema(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices, period=14):
    delta = prices.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    if len(rs) == 0 or len(rs) > 0 and np.isnan(rs.iloc[-1]):
        return 50
    return 100 - (100 / (1 + rs))

def stock_data_columns():
    return ['sma', 'ema', 'rsi', 'r']

def prepare_stock_data(df, target):
    new = pd.DataFrame({
        target:df[target],
        "sma":calculate_sma(df[target]),
        "ema":calculate_ema(df[target]),
        "rsi":calculate_rsi(df[target]),
        "r":np.log(df[target] / df[target].shift(1))
    })
    new.dropna(inplace=True)
    
    new_ = (new - new.mean()) / new.std()
    new['d'] = np.where(new_['r'] > 0, 1, 0)
    return new, new_, new_.columns