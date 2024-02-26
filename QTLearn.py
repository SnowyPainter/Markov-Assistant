from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import *
import numpy as np
import models, environment

class LearningThread(QThread):
    update_signal = pyqtSignal(models.EpisodeData)  # Signal to update GUI with results

    def __init__(self, agent, episodes):
        super().__init__()
        self.agent = agent
        self.episodes = episodes

    def run(self):
        for d in self.agent.learn(episodes=self.episodes):
            self.update_signal.emit(d)
        self.update_signal.emit(models.EpisodeData(episode=-1))
        
class StockMarketLearningThread(QThread):
    update_signal = pyqtSignal(models.EpisodeData)  # Signal to update GUI with results

    def __init__(self, env, episodes, batch_size):
        super().__init__()
        self.env = env
        self.episodes = episodes
        self.batch_size = batch_size

    def run(self):
        state_size = self.env.agents[environment.Agent.TRADE].state_size
        n_features = self.env.agents[environment.Agent.TRADE].n_features
        for e in range(self.episodes):
            states = self.env.reset()
            for i in range(0, len(states)):
                states[i] = np.reshape(states[0], [1,  state_size, n_features])
            
            for _ in range(10000):
                acts = []
                for i in range(0, len(self.env.agents)):
                    acts.append(self.env.agents[i].act(states[i]))
                next_states, rewards, done, info = self.env.step(acts)
                for i in range(0, len(next_states)):
                    next_states[i] = np.reshape(next_states[i], [1, state_size, n_features])
                    self.env.agents[i].remember(states[i], acts[i], rewards[i], next_states[i], done)
                    states[i] = next_states[i]
                
                if done:
                    self.update_signal.emit(models.EpisodeData(e+1, performance=self.env.performance))
                    break
            
            for i in range(0, len(self.env.agents)):
                if len(self.env.agents[i].memory) > self.batch_size:
                    self.env.agents[i].replay(self.batch_size)
        self.update_signal.emit(models.EpisodeData(episode=-1))