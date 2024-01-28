import data
import models
import backtester
import time
import threading
import matplotlib.pyplot as plt

y3_long_nvda_symbols = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
mo1_5m_long_nvda_tickers = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
updown_symbols = ["nvda", "amd", "intc"]

def get_tomorrow_updown(symbols):
    lags = 10
    train = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    mo1_5m = data.create_dataset(symbols, start=data.today_before(data.days_to_months(1)), end=data.today(), interval='1d')
    
    train_values = data.lstm_prepare_dataset(train).values
    test_values = data.lstm_prepare_dataset(mo1_5m).values
    
    lstm = models.LSTM_Sequential(lags, len(symbols), 10, 100, verbose=True)
    lstm.compile()
    lstm.fit(train_values, 100, 10, './models/lstm.keras', skip_if_exist=True)
    
    return lstm.predict(test_values)

def get_long_term_prediction(symbols):
    lags = 3
    df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    X_train, X_test, y_train, y_test = data.dnn_prepare_dataset(df, lags, "nvda_Price")
    dnn = models.DNN(X_train, X_test, y_train, y_test, verbose=2)
    dnn.compile()
    dnn.fit(100, './models/dnn.keras', skip_if_exist=True)
    
    df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    df = data.dnn_prepare_for_prediction_dataset(df, lags)
    return dnn.predict(df)

def learn_rl(train_symbols, model):
    symbol = 'nvda_Price'
    features = [symbol, 'r', 's', 'm', 'v']
    df = data.create_dataset(train_symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    learn_env = models.FinanceEnv(df, symbol, features, window=20, lags=3, data_preparing_func=data.prepare_RSMV_data,
                    leverage=1, min_performance=0.9, min_accuracy=0.475,
                    start=0, end=300)
    valid_env = models.FinanceEnv(df, symbol, features=learn_env.features,
                                window=learn_env.window,
                                lags=learn_env.lags, data_preparing_func=data.prepare_RSMV_data,
                                leverage=learn_env.leverage,
                                min_performance=0.0, min_accuracy=0.0,
                                start=300, end=None)

    models.set_seeds(100)
    agent = models.TradingBot(24, 0.001, learn_env, valid_env)
    episodes = 60
    agent.learn(episodes)
    agent.model.save(model)

#print(get_tomorrow_updown(updown_symbols))
#print(get_long_term_prediction(y3_long_nvda_symbols))
model = "./models/agent-NAI.keras"
#learn_rl(updown_symbols, model)