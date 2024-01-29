from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime

class RealTimePlot(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.canvas = PlotCanvas(self, width=5, height=4)
        self.canvas.set_major_formatter('%H:%M:%S')
        self.main_layout.addWidget(self.canvas)
        self.setLayout(self.main_layout)

    def update_plot(self, x, y):
        self.canvas.add_data(x, y)
        
    def clear(self):
        self.canvas.clear()
        self.canvas.set_major_formatter('%H:%M:%S')
        
class StaticPlot(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Minimum, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.plot_static_data([], [])

    def plot_static_data(self, x, y, xlabel="", ylabel="", title=""):
        self.ax.plot(x, y)
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.draw()

    def clear_plot(self):
        self.ax.clear()
        self.plot_static_data([], [])
        
class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Minimum, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.x_data = []
        self.y_data = []

        self.line, = self.axes.plot(self.x_data, self.y_data, marker='o')
        
    def set_major_formatter(self, dateformat):
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter(dateformat))
        
    def add_data(self, x, y):
        #x = mdates.date2num(datetime.datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S'))
        self.x_data.append(x)
        self.y_data.append(y)
        if len(self.x_data) > 10:
            self.x_data = self.x_data[-10:]
            self.y_data = self.y_data[-10:]
        self.line.set_xdata(self.x_data)
        self.line.set_ydata(self.y_data)
        self.axes.relim()
        self.axes.autoscale_view()

        self.draw()

    def clear(self):
        self.axes.clear()
        self.x_data = []
        self.y_data = []
        self.line, = self.axes.plot(self.x_data, self.y_data, marker='o')
        self.draw()
        
