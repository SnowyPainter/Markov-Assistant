from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import models, resources.canvas as canvas, data, QTLearn, environment
import os

class TrainRLModelWindow(QDialog):
    def __init__(self):
        super(TrainRLModelWindow, self).__init__(None)
        self.resize(1024, 600)
        self.center()
        self.setWindowTitle("Training New RL Model for Backtesting")
        self.is_learning = False
    def initUI(self, symbol="nvda"):
        layout = QVBoxLayout()
        val_int = QIntValidator()
        self.symbol_input = QLineEdit(self)
        self.symbol_input.setText(symbol)
        self.lags_input = QLineEdit(self)
        self.lags_input.setText("3")
        self.episodes_input = QLineEdit(self)
        self.episodes_input.setText("30")
        self.train_days_input = QLineEdit(self)
        self.train_days_input.setText("50")
        self.train_interval_input = QLineEdit(self)
        self.train_interval_input.setText("5m")
        
        symbol_label = QLabel('Symbol:', self)
        lags_label = QLabel('Lags:', self)
        episodes_label = QLabel('Episodes:', self)
        train_days_label = QLabel('Train Days:', self)
        train_interval_label = QLabel("Train Days Interval", self)
        self.learn_button = QPushButton('Learn', self)
        
        form_layout = QFormLayout()
        form_layout.addRow(symbol_label, self.symbol_input)
        form_layout.addRow(lags_label, self.lags_input)
        form_layout.addRow(episodes_label, self.episodes_input)
        form_layout.addRow(train_days_label, self.train_days_input)
        form_layout.addRow(train_interval_label, self.train_interval_input)
        
        self.performance_plot = canvas.RealTimePlot()
        self.performance_plot.canvas.set_title("Total Reward chart")
        
        self.plot_layout = QHBoxLayout()
        self.plot_layout.addWidget(self.performance_plot)
        
        self.lags_input.setValidator(val_int)
        self.episodes_input.setValidator(val_int)
        self.train_days_input.setValidator(val_int)
        self.learn_button.clicked.connect(self.learn_clicked)
        
        layout.addLayout(form_layout)
        layout.addLayout(self.plot_layout)
        layout.addWidget(self.learn_button, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def learn_clicked(self):
        if self.is_learning:
            return
        symbol = self.symbol_input.text().strip()
        folder_path = QFileDialog.getExistingDirectory(None, "Folder For New Model", "", QFileDialog.ShowDirsOnly)
        if folder_path:
            try:
                new_dir_path = os.path.join(folder_path, f"{symbol}")
                if os.path.exists(new_dir_path):
                    QMessageBox.information(self, "Existing Folder", f"{symbol} RL model folder is existing.")
                    return
                os.makedirs(new_dir_path)
                self.model_paths = environment.get_model_paths(new_dir_path)
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error while system create a directory: {str(e)}", QMessageBox.Ok)
        else:
            return
        lags = int(self.lags_input.text())
        episodes = int(self.episodes_input.text())
        days = int(self.train_days_input.text().strip())
        interval = self.train_interval_input.text().strip()
        target = symbol+'_Price'
        features = data.stock_data_columns()
        features.append(target)
        df = data.create_dataset([symbol], start=data.today_before(days), end=data.today(), interval=interval)
        sideway_agent = models.DQNMulti(lags, 2, len(features)) # 0:hold, 1:trade
        rsi_trade_agent = models.DQNMulti(lags, 2, len(features)) # 0:buy 1:sell
        sma_trade_agent = models.DQNMulti(lags, 2, len(features)) # 0:buy 1:sell
        agents = [sideway_agent, rsi_trade_agent, sma_trade_agent]
        self.stock_market_env = environment.StockMarketEnvironment(agents, df, target, lags=lags)
        
        models.set_seeds(100)
        self.is_learning = True
        self.learning_thread = QTLearn.StockMarketLearningThread(self.stock_market_env, episodes, 64)
        self.learning_thread.update_signal.connect(self.update_results)
        self.learning_thread.start()

    def update_results(self, episode_data):
        if episode_data.episode == -1: #end
            self.learn_button.setText("Learn")
            self.is_learning = False
            for i in range(0, len(self.stock_market_env.agents)):
                self.stock_market_env.agents[i].model.save(self.model_paths[i])
                
            QMessageBox.information(self, "Learning finished!", "Your model finished learning.")
        else:
            self.learn_button.setText(f"Learning {episode_data.episode}")     
            self.performance_plot.update_plot(episode_data.episode, episode_data.treward)