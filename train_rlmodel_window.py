from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import models, resources.canvas as canvas

class TrainRLModelWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1024, 600)
        self.center()
        self.setWindowTitle("Training New RL Model for Backtesting")
    
    def initUI(self):
        layout = QVBoxLayout()
        self.l1 = QLabel("hello", self)
        layout.addWidget(self.l1)
        self.setLayout(layout)
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())