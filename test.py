import data
import models
import matplotlib.pyplot as plt

y3_long_nvda_symbols = ["nvda", "^vix", "tqqq", "xsd", "eurusd=x"]
mo1_5m_long_nvda_tickers = ["nvda", "amd", "intc"]

def get_tomorrow_updown():
    lags = 3
    mo1_5m = data.create_dataset(mo1_5m_long_nvda_tickers, start=data.today_before(data.days_to_months(1)), end=data.today(), interval='5m')
    mo1_r, r_cols = data.add_rate_of_return(mo1_5m)
    r = mo1_r[r_cols].values
    lstm = models.LSTM_Sequential(lags, len(mo1_5m_long_nvda_tickers), 10, 100, verbose=True)
    lstm.compile()
    lstm.fit(r, 100, 10, './models/lstm.h5', skip_if_exist=True)
    return "up" if lstm.predict(r)[-1] > 0 else "down"

print(get_tomorrow_updown())