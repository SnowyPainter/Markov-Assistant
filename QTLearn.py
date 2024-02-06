from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import *
import models

class LearningThread(QThread):
    update_signal = pyqtSignal(models.EpisodeData)  # Signal to update GUI with results

    def __init__(self, agent, episodes):
        super().__init__()
        self.agent = agent
        self.episodes = episodes

    def run(self):
        for d in self.agent.learn(self.episodes, 128):
            self.update_signal.emit(d)
        self.update_signal.emit(models.EpisodeData(episode=-1))