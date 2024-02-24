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
        state_size = self.env.trade_agent.state_size
        n_features = self.env.trade_agent.n_features
        for e in range(self.episodes):
            sideway_state, trade_state = self.env.reset()
            sideway_state = np.reshape(sideway_state, [1,  state_size, n_features])
            trade_state = np.reshape(trade_state, [1, state_size, n_features])
            
            for _ in range(10000):
                sideway_act = self.env.sideway_agent.act(sideway_state)
                trade_act = self.env.trade_agent.act(trade_state)
                next_sideway_state, next_trade_state, sideway_reward, trade_reward, done, info = self.env.step(sideway_act, trade_act)
                
                next_sideway_state = np.reshape(next_sideway_state, [1, state_size, n_features])
                next_trade_state = np.reshape(next_trade_state, [1, state_size, n_features])
                
                self.env.sideway_agent.remember(sideway_state, sideway_act, sideway_reward, next_sideway_state, done)
                self.env.trade_agent.remember(trade_state, trade_act, trade_reward, next_trade_state, done)
                
                sideway_state = next_sideway_state
                trade_state = next_trade_state
                
                if done:
                    self.update_signal.emit(models.EpisodeData(e+1, performance=self.env.performance))
                    break
                
            if len(self.env.sideway_agent.memory) > self.batch_size:
                self.env.sideway_agent.replay(self.batch_size)
            if len(self.env.trade_agent.memory) > self.batch_size:
                self.env.trade_agent.replay(self.batch_size)
        self.update_signal.emit(models.EpisodeData(episode=-1))