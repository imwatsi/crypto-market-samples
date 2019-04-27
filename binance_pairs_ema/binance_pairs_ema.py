import requests
import json
import os
import time
from threading import Thread
from bfxhfindicators import EMA

BASE_URL = 'https://api.binance.com'

TIMEFRAME = '4h'
EMA_PERIODS = [50, 200]

symbols = []
candles = {}
prices = {}
ema_values = {}

def load_candles(sym):
    global candles, prices, BASE_URL
    payload = {
            'symbol': sym,
            'interval': '4h',
            'limit': 250
    }
    resp = requests.get(BASE_URL + '/api/v1/klines', params=payload)
    klines = json.loads(resp.content)
    # parse klines and store open, high, low, close and vol only
    parsed_klines = []
    for k in klines:
        k_candle = {
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'vol': float(k[5])
        }
        parsed_klines.append(k_candle)
    candles[sym] = parsed_klines
    index = len(parsed_klines) - 1 # get index of latest candle
    prices[sym] = parsed_klines[index]['close'] # save current price

# create results folder if it doesn't exist
if not os.path.exists('results/'):
    os.makedirs('results/')
# start with blank files
open('results/below_50.txt', 'w').close()
open('results/above_50_below_200.txt', 'w').close()
open('results/above_200.txt', 'w').close()

# load symbols information
print('Getting list of BTC trade pairs...')
resp = requests.get(BASE_URL + '/api/v1/ticker/allBookTickers')
tickers_list = json.loads(resp.content)
for ticker in tickers_list:
    if str(ticker['symbol'])[-4:] == 'USDT':
        symbols.append(ticker['symbol'])

# get 4h candles for symbols
print('Loading candle data for symbols...')
for sym in symbols:
    Thread(target=load_candles, args=(sym,)).start()
while len(candles) < len(symbols):
    print('%s/%s loaded' %(len(candles), len(symbols)), end='\r', flush=True)
    time.sleep(0.1)

# calculate EMAs for each symbol
print('Calculating EMAs...')
for sym in candles:
    for period in EMA_PERIODS:
        iEMA = EMA([period])
        lst_candles = candles[sym][:]
        for c in lst_candles:
            iEMA.add(c['close'])
        if sym not in ema_values:
            ema_values[sym] = {}
        ema_values[sym][period] = iEMA.v()

# save filtered EMA results in txt files
print('Saving filtered EMA results to txt files...')
for sym in ema_values:
    ema_50 = ema_values[sym][50]
    ema_200 = ema_values[sym][200]
    price = prices[sym]
    entry = ''
    if price < ema_50:
    # save symbols trading below EMA (50)
        f = open('results/below_50.txt', 'a')
        entry = '%s: $%s\n' %(sym, round(price,3))
        f.write(entry)
    elif price > ema_50 and price < ema_200:
    # save symbols trading above EMA(200)
        f = open('results/above_50_below_200.txt', 'a')
        entry = '%s: $%s\n' %(sym, round(price,3))
        f.write(entry)
    elif price > ema_200:
    # save symbols trading above EMA(50) but below EMA(200)
        f = open('results/above_200.txt', 'a')
        entry = '%s: $%s\n' %(sym, round(price,3))
        f.write(entry)
    f.close()
    del f # cleanup

print('All done! Results saved in results folder.')

