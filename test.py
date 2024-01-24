import data
import models
def dnn_lstm_test():
    symbols = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
    y3 = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    #mo1_5m = data.create_dataset(symbols, start=data.today_before(data.days_to_months(1)), end=data.today(), interval='5min')

    lags = 3
    sr = 0.8

    y3_r, r_cols = data.add_rate_of_return(y3)
    y3_lagged, lag_cols = data.add_lags(y3, lags)

    y3_lagged_norm = data.normalize_zscore(y3_lagged)

    X_train, X_test, y_train, y_test = data.split_train_test(y3_lagged_norm, 'nvda_Price', lag_cols, lags=lags, split_ratio=sr)
    dnn = models.DNN(X_train, X_test, y_train, y_test, verbose=True)
    dnn.compile()
    dnn.fit(100, './models/dnn.h5', skip_if_exist=True)
    print(dnn.predict(X_test))

    r = y3_r[r_cols].values
    lstm = models.LSTM_Sequential(r, lags, len(r[0]), 10, 50, verbose=True)
    lstm.compile()
    lstm.fit(100, 10, './models/lstm.h5', skip_if_exist=True)
    print(lstm.predict(r))

print(data.get_realtime_price('nvda')["currentPrice"])