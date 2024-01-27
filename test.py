import data
import models

y3_long_nvda_symbols = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
mo1_5m_long_nvda_tickers = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
updown_symbols = ["nvda", "amd", "intc"]

def get_tomorrow_updown(symbols):
    lags = 10
    train = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    mo1_5m = data.create_dataset(symbols, start=data.today_before(data.days_to_months(1)), end=data.today(), interval='1d')
    
    train_values = models.lstm_prepare_dataset(train).values
    test_values = models.lstm_prepare_dataset(mo1_5m).values
    
    lstm = models.LSTM_Sequential(lags, len(symbols), 10, 100, verbose=True)
    lstm.compile()
    lstm.fit(train_values, 100, 10, './models/lstm.keras', skip_if_exist=True)
    
    return lstm.predict(test_values)

def get_long_term_prediction(symbols):
    lags = 3
    df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    X_train, X_test, y_train, y_test = models.dnn_prepare_dataset(df, lags, "nvda_Price")
    dnn = models.DNN(X_train, X_test, y_train, y_test, verbose=2)
    dnn.compile()
    dnn.fit(100, './models/dnn.keras', skip_if_exist=True)
    
    df = data.create_dataset(symbols, start=data.today_before(data.days_to_years(3)), end=data.today(), interval='1d')
    df = models.dnn_prepare_for_prediction_dataset(df, lags)
    return dnn.predict(df)

#print(get_tomorrow_updown(updown_symbols))
#print(get_long_term_prediction(y3_long_nvda_symbols))