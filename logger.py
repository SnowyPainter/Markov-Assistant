from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys, os, json

def calculate_trade(stock, path="./log/orders.json"):
    logs = read_all_trades(path=path)
    if logs == []:
        QMessageBox.information(None, "Error", "There's no trades you did.")
        return
    logs = [item for item in logs if item.get("stock") == stock]
    profit = 0
    for item in logs:
        action = item.get("action")
        units = float(item.get('units'))
        price = float(item.get("price"))
        if action == "buy":
            profit -= (units * price)
        if action == "sell":
            profit += ((units * price) - ((units * price) * (0.0025)))
    return profit

def log_trade(stock, action, units, price, path="./log/orders.json"):
    if not units or not price:
        QMessageBox.information(None, "Error", "Please put informations about stock.")
        return
    if not os.path.exists("./log"):
        os.makedirs("./log")
    try:
        with open(path, "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    trade_log = {"action": action, "stock":stock,"units": units, "price": round(float(price), 2)}
    logs.append(trade_log)
    with open(path, "w") as f:
        json.dump(logs, f, indent=2)

def read_all_trades(path="./log/orders.json"):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            logs = json.load(f)
    except:
        return []
    return logs

def log_backtest(net_wealth, date, infotype=5, position=3, tradetype=3, p=0, units=0, price=0):
    if not os.path.exists("./log"):
        os.makedirs("./log")
    try:
        with open("./log/backtest.json", "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    backtest_log = {"net_wealth": round(net_wealth, 4), "date":date,"infotype":infotype, "position":position, "tradetype":tradetype, "p":p, "units":units, "price":round(price, 2)}
    logs.append(backtest_log)
    with open("./log/backtest.json", "w") as f:
        json.dump(logs, f, indent=2)
        
def log_monitor(date, price, tradetype):
    if not os.path.exists("./log"):
        os.makedirs("./log")
    try:
        with open("./log/monitor.json", "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    monitor_log = {"date": date, "price":price, "tradetype":tradetype}
    logs.append(monitor_log)
    with open("./log/monitor.json", "w") as f:
        json.dump(logs, f, indent=2)