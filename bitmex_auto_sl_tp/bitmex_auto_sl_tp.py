import requests
import hmac
import hashlib
import json
import time
import urllib
from threading import Thread

BASE_URL = 'https://www.bitmex.com/api/v1/'

API_KEY = ''
API_SECRET = ''

STOP_LOSS = 0.004       # i.e. default = 0.4%
TAKE_PROFIT = 0.01      # i.e. default = 1%
ENABLE_STOP_LOSS = True
ENABLE_TAKE_PROFIT = True

trade_symbols = ["XBTUSD", "ETHUSD"]
positions = {
    'XBTUSD': {'qty': 0},
    'ETHUSD': {'qty': 0}
}
orders = {'XBTUSD': [], 'ETHUSD': []}

def rounded_price(number, symbol):
    if symbol == "XBTUSD":
        return round(number * 2.0) / 2.0
    elif symbol == "ETHUSD":
        return round(number * 20.0) / 20.0

def auth_req_get(endpoint, query):
    # make authenticated GET requests
    global API_SECRET, API_KEY
    path = BASE_URL + endpoint
    e_path = '/api/v1/' + endpoint # path for encrypted message
    if query != '': # add query to paths
        path = path + "?" + query
        e_path = e_path + "?" + query
    expires = int(round(time.time()) + 10)
    message = str ('GET' + e_path + str(expires))
    signature = hmac.new(bytes(API_SECRET, 'utf8'),\
                bytes(message,'utf8'), digestmod=hashlib.sha256)\
                .hexdigest()
    request_headers = {
            'api-expires' : str(expires),
            'api-key' : API_KEY,
            'api-signature' : signature,
    }
    while True:
        resp = requests.get(path, headers=request_headers)
        if resp.status_code == 200:
            return json.loads(resp.content)
        else:
            print(resp.content)
        time.sleep(1)

def auth_req_post(endpoint, payload):
    # make authenticated POST requests
    global API_KEY, API_SECRET
    path = BASE_URL + endpoint
    e_path = '/api/v1/' + endpoint # path for encrypted message
    expires = int(round(time.time()) + 10)
    payload2 = str(payload.replace(' ', '')) # remove extra spaces
    message = str ('POST' + e_path + str(expires) + payload2)
    signature = hmac.new(bytes(API_SECRET, 'utf8'),\
                bytes(message,'utf8'), digestmod=hashlib.sha256).\
                hexdigest()
    request_headers = {
            'Content-type' : 'application/json',
            'api-expires' : str(expires),
            'api-key' : API_KEY,
            'api-signature' : signature,
    }
    resp = requests.post(path, headers=request_headers, data=payload2)
    return resp

def place_order(symbol, side, qty, ref_price, stop=False):
    if side == 'Buy': # it means we are SHORT
        if stop == True:
            # stop loss above entry
            price = ref_price * (1+STOP_LOSS)
        else:
            # take profit below entry
            price = ref_price * (1-TAKE_PROFIT)
    elif side == 'Sell': # it means we are LONG
        if stop == True:
            # stop loss below entry
            price = ref_price * (1-STOP_LOSS)
        else:
            # take profit above entry
            price = ref_price * (1+TAKE_PROFIT)
    order_details = {
        'symbol': symbol,
        'side': side,
        'orderQty': qty,
    }
    if stop == True: # add extra info for stop orders
        order_details['ordType'] = 'Stop'
        order_details['stopPx'] = rounded_price(price, symbol)
    else:
        order_details['price'] = rounded_price(price, symbol)
    result = auth_req_post('order', json.dumps(order_details))
    if result.status_code == 200:
        print('Order placed successfully.')
        get_positions()
        get_orders()
    else:
        print(result.content)

def get_positions():
    global positions
    # load positions in memory
    req = auth_req_get('position', '')
    for pos in req:
        sym = pos['symbol']
        positions[sym]['qty'] = pos['currentQty']
        positions[sym]['entry_price'] = pos['avgEntryPrice']

def get_orders():
    global trade_symbols, orders
    # load open orders in memory
    query = "filter=" + urllib.parse.quote_plus('{"open":true}')
    req = auth_req_get('order', query)
    for sym in trade_symbols:
        lst_orders = []
        for order in req:
            if order['symbol'] == sym:
                ord_details = {
                    'side': order['side'],
                    'o_id': order['orderID'],
                    'type': order['ordType']
                }
                lst_orders.append(ord_details)
        orders[sym] = lst_orders

def maintain_positions():
    global positions
    print('Positions are now loaded...')
    while True:
        get_positions()
        time.sleep(10)

def maintain_orders():
    global orders
    print('Orders are now loaded...')
    while True:
        get_orders()
        time.sleep(10)

def cover_positions():
    global positions, orders, STOP_LOSS, TAKE_PROFIT
    print('Actively scanning for open positions now.')
    while True:
        # cover open positions that do not have stop loss / take profit
        for sym in positions:
            if positions[sym]['qty'] > 0: # long position entered
                price = positions[sym]['entry_price']
                has_tp = False
                has_sl = False
                for od in orders[sym]:
                    if od['side'] == 'Sell' and od['type'] == 'Stop':
                        has_sl = True # found stop loss
                    elif od['side'] == 'Sell':
                        has_tp = True # found take profit
                if has_sl == False:
                    if ENABLE_STOP_LOSS == True:
                        place_order(sym, 'Sell', abs(positions[sym]['qty']),\
                                    price, True)
                if has_tp == False:
                    if ENABLE_TAKE_PROFIT == True:
                        place_order(sym, 'Sell', abs(positions[sym]['qty']),\
                                    price)
            elif positions[sym]['qty'] < 0: # short position entered
                price = positions[sym]['entry_price']
                has_tp = False
                has_sl = False
                for od in orders[sym]:
                    if od['side'] == 'Buy' and od['type'] == 'Stop':
                        has_sl = True # found stop loss
                    elif od['side'] == 'Buy':
                        has_tp = True # found take profit
                if has_sl == False:
                    if ENABLE_STOP_LOSS == True:
                        place_order(sym, 'Buy', abs(positions[sym]['qty']),\
                                    price, True)
                if has_tp == False:
                    if ENABLE_TAKE_PROFIT == True:
                        place_order(sym, 'Buy', abs(positions[sym]['qty']),\
                                    price)
        time.sleep(1)

if __name__ == '__main__':
    # start main threads
    Thread(target=maintain_positions).start()
    Thread(target=maintain_orders).start()
    Thread(target=cover_positions).start()
