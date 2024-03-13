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
        self.main_layout.addWidget(self.canvas)
        self.setLayout(self.main_layout)

    def update_plot(self, x, y):
        self.canvas.add_data(x, y)
        
    def clear(self):
        self.canvas.clear()
        
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

        self.multiple_y_axis = []
        self.multiple_y_x = []
        self.multiple_y_y = []
        self.sub_y_lines = []
        self.sub_y_linestyles = []
        self.sub_y_colors = []
        
        self.candlesticks = []
        self.x_data = []
        self.y_data = []
        self.sub_x = []
        self.sub_y = []
        self.sub_lines = []
        self.sub_linestyles = []
        self.sub_colors = []
        self.destroy_prev = True
        self.main_line, = self.axes.plot(self.x_data, self.y_data, marker='o')
        
        self.limit_show = 10

    def set_major_formatter(self, dateformat):
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter(dateformat))
    
    def create_new_y_axis(self, linestyle, color):
        self.multiple_y_x.append([])
        self.multiple_y_y.append([])
        self.multiple_y_axis.append(self.axes.twinx())
        self.sub_y_linestyles.append(linestyle)
        self.sub_y_colors.append(color)
        index = len(self.multiple_y_axis) - 1
        line, = self.multiple_y_axis[index].plot(self.multiple_y_x[index], self.multiple_y_y[index], linestyle=linestyle, color=color)
        self.sub_y_lines.append(line)
        return index
    
    def create_sub_line(self, linestyle, color):
        self.sub_x.append([])
        self.sub_y.append([])
        self.sub_linestyles.append(linestyle)
        self.sub_colors.append(color)
        index = len(self.sub_x) - 1
        line, = self.axes.plot(self.sub_x[index], self.sub_y[index], linestyle=linestyle, color=color)
        self.sub_lines.append(line)
        return index
        
    def set_title(self, title):
        self.axes.set_title(title)
    
    def add_data(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        if len(self.x_data) > self.limit_show and self.destroy_prev:
            self.x_data = self.x_data[-self.limit_show:]
            self.y_data = self.y_data[-self.limit_show:]
        self.main_line.set_xdata(self.x_data)
        self.main_line.set_ydata(self.y_data)
        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
    
    def add_sub_line_data(self, index, x, y):
        self.sub_x[index].append(x)
        self.sub_y[index].append(y)
        if len(self.sub_x[index]) > 10 and self.destroy_prev:
            self.sub_x[index] = self.sub_x[index][-10:]
            self.sub_y[index] = self.sub_y[index][-10:]
        self.sub_lines[index].set_xdata(self.sub_x[index])
        self.sub_lines[index].set_ydata(self.sub_y[index])
        
        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
    
    def add_multi_y_line_data(self, index, x, y):
        self.multiple_y_x[index].append(x)
        self.multiple_y_y[index].append(y)
        if len(self.multiple_y_x[index]) > 10 and self.destroy_prev:
            self.multiple_y_x[index] = self.multiple_y_x[index][-10:]
            self.multiple_y_y[index] = self.multiple_y_y[index][-10:]
        self.sub_y_lines[index].set_xdata(self.multiple_y_x[index])
        self.sub_y_lines[index].set_ydata(self.multiple_y_y[index])
        
        self.multiple_y_axis[index].relim()
        self.multiple_y_axis[index].autoscale_view()
        self.draw()
    
    def plot_a_point(self, x, y, marker):
        self.axes.plot(x, y, marker)
        
    def add_text_at_value(self, text, x, y=0, color="black"):
        self.axes.annotate(text, xy=(x, y), xytext=(x, y-3),ha='center', va='top', arrowprops=dict(facecolor=color, shrink=0.05))
    
    def add_axhline_at_value(self, y, color="b", linestyle='--'):
        self.axes.axhline(y=y, color=color, linestyle=linestyle)
    
    def add_candlestick(self, x, prices):
        o = prices[0]
        h = max(prices)
        l = min(prices)
        c = prices[-1]
        candlestick = [self.axes.plot([x[-2], x[-2]], [l, h], color='black', linewidth=1)[0],
                       self.axes.plot([x[-2], x[-1]], [o, o], color='green', linewidth=2)[0],
                       self.axes.plot([x[-2], x[-1]], [c, c], color='red', linewidth=2)[0]]
        self.candlesticks.append(candlestick)
        return len(self.candlesticks) - 1
    def update_candlestick(self, x, prices, index):
        o = prices[0]
        h = max(prices)
        l = min(prices)
        c = prices[-1]
        
        if o == h and h == l and l == c:
            return

        self.candlesticks[index][0].set_data([[x[-2], x[-2]], [l, h]])
        self.candlesticks[index][1].set_data([[x[-2], x[-1]], [o, o]])
        self.candlesticks[index][2].set_data([[x[-2], x[-1]], [c, c]])
        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
        
    def clear(self):
        self.axes.clear()
        self.x_data = []
        self.y_data = []
        self.main_line, = self.axes.plot(self.x_data, self.y_data, '-')
        for i in range(0, len(self.sub_x)):
            self.sub_x[i] = []
            self.sub_y[i] = []
            #line, = self.axes.plot(self.sub_x[i], self.sub_y[i], linestyle=self.sub_linestyles[i], color=self.sub_colors[i])

        for i in range(0, len(self.multiple_y_x)):
            self.multiple_y_x[i] = []
            self.multiple_y_y[i] = []
            self.sub_y_lines[i].set_xdata(self.multiple_y_x[i])
            self.sub_y_lines[i].set_ydata(self.multiple_y_y[i])
            
        self.draw()
        self.sub_lines = []
        self.multiple_y_axis = []
