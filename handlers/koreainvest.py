import mojito
import websockets
import json
import requests
import os
import time
import data

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

KOREA_DEALPRICE_ID = 'H0STCNT0'
KOREA_ASKINGPRICE_ID = 'H0STASP0'
KOREA_TRANSCATION_NOTICE_ID = 'H0STCNI0' #모의투자 H0STCNI9, tr_key = HTS ID

NYSE_DEALPRICE_ID = 'HDFSCNT0'
NYSE_ASKINGPRICE_ID = 'HDFSASP0'
NYSE_TRANSCATION_NOTICE_ID = 'H0GSCNI0' # tr_key = HTS ID

HANDLE_ASKINGPRICE = 0
HANDLE_DEALPRICE = 1
HANDLE_TRNSCNOTICE = 2

def get_tr_key_by_symbol(symbol):
    return f"DNAS{symbol}"

def handle_ws_data(ws, data):
    result = {"error":0}
    if data[0] == '0':
        recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split
        trid0 = recvstr[1]
        #국내장 호가 (10호가 제공)
        if trid0 == KOREA_ASKINGPRICE_ID:
            result["type"] = HANDLE_ASKINGPRICE
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
            result["type"] = HANDLE_ASKINGPRICE
            aps, apb = stock_ap_NYSE(recvstr[3])
            result["aps"] = aps[0]
            result["aps_n"] = aps[1]
            result["s_aps_n"] = aps[2]
            result["apb"] = apb[0]
            result["apb_n"] = apb[1]
            result["s_apb_n"] = apb[2]
            result["predicted_price"] = apb[0][0]
        elif trid0 == KOREA_DEALPRICE_ID: 
            result["type"] = HANDLE_DEALPRICE
            data_cnt = int(recvstr[2])  
            info = stock_deal_KRX(data_cnt, recvstr[3])
            result["stock"] = info[0]
            result["current_price"] = info[2]
        elif trid0 == NYSE_DEALPRICE_ID: 
            result["type"] = HANDLE_DEALPRICE
            data_cnt = int(recvstr[2]) 
            info = stock_deal_NYSE(data_cnt, recvstr[3])
            result["stock"] = info[0]
            result["current_price"] = info[11]
    elif data[0] == '1':
        recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split
        trid0 = recvstr[1]
        # 주식체결 통보 처리
        if trid0 == KOREA_TRANSCATION_NOTICE_ID or trid0 == "H0STCNI9":  #2모의
            result["type"] = HANDLE_TRNSCNOTICE
            signed, values = stock_signingnotice_KRX(recvstr[3], aes_key, aes_iv)
            result["signed"] = signed
            result["values"] = values
        # 해외주식체결 통보 처리
        elif trid0 == NYSE_TRANSCATION_NOTICE_ID:  
            result["type"] = HANDLE_TRNSCNOTICE
            signed, values = stock_signingnotice_NYSE(recvstr[3], aes_key, aes_iv)
            result["signed"] = signed
            result["values"] = values
    else:
        jsonObject = json.loads(data)
        trid = jsonObject["header"]["tr_id"]
        result["type"] = -1
        if trid != "PINGPONG":
            rt_cd = jsonObject["body"]["rt_cd"]
            if rt_cd == '1':  # 에러일 경우 처리
                if jsonObject["body"]["msg1"] != 'ALREADY IN SUBSCRIBE':
                    print("### ERROR RETURN CODE [ %s ][ %s ] MSG [ %s ]" % (jsonObject["header"]["tr_key"], rt_cd, jsonObject["body"]["msg1"]))
                return {'error':-1}
            elif rt_cd == '0':  # 정상일 경우 처리
                # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                if trid == "H0GSCNI0": # 해외주식
                    aes_key = jsonObject["body"]["output"]["key"]
                    aes_iv = jsonObject["body"]["output"]["iv"]
        elif trid == "PINGPONG":
            ws.pong(data)
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

def stock_deal_KRX(data_cnt, data):
    #menulist = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"
    pValue = data.split('^')
    return pValue

def stock_deal_NYSE(data_cnt, data):
    #menulist = "실시간종목코드|종목코드|수수점자리수|현지영업일자|현지일자|현지시간|한국일자|한국시간|시가|고가|저가|현재가|대비구분|전일대비|등락율|매수호가|매도호가|매수잔량|매도잔량|체결량|거래량|거래대금|매도체결량|매수체결량|체결강도|시장구분"
    pValue = data.split('^')
    return pValue

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
    return broker.fetch_balance()

def get_deposit(balance_output, timezone):
    dnca_tot_amt = 0
    if timezone == data.TIMEZONE_KRX:
        dnca_tot_amt = float(balance_output['output2'][0]["dnca_tot_amt"])
    elif "dnca_tot_amt" in balance_output['output2']:
        dnca_tot_amt = float(balance_output['output2']["dnca_tot_amt"])
    return dnca_tot_amt

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