import mojito
import websockets
import json
import requests
import os
import asyncio
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

key_bytes = 32

# AES256 DECODE
def aes_cbc_base64_dec(key, iv, cipher_text):
    """
    :param key:  str type AES256 secret key value
    :param iv: str type AES256 Initialize Vector
    :param cipher_text: Base64 encoded AES256 str
    :return: Base64-AES256 decodec str
    """
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))

# 웹소켓 접속키 발급
def get_approval(key, secret):
    url = 'https://openapivts.koreainvestment.com:29443' # 모의투자계좌     
    #url = 'https://openapi.koreainvestment.com:9443' # 실전투자계좌
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": key,
            "secretkey": secret}
    PATH = "oauth2/Approval"
    URL = f"{url}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    approval_key = res.json()["approval_key"]
    return approval_key

KOREA_ASKINGPRICE_ID = 'H0STASP0'
KOREA_TRANSCATION_NOTICE_ID = 'H0STCNI0' #모의투자 H0STCNI9, tr_key = HTS ID

NYSE_ASKINGPRICE_ID = 'HDFSASP0'
NYSE_TRANSCATION_NOTICE_ID = 'H0GSCNI0' # tr_key = HTS ID

def get_tr_key_by_symbol(symbol):
    return f"DNAS{symbol}"

def create_websocket_data(approval_key, tr_id, tr_key):
    return '{"header" : {"approval_key": "%s", "custtype" : "P", "tr_type" : "1", "content-type" : "utf-8" }, "body" : { "input":{ "tr_id" : "%s", "tr_key" : "%s"} } }'%(approval_key,tr_id, tr_key)

def handle_websocket_data(websocket, received):
    result = {"error":0}
    
    if received[0] == '0':
        result["type"] = 0
        recvstr = received.split('|')
        trid0 = recvstr[1]
        #국내장 호가 (10호가 제공)
        if trid0 == KOREA_ASKINGPRICE_ID:
            aps, apb, predicted_p = stock_ap_KRX(recvstr[3])
            result["aps"] = aps[0]
            result["aps_n"] = aps[1]
            result["s_aps_n"] = aps[2]
            result["apb"] = apb[0]
            result["apb_n"] = apb[1]
            result["s_apb_n"] = apb[2]
            result["predicted_price"] = predicted_p
        #미국장 호가 (1호가 제공)
        elif trid0 == NYSE_ASKINGPRICE_ID:
            aps, apb = stock_ap_NYSE(recvstr[3])
            result["aps"] = aps[0]
            result["aps_n"] = aps[1]
            result["s_aps_n"] = aps[2]
            result["apb"] = apb[0]
            result["apb_n"] = apb[1]
            result["s_apb_n"] = apb[2]
            result["predicted_price"] = apb[0]
    elif received[0] == '1':
        result["type"] = 1
        recvstr = received.split('|') 
        trid0 = recvstr[1]
        # 주식체결 통보 처리
        if trid0 == KOREA_TRANSCATION_NOTICE_ID or trid0 == "H0STCNI9":  #2모의
           signed, values = stock_signingnotice_KRX(recvstr[3], aes_key, aes_iv)
           result["signed"] = signed
           result["values"] = values
        # 해외주식체결 통보 처리
        elif trid0 == NYSE_TRANSCATION_NOTICE_ID:  
            signed, values = stock_signingnotice_NYSE(recvstr[3], aes_key, aes_iv)
            result["signed"] = signed
            result["values"] = values
    else:
        result["type"] = -1
        jsonObject = json.loads(received)
        trid = jsonObject["header"]["tr_id"]
        if trid != "PINGPONG":
            rt_cd = jsonObject["body"]["rt_cd"]
            if rt_cd == '1':  # 에러일 경우 처리
                if jsonObject["body"]["msg1"] != 'ALREADY IN SUBSCRIBE':
                    print("### ERROR RETURN CODE [ %s ][ %s ] MSG [ %s ]" % (jsonObject["header"]["tr_key"], rt_cd, jsonObject["body"]["msg1"]))
                result["error"] = -1
            elif rt_cd == '0':  # 정상일 경우 처리
                print("### RETURN CODE [ %s ][ %s ] MSG [ %s ]" % (jsonObject["header"]["tr_key"], rt_cd, jsonObject["body"]["msg1"]))
                # 국내주식
                if trid == KOREA_TRANSCATION_NOTICE_ID or trid == "H0STCNI9": 
                    aes_key = jsonObject["body"]["output"]["key"]
                    aes_iv = jsonObject["body"]["output"]["iv"]
                    print("### KRX TRID [%s] KEY[%s] IV[%s]" % (trid, aes_key, aes_iv))
                # 해외주식
                elif trid == NYSE_TRANSCATION_NOTICE_ID: 
                    aes_key = jsonObject["body"]["output"]["key"]
                    aes_iv = jsonObject["body"]["output"]["iv"]
                    print("### NYSE TRID [%s] KEY[%s] IV[%s]" % (trid, aes_key, aes_iv))
        elif trid == "PINGPONG":
            print("### RECV [PINGPONG] [%s]" % (received))
            websocket.pong(received)
            print("### SEND [PINGPONG] [%s]" % (received))
    return result

def stock_ap_KRX(recv):
    """ (매도호가, 호가 당 잔량, 총 호가 잔량), (매수호가, 호가 당 잔량, 총 호가 잔량), 예상 체결가
    stockhoka_KRX(recieved)
    """
    recvvalue = recv.split('^')
    ap_s = recvvalue[3:12+1]
    ap_s_n = recvvalue[23:32+1]
    ap_b = recvvalue[13:22+1] #호가
    ap_b_n = recvvalue[33:42+1] #잔량
    predicted_p = recvvalue[47] #예상 체결가
    sum_ap_s = recvvalue[43] #총 매도호가 잔량
    sum_ap_b = recvvalue[44] #총 매수호가 잔량
    return (ap_s, ap_s_n, sum_ap_s), (ap_b, ap_b_n, sum_ap_b), predicted_p

def stock_ap_NYSE(data):
    """ (매도호가, 호가 당 잔량, 총 호가 잔량), (매수호가, 호가 당 잔량, 총 호가 잔량)
    stockhoka_NYSE(recieved)
    """
    recvvalue = data.split('^')
    return ([recvvalue[12]],[recvvalue[14]],recvvalue[8]), ([recvvalue[11]], [recvvalue[13]], recvvalue[7])

def stock_signingnotice_KRX(data, key, iv):
    ''' 체결여부, 주문번호(2), 주문수량(9), 체결단가(10)
    '''
    # AES256 처리 단계
    aes_dec_str = aes_cbc_base64_dec(key, iv, data)
    pValue = aes_dec_str.split('^')
    if pValue[13] == '2': # 체결통보
        print("#### 국내주식 체결 통보 ####")
        return True, pValue
    else:
        print("#### 국내주식 주문·정정·취소·거부 접수 통보 ####")
        menulist = "고객ID|계좌번호|주문번호|원주문번호|매도매수구분|정정구분|주문종류|주문조건|주식단축종목코드|주문수량|주문가격|주식체결시간|거부여부|체결여부|접수여부|지점번호|주문수량|계좌명|주문종목명|신용구분|신용대출일자|체결종목명40|체결단가"
        menustr1 = menulist.split('|')
        i = 0
        for menu in menustr1:
            print("%s  [%s]" % (menu, pValue[i]))
            i += 1
        return False, pValue
        
def stock_signingnotice_NYSE(data, key, iv):
    ''' 체결여부, 주문번호(2), 주문수량(8), 체결단가(9)
    '''
    menulist = "고객 ID|계좌번호|주문번호|원주문번호|매도매수구분|정정구분|주문종류2|단축종목코드|주문수량|체결단가|체결시간|거부여부|체결여부|접수여부|지점번호|체결수량|계좌명|체결종목명|해외종목구분|담보유형코드|담보대출일자"
    menustr1 = menulist.split('|')

    # AES256 처리 단계
    aes_dec_str = aes_cbc_base64_dec(key, iv, data)
    pValue = aes_dec_str.split('^')

    if pValue[12] == '2': # 체결통보
        print("#### 해외주식 체결 통보 ####")
        return True, pValue
    else:
        print("#### 해외주식 주문·정정·취소·거부 접수 통보 ####")
        i = 0
        for menu in menustr1:
            print("%s  [%s]" % (menu, pValue[i]))
            i += 1
        return False, pValue

def create_broker(api_key, api_secret, acc_no, exchange="나스닥",mock=True):
    broker = mojito.KoreaInvestment(
        api_key=api_key,
        api_secret=api_secret,
        acc_no=acc_no,
        exchange = exchange,
        mock=mock
    )
    return broker

def get_balance(broker):
    return broker.fetch_present_balance()

def get_deposit(balance_output):
    return balance_output['output2'][0]['dcna_tot_amt']

# for domestic market
def get_price_to_asking_price(price):
    if price < 2000:
        return round(price)
    elif price < 5000:
        return round(price / 5) * 5
    elif price < 20000:
        return round(price / 10) * 10
    elif price < 50000:
        return round(price / 50) * 50
    elif price < 200000:
        return round(price / 100) * 100
    elif price < 500000:
        return round(price / 500) * 500
    else:
        return round(price / 1000) * 1000

def place_buy_order_limits(broker, symbol, price, qty):
    return broker.create_limit_buy_order(
        symbol=symbol,
        price=price,
        quantity=qty
    )

def place_sell_order_limits(broker, symbol, price, qty):
    return broker.create_limit_sell_order(
        symbol=symbol,
        price=price,
        quantity=qty
    )

def cancel_order(broker, KRX_FWDG_ORD_ORGNO, ODNO, qty, cancel_all=False):
    return broker.cancel_order(org_no=KRX_FWDG_ORD_ORGNO, order_no=ODNO, quantity=qty, total=cancel_all)