from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import models, resources.canvas as canvas

class TrainResultWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.loss_plot = canvas.StaticPlot()
        self.loss_label = QLabel("")
        self.rating_label = QLabel("")
        
        layout.addWidget(self.loss_plot)
        layout.addWidget(self.loss_label)
        layout.addWidget(self.rating_label)
        
        self.setLayout(layout)
    def initUI(self, title, train_result):
        self.setWindowTitle(title)
        self.loss_plot.clear_plot()
        loss = train_result.history['loss']
        self.loss_plot.plot_static_data(range(0, len(loss)), loss, ylabel="loss", title="Training Loss")
        self.loss_label.setText(str(loss[-1]))
        rating = ""
        loss = loss[-1]
        if loss > 1.3:
            rating = "Seriously bad"
        elif loss > 0.9:
            rating = "Bad"
        elif loss > 0.65:
            rating = "Request touch"
        elif loss > 0.3:
            rating = "Normal"
        elif loss > 0.2:
            rating = "Good"
        elif loss > 0.05:
            rating = "Excellent"
        else:
            rating = "Overfitting"
        self.rating_label.setText(rating)