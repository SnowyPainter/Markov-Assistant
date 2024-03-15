from data import *
import riskmanager
import tradeinfo
import pandas as pd
import random
import time
import websocket
from secret import keys
import logger
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
                    df = create_realtime_dataset([self.symbol])
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
        
class WSMonitorStock(QThread):
    def __init__(self, user_info, symbol, broker, env, interval_sec, timezone, stoploss=-0.02, takeprofit=0.04):
        super(QThread, self).__init__()
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
        
        self.TEST_DEPOSIT = 10000

    signal = pyqtSignal(tradeinfo.TradeInfo)
    def stop(self):
        self.ws.close()
        self.running = False
        
    def run(self):
        
        self.running = True
        timer = time.time()
        self.monitor = riskmanager.StatelessStockMonitor(self.env, self.timezone)
        
        hts_id = self.user_info['htsid']
        key = self.user_info['apikey']
        secret = self.user_info['apisecret']
        #key = keys.KEY
        #secret = keys.APISECRET
        #hts_id = keys.HTS_ID
        g_approval_key = get_approval(key, secret)
        url = 'ws://ops.koreainvestment.com:31000' # 모의투자계좌
        #url = 'ws://ops.koreainvestment.com:21000' # 실전투자계좌

        
        if self.timezone == TIMEZONE_KRX:
            code_list = [['1', KOREA_ASKINGPRICE_ID, self.symbol.split('.')[0]], ['1', KOREA_DEALPRICE_ID, self.symbol.split('.')[0]],['1', KOREA_TRANSCATION_NOTICE_ID, hts_id]]
        else:
            symbol_tr_key = get_tr_key_by_symbol(self.symbol)
            code_list = [['1', NYSE_ASKINGPRICE_ID, symbol_tr_key], ['1', NYSE_DEALPRICE_ID, symbol_tr_key],['1', NYSE_TRANSCATION_NOTICE_ID, hts_id]]
        senddata_list=[]
        for i,j,k in code_list:
            temp = '{"header":{"approval_key": "%s","custtype":"P","tr_type":"%s","content-type":"utf-8"},"body":{"input":{"tr_id":"%s","tr_key":"%s"}}}'%(g_approval_key,i,j,k)
            senddata_list.append(temp)

        self.ws = websocket.create_connection(url)
        
        for senddata in senddata_list:
            self.ws.send(senddata)
            self.msleep(int(500))
        while self.running:
            timer_curr = time.time()
            try:
                data = self.ws.recv()
                self.msleep(int(500))
                result = handle_ws_data(self.ws, data)
                if result["error"] == -1:
                    break
                if result["type"] == HANDLE_ASKINGPRICE:
                    self.signal.emit(tradeinfo.asking_price_info(result, self.timezone))
                    self.msleep(int(500))
                elif result["type"] == HANDLE_DEALPRICE:
                    self.signal.emit(tradeinfo.deal_price_info(result, self.timezone))
                    df = create_realtime_dataset_by_price(self.symbol, float(result["current_price"]), self.timezone)
                    self.monitor.env.append_raw(df)
                    self.msleep(int(500))
                elif result["type"] == HANDLE_TRNSCNOTICE:
                    if result["signed"] == True:
                        self.order_book[result["values"][2]]["signed"] = True
                        self.units = self.order_book[result["values"][2]]["units"]
                    
                    self.signal.emit(tradeinfo.signed_info(result, self.timezone))
                    self.msleep(int(500))
                
                if timer_curr - timer >= int(self.interval_sec):
                    trade_info = self.monitor.get_monitor(self.stoploss, self.takeprofit)
                    trade_type = trade_info.trade_type
                    price = trade_info.price
                    if self.timezone == TIMEZONE_KRX:
                        price = get_price_to_asking_price(trade_info.price)
                    #current_deposit = get_deposit(get_balance(self.broker), self.timezone)
                    current_deposit = self.TEST_DEPOSIT
                    if current_deposit == 0.0:
                        continue
                    affordable_units = int(current_deposit / price)
                    if trade_type == tradeinfo.TradeType.BUY and affordable_units > 0:
                        #result = place_buy_order_limits(self.broker, self.symbol, price, affordable_units)
                        #self.order_book[result['output']['ODNO']] = {
                        #    "signed":False,
                        #    "units":affordable_units,
                        #    "price":price
                        #}
                        self.units += affordable_units
                        self.TEST_DEPOSIT -= affordable_units * price
                        logger.log_trade(self.symbol, tradeinfo.TradeType.BUY, affordable_units, price, path="./log/log my NVDA trade 001.json")
                    elif trade_type == tradeinfo.TradeType.SELL and self.units > 0:
                        #result = place_sell_order_limits(self.broker, self.symbol, price, self.units)
                        #self.order_book[result['output']['ODNO']] = {
                        #    "signed":False,
                        #    "units":self.units,
                        #    "price":price
                        #}
                        self.TEST_DEPOSIT += self.units * price
                        logger.log_trade(self.symbol, tradeinfo.TradeType.BUY, self.units, price, path="./log/log my NVDA trade 001.json")
                        self.units = 0
                    self.signal.emit(trade_info)
                    timer = timer_curr
                
            except websockets.ConnectionClosed:
                continue