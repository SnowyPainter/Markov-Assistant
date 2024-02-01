from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys, os, json
import handlers.logger as logger

class PlaceOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
    def initUI(self, stock):
        self.setWindowTitle("Place Order Window")
        self.stock = stock
        layout = QVBoxLayout()
        self.quantity_label = QLabel("Units:")
        self.quantity_input = QLineEdit(self)
        self.price_label = QLabel("Price:")
        self.price_input = QLineEdit(self)
        self.buy_button = QPushButton("Buy", self)
        self.buy_button.clicked.connect(self.on_buy_button_clicked)
        self.sell_button = QPushButton("Sell", self)
        self.sell_button.clicked.connect(self.on_sell_button_clicked)
        layout.addWidget(self.quantity_label)
        layout.addWidget(self.quantity_input)
        layout.addWidget(self.price_label)
        layout.addWidget(self.price_input)
        layout.addWidget(self.buy_button)
        layout.addWidget(self.sell_button)
        self.setLayout(layout)
    def on_buy_button_clicked(self):
        self.log_trade("buy")

    def on_sell_button_clicked(self):
        self.log_trade("sell")
    
    def log_trade(self, action):
        units = self.quantity_input.text()
        price = self.price_input.text()
        logger.log_trade(self.stock, action, units, price)