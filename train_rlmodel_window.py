from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import models, resources.canvas as canvas, data, QTLearn, environment

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
        self.performance_plot.canvas.set_title("Performance chart")
        
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
        
        self.fname = QFileDialog.getSaveFileName(self, '.Keras save file', "./my_model.keras", "Keras (*.keras)")[0]
        if self.fname == "":
            return
        
        lags = int(self.lags_input.text())
        episodes = int(self.episodes_input.text())
        symbol = self.symbol_input.text().strip()
        days = int(self.train_days_input.text().strip())
        interval = self.train_interval_input.text().strip()
        target = symbol+'_Price'
        features = [target, 'r', 's', 'm', 'v']
        
        df = data.create_dataset([symbol], start=data.today_before(days), end=data.today(), interval=interval)
        learn_env = environment.FinanceEnv(df, target, features, window=20, lags=lags, data_preparing_func=data.prepare_RSMV_data, min_performance=0.9)
        models.set_seeds(100)
        self.is_learning = True
        self.agent = models.SARSA(learn_env)
        self.learning_thread = QTLearn.LearningThread(self.agent, episodes)
        self.learning_thread.update_signal.connect(self.update_results)
        self.learning_thread.start()

    def update_results(self, episode_data):
        if episode_data.episode == -1: #end
            self.learn_button.setText("Learn")
            self.is_learning = False
            self.agent.model.save(self.fname)
            QMessageBox.information(self, "Learning finished!", "Your model finished learning.")
        else:
            self.learn_button.setText(f"Learning {episode_data.episode}")     
            self.performance_plot.update_plot(episode_data.episode, episode_data.performance)