import numpy as np
from scipy.optimize import minimize
import json
'''
def load_portfolio():
    try:
        with open("portfolio.json", 'r') as file:
            portfolio = json.load(file)
    except FileNotFoundError:
        portfolio = {}
    return portfolio

portfolio = load_portfolio()
'''
def get_names(portfolio):
    return [stock for stock in portfolio.keys()]
def get_today_tomorrow_prices(portfolio):
    dnn_predictions = []
    lstm_predictions = []
    for stock in portfolio.values():
        if "dnn" in stock and "result" in stock["dnn"]:
            dnn_predictions.append(stock["dnn"]['result']['prediction'])
        if "lstm" in stock and "result" in stock["lstm"]:
            lstm_predictions.append(stock["lstm"]['result']['prediction'])
    today_price = np.array(dnn_predictions)
    tomorrow_price = np.empty(shape=[len(dnn_predictions)])
    for i in range(len(lstm_predictions)):
        ret = 0.03 if lstm_predictions[i] >= 0 else -0.03
        tomorrow_price[i] = dnn_predictions[i] * (1 + ret)
    return today_price, tomorrow_price

def calculate_portfolio_return(weights, returns):
    portfolio_return = np.sum(weights * returns)
    return portfolio_return

def calculate_portfolio_volatility(weights, cov_matrix):
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return portfolio_volatility

def calculate_negative_sharpe_ratio(weights, returns, cov_matrix, risk_free_rate):
    portfolio_return = calculate_portfolio_return(weights, returns)
    portfolio_volatility = calculate_portfolio_volatility(weights, cov_matrix)
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
    return -sharpe_ratio

def optimize_portfolio(returns, cov_matrix, risk_free_rate):
    num_assets = len(returns)
    initial_weights = np.array(num_assets * [1. / num_assets])
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for asset in range(num_assets))

    result = minimize(calculate_negative_sharpe_ratio, initial_weights,
                      args=(returns, cov_matrix, risk_free_rate), method='SLSQP',
                      bounds=bounds, constraints=constraints)

    return result.x

def optimal_portfolio_weights(today_price, tomorrow_price, risk_free_rate = 0.02):
    returns = (tomorrow_price - today_price) / today_price
    cov_matrix = np.cov(returns)
    return optimize_portfolio(returns, cov_matrix, risk_free_rate)

def portfolio_volatility(phi, today_price, tomorrow_price):
    returns = (tomorrow_price - today_price) / today_price
    cov_matrix = np.cov(returns)
    return np.sqrt(np.dot(phi, np.dot(cov_matrix, phi)))
