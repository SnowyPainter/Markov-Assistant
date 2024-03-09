import data
import riskmanager
import tradeinfo
import pandas as pd
import random
import time
from secret import keys
from handlers.koreainvest import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class QTMonitorStockThread(QThread):
    signal = pyqtSignal(tradeinfo.TradeInfo)
    def __init__(self, symbol, broker, env, interval_sec, timezone, stoploss=-0.02, takeprofit=0.04):
        super(QThread, self).__init__()
        self.env = env
        self.broker = broker
        self.symbol = symbol
        self.timezone = timezone
        self.stoploss = stoploss
        self.takeprofit = takeprofit
        #df = pd.DataFrame({env.target:[], 'Datetime':[]})
        #df.set_index('Datetime', inplace=True)
        self.interval_sec = interval_sec
        self.order_book = {}
        self.units = 0
    
    def stop(self):
        #FOR TEST
        #FOR TEST
        #self.monitor.stop_monitor()
        #FOR TEST
        #FOR TEST
        self.quit()
        self.wait(500)
    
    async def run(self):
        timer = time.time()
        self.monitor = riskmanager.MonitorStock(self.env, self.timezone)
        for infos in self.monitor.monitor():
            timer_curr = time.time()
            for info in infos:
                if info.info_type == tradeinfo.InfoType.WAITFORNEWDATA: #1초 마다
                    df = data.create_realtime_dataset([self.symbol])
                    self.monitor.env.append_raw(df)
                    p = df[f"{self.symbol}_Price"].iloc[-1]
                    rand1 = random.randint(1, 50)
                    rand2 = random.randint(1, 50)
                    result = {
                        "apb":[p],
                        "aps":[p],
                        "apb_n":[rand1],
                        "aps_n":[rand2],
                        "s_apb_n":rand1,
                        "s_aps_n":rand2,
                        "predicted_price":p
                    }
                    self.signal.emit(tradeinfo.asking_price_info(result, self.timezone))
                elif timer_curr - timer >= int(self.interval_sec): # this is not a waitingfordata info.
                    self.signal.emit(info)
                    timer = timer_curr
        
class WSMonitorStock():
    def __init__(self, user_info, symbol, broker, env, interval_sec, timezone, stoploss=-0.02, takeprofit=0.04):
        self.env = env
        self.user_info = user_info
        self.broker = broker
        self.symbol = symbol
        self.timezone = timezone
        self.stoploss = stoploss
        self.takeprofit = takeprofit
        self.interval_sec = interval_sec
        self.order_book = {}
        self.units = 0
        self.handler = self._basic
    def _basic(info):
        print(info)
    
    def set_handler(self, func):
        self.handler = func
    
    async def connect(self):
        timer = time.time()
        self.monitor = riskmanager.StatelessStockMonitor(self.env, self.timezone)
        
        #hts_id = self.user_info['htsid']
        #key = self.user_info['apikey']
        #secret = self.user_info['apisecret']
        key = keys.KEY
        secret = keys.APISECRET
        hts_id = keys.HTS_ID
        
        if self.timezone == data.TIMEZONE_KRX:
            actions = [[KOREA_ASKINGPRICE_ID, self.symbol], [KOREA_TRANSCATION_NOTICE_ID, hts_id]]
        elif self.timezone == data.TIMEZONE_NYSE:
            actions = [[NYSE_ASKINGPRICE_ID, get_tr_key_by_symbol(self.symbol)], [NYSE_TRANSCATION_NOTICE_ID, hts_id]]
        approval_key = get_approval(key, secret)
        
        send_data_list = []
        for action in actions:
            send_data_list.append(create_websocket_data(approval_key, action[0], action[1]))
        
        #url = 'ws://ops.koreainvestment.com:21000' # 실전투자계좌
        url = 'ws://ops.koreainvestment.com:31000' # 모의투자계좌
        
        async with websockets.connect(url, ping_interval=None) as websocket:
            for send_data in send_data_list:
                websocket.send(send_data)
                await asyncio.sleep(0.5)
            while True:
                timer_curr = time.time()
                try:
                    recvd = await websocket.recv()
                    result = handle_websocket_data(websocket, recvd)
                    if result["error"] == -1:
                        break
                    if result["type"] == 0: #호가 처리
                        df = data.create_realtime_dataset_by_price(self.symbol, result["predicted_price"], self.timezone)
                        self.monitor.env.append_raw(df)
                        self.handler(tradeinfo.asking_price_info(result, self.timezone))
                        await asyncio.sleep(0.5)
                    elif result["type"] == 1: #체결 처리
                        if result["signed"] == True:
                            self.order_book[result["values"][2]]["signed"] = True
                            self.units = self.order_book[result["values"][2]]["units"]
                            
                        self.handler(tradeinfo.signed_info(result, self.timezone))
                        await asyncio.sleep(0.5)
                    if timer_curr - timer >= int(self.interval_sec):
                        trade_info = self.monitor.get_monitor(self.stoploss, self.takeprofit)
                        trade_type = trade_info.trade_type
                        price = trade_info.price
                        if self.timezone == data.TIMEZONE_KRX:
                            price = get_price_to_asking_price(trade_info.price)
                        current_deposit = get_deposit(get_balance(self.broker))
                        affordable_units = int(current_deposit / price)
                        if trade_type == tradeinfo.TradeType.BUY and affordable_units > 0:
                            result = place_buy_order_limits(self.broker, self.symbol, price, affordable_units)
                            self.order_book[result['output']['ODNO']] = {
                                "signed":False,
                                "units":affordable_units,
                                "price":price
                            }
                        elif trade_type == tradeinfo.TradeType.SELL and self.units > 0:
                            result = place_sell_order_limits(self.broker, self.symbol, price, self.units)
                            self.order_book[result['output']['ODNO']] = {
                                "signed":False,
                                "units":self.units,
                                "price":price
                            }
                        self.handler(trade_info)
                        timer = timer_curr
                except websockets.ConnectionClosed:
                    continue