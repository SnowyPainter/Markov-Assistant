from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import QTMonitorStock
import models, resources.canvas as canvas

class MonitorStockWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Stock")
        self.initUI()
        
    def initUI(self):
        base_layout = QVBoxLayout()
        self.monitor_canvas = canvas.RealTimePlot()
        self.monitor_canvas.canvas.set_major_formatter("%H:%M:%S")
        self.run_btn = QPushButton("Run", self)
        self.stop_btn = QPushButton("Stop", self)
        
        controls_layout = QVBoxLayout()
        agent_info_layout = QHBoxLayout()
        runstop_layout = QHBoxLayout()
        
        controls_layout.addWidget(self.monitor_canvas)
        runstop_layout.addWidget(self.run_btn)
        runstop_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(agent_info_layout)
        controls_layout.addLayout(runstop_layout)
        base_layout.addLayout(controls_layout)
        
        self.run_btn.clicked.connect(self.run_btn_clicked)
        self.stop_btn.clicked.connect(self.stop_btn_clicked)
        
        self.setLayout(base_layout)
    
    def run_btn_clicked(self):
        self.montior_thread = QTMonitorStock.QTMonitorStockThread('nvda', models.load('./models/agent.keras'), 3, 1, 0.025, 0.02, 0.04, True)
        self.montior_thread.signal.connect(self.montiro_thread_result_handler)
        self.montior_thread.start()
        
    def stop_btn_clicked(self):
        self.montior_thread.stop()
        
    def montiro_thread_result_handler(self, info):
        print(info.info_type)