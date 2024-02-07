from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import models, resources.canvas as canvas, data, QTLearn, environment

class TrainStoplossModelWindow(QDialog):
    def __init__(self):
        super(TrainStoplossModelWindow, self).__init__(None)
        self.center()
        self.setWindowTitle("Training New Stop-Loss Model")
        self.initUI()
        self.is_learning = False
    def initUI(self):
        layout = QVBoxLayout()
        val_int = QIntValidator()
        self.symbol_input = QLineEdit(self)
        self.symbol_input.setText("nvda")
        self.lags_input = QLineEdit(self)
        self.lags_input.setText("3")
        self.episodes_input = QLineEdit(self)
        self.episodes_input.setText("300")
        self.price_input = QLineEdit(self)
        self.train_days_input = QLineEdit(self)
        self.train_days_input.setText("30")
        self.train_interval_input = QLineEdit(self)
        self.train_interval_input.setText("5m")
        
        symbol_label = QLabel('Symbol:', self)
        lags_label = QLabel('Lags:', self)
        episodes_label = QLabel('Episodes:', self)
        price_label = QLabel('Price:', self)
        train_days_label = QLabel('Train Days:', self)
        train_interval_label = QLabel("Train Days Interval", self)
        self.learn_button = QPushButton('Learn', self)
        
        form_layout = QFormLayout()
        form_layout.addRow(symbol_label, self.symbol_input)
        form_layout.addRow(lags_label, self.lags_input)
        form_layout.addRow(episodes_label, self.episodes_input)
        form_layout.addRow(price_label, self.price_input)
        form_layout.addRow(train_days_label, self.train_days_input)
        form_layout.addRow(train_interval_label, self.train_interval_input)

        self.lags_input.setValidator(val_int)
        self.episodes_input.setValidator(val_int)
        self.train_days_input.setValidator(val_int)
        self.learn_button.clicked.connect(self.learn_clicked)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.learn_button)
        self.setLayout(layout)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def learn_clicked(self):
        if self.is_learning:
            return
        
        self.fname = QFileDialog.getSaveFileName(self, '.Keras save file', "./stop_loss.keras", "Keras (*.keras)")[0]
        if self.fname == "":
            return
        lags = int(self.lags_input.text())
        episodes = int(self.episodes_input.text())
        symbol = self.symbol_input.text().strip()
        price = float(self.price_input.text().strip())
        days = int(self.train_days_input.text().strip())
        interval = self.train_interval_input.text().strip()
        target = symbol+'_Price'
        df = data.create_dataset([symbol], start=data.today_before(days), end=data.today(), interval=interval)
        env = environment.StoplossEnv(price, df, target, lags)
        models.set_seeds(100)
        self.is_learning = True
        self.agent = models.QLearningAgent(env, models.build_model)
        self.learning_thread = QTLearn.LearningThread(self.agent, episodes)
        self.learning_thread.update_signal.connect(self.update_results)
        self.learning_thread.start()

    def update_results(self, episode_data):
        if episode_data.episode == -1: #end
            self.learn_button.setText("Learn")
            self.is_learning = False
            self.agent.model.save(self.fname)
            QMessageBox.information(self, "Learning finished!", "Your stoploss model finished learning.")
        else:
            self.learn_button.setText(f"Learning {episode_data.episode}")