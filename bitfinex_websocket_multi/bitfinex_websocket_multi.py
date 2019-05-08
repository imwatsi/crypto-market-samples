import websocket
import requests
import hashlib
import hmac
import json
import time
import os
from threading import Thread

# GLOBAL VARIABLES
channels = {0: 'Bitfinex'}
symbols = []
tickers = {}    # [market][bid/ask]
candles = {}    # [market][candle1,candle2...]

def update_tickers(data):
    global tickers
    sym = channels[data[0]][1]
    ticker_raw = data[1]
    ticker_parsed = {
        'bid': ticker_raw[0],
        'ask': ticker_raw[2],
        'last_price': ticker_raw[6],
        'volume': ticker_raw[7],
    }
    tickers[sym] = ticker_parsed

def update_candles(data):
    global candles
    def truncate_market(str_data):
        # Get market symbol from channel key
        col1 = str_data.find(':t')
        res = str_data[col1+2:]
        return res
    def parse_candle(lst_data):
        # Get candle dictionary from list
        return {
            'mts': lst_data[0],
            'open': lst_data[1],
            'close': lst_data[2],
            'high': lst_data[3],
            'low': lst_data[4],
            'vol': lst_data[5]
        }

    market = truncate_market(channels[data[0]][1])
    # Identify snapshot (list=snapshot, int=update)
    if type(data[1][0]) is list: 
        lst_candles = []
        for raw_candle in data[1]:
            candle = parse_candle(raw_candle)
            lst_candles.append(candle)
        candles[market] = lst_candles
    elif type(data[1][0]) is int:
        raw_candle = data[1]
        lst_candles = candles[market]
        candle = parse_candle(raw_candle)
        if candle['mts'] == candles[market][0]['mts']:
            # Update latest candle
            lst_candles[0] = candle
            candles[market] = lst_candles
        elif candle['mts'] > candles[market][0]['mts']:
            # Insert new (latest) candle
            lst_candles.insert(0, candle)
            candles[market] = lst_candles

def print_details():
    # interactive function to view tickers and candles
    while len(tickers) == 0 or len(candles) == 0:
        # wait for tickers to populate
        time.sleep(1)
    print('Tickers and candles loaded. You may query a symbol now.')
    while True:
        symbol = input()
        symbol = symbol.upper()
        if symbol not in symbols:
            print('%s not in list of symbols.' %(symbol))
            continue
        details = tickers[symbol]
        print('%s:  Bid: %s, Ask: %s, Last Price: %s, Volume: %s'\
            %(symbol, details['bid'], details['ask'],\
            details['last_price'], details['volume']))
        print('%s: currently has (%s) candles, latest candle: %s'\
            %(symbol, len(candles[symbol]), str(candles[symbol][0])))

def on_message(ws, message):
    global channels, balances, tickers
    data = json.loads(message)
    # Handle events
    if 'event' in data:
        if data['event'] == 'info':
            pass # ignore info messages
        elif data['event'] == 'auth':
            if data['status'] == 'OK':
                print('API authentication successful')
            else:
                print(data['status'])
        # Capture all subscribed channels
        elif data['event'] == 'subscribed':
            if data['channel'] == 'ticker':
                channels[data['chanId']] = [data['channel'], data['pair']]
            elif data['channel'] == 'candles':
                channels[data['chanId']] = [data['channel'], data['key']]
    # Handle channel data
    else:
        chan_id = data[0]
        if chan_id in channels:
            if 'ticker' in channels[chan_id]:
                # if channel is for ticker
                if data[1] == 'hb':
                    # Ignore heartbeat messages
                    pass
                else:
                    # parse ticker and save to memory
                    Thread(target=update_tickers, args=(data,)).start()
            elif 'candles' in channels[chan_id]:
                # if channel is for candles
                if data[1] == 'hb':
                    # Ignore heartbeat messages
                    pass
                else:
                    # parse candle update and save to memory
                    Thread(target=update_candles, args=(data,)).start()

def on_error(ws, error):
    print(error)

def on_close(ws):
    print('### API connection closed ###')
    os._exit(0)

def on_open(ws):
    print('API connected')
    for sym in symbols:
        sub_tickers = {
            'event': 'subscribe',
            'channel': 'ticker',
            'symbol': sym
        }
        ws.send(json.dumps(sub_tickers))
        sub_candles = {
            'event': 'subscribe',
            'channel': 'candles',
            'key': 'trade:15m:t' + sym
        }
        ws.send(json.dumps(sub_candles))
    # start printing the books
    Thread(target=print_details).start()

def connect_api():
    global ws
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp('wss://api.bitfinex.com/ws/2',
                            on_message = on_message,
                            on_error = on_error,
                            on_close = on_close,
                            on_open = on_open)
    ws.run_forever()

# load USD tickers
res = requests.get("https://api.bitfinex.com/v1/symbols")
all_sym = json.loads(res.content)
for x in all_sym:
    if "usd" in x:
        symbols.append(x.upper())
print('Found (%s) USD symbols' %(len(symbols)))

# initialize api connection
connect_api()
