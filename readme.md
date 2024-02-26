# Markov Assistant

## Supports
* Short-Term stock price's up & down prediction
* Long-Term stock price's movement
* Trading Bot Backtesting
* Stop Loss Monitoring

## Program Consists of:

### Main Window
![MainWindow](./readme_resources/main_window.png)

#### Portfolio
Register your interested stock, and manage with data that program provides.

#### Short-Term Stock Price Up & Down
Using Densed RNN algorithms, based on log-return profit, you can seize tomorrow stock prices' up & down.

#### Long-Term Stock Price Flow Prediction
Using DNN algorithm, its flow chart infected many other indexes, stocks.  
You can thrive you portfolio more profitable and be acknowledged about prices a few months later.

#### Backtesting Your own algorithm
Your main trading algorithm consisted of different agent that works interdependent. Furthermore backtest your RL-model with specific days, you can measure your model works well.

### Train New Backtest Model
![TrainNewRLWindow](./readme_resources/newrlmodel_window.png)

* Symbol : what stock you want to train.
* Lags : previous days referenced by the model.
* Episodes : model's training cycle.
* Train Days : previous days that model will train.
* Interval : update interval of stock price.

### Train New Stop loss Model
![TrainStoplossModelWindow](./readme_resources/new_stoploss_model_window.png)

### Trade Window
![TradeWindow](./readme_resources/trade_window.png)

* Holding : Your one of your agent is for prevent trading while sideway market.
* Trading : Other agents, interact each other, trade a stock.

### Installing Environment
* CUDA: 12.4
* Python: 3.9.12
* Keras: 2.15.0
* numpy: 1.26.3
* pandas: 1.4.2
* PyQt5: 5.15.10
* pyqtgraph: 0.13.3
* tensorflow: 2.15.0
* yfinance: 0.2.36