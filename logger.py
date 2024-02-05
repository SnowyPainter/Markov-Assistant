from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys, os, json

def log_trade(stock, action, units, price):
    if not units or not price:
        QMessageBox.information(None, "Error", "Please put informations about stock.")
        return
    if not os.path.exists("./log"):
        os.makedirs("./log")
    try:
        with open("./log/orders.json", "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    trade_log = {"action": action, "stock":stock,"units": units, "price": round(float(price), 2)}
    logs.append(trade_log)
    with open("./log/orders.json", "w") as f:
        json.dump(logs, f, indent=2)

def read_all_trades():
    if not os.path.exists("./log/orders.json"):
        return []
    try:
        with open("./log/orders.json", "r") as f:
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