import requests
import json
import time
from bfxhfindicators import Stochastic
from threading import Thread

candles = []

def load_candles():
    global candles
    while True:
        resp = requests.get('https://api.hitbtc.com/api/2/public/candles/ETHUSD?period=H1')
        raw_candles = json.loads(resp.content)
        parsed_candles = []
        for raw_c in raw_candles:
            new_candle = {
                'timestamp': raw_c['timestamp'],
                'close': float(raw_c['close']),
                'low': float(raw_c['min']),
                'high': float(raw_c['max'])
            }
            parsed_candles.append(new_candle)
        candles = parsed_candles[:]
        time.sleep(5)

# start loop that loads candles
Thread(target=load_candles).start()

# wait for candles to populate
while len(candles) == 0:
    time.sleep(1)

# calculate Stochastic Oscillator values
while True:
    iStoch = Stochastic([14,3,3])
    for candle in candles:
        iStoch.add(candle)
    stoch_values = iStoch.v()
    # print Stochastic values, identify basic levels
    str_print = 'ETHUSD:  K:%s D:%s' %(round(stoch_values['k'],4), round(stoch_values['d'],4))
    if stoch_values['k'] > 80 and stoch_values['d'] > 80:
        str_print += '  In overbought area...'
    elif stoch_values['k'] < 20 and stoch_values['d'] < 20:
        str_print += '  In oversold area...'
    print(str_print, end='\r', flush=True)
    time.sleep(1)
