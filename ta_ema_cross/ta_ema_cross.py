import requests
import json
import time
from bfxhfindicators import EMA
from threading import Thread

BASE_URL = 'https://api.hitbtc.com'

historic_window = 10
symbols = []
candles = {}
ema_values = {}
ema_periods = [10,20]
go_on = False


def import_candles(symbol):
    global candles
    # get candles
    resp = requests.get(BASE_URL + '/api/2/public/candles/%s?period=M15&limit=250'
                        %(symbol))
    raw_candles = json.loads(resp.content)
    # parse candles and save to memory
    parsed_candles = []
    for raw_c in raw_candles:
        new_candle = {
            'timestamp': raw_c['timestamp'],
            'close': float(raw_c['close']),
            'low': float(raw_c['min']),
            'high': float(raw_c['max'])
        }
        parsed_candles.append(new_candle)
    candles[symbol] = parsed_candles[:]

def show_progress():
    global go_on
    #wait for symbols to load
    while True:
        time.sleep(0.2)
        print('Importing candles: %s/%s symbols loaded'
                %(len(candles), len(symbols)), end='\r')
        if len(candles) == len(symbols): # break when equal
            break
    go_on = True


# get 20 USD symbols
print('Retrieving the first 20 USD symbols')
resp = requests.get(BASE_URL + '/api/2/public/symbol')
all_sym = json.loads(resp.content)
for x in all_sym:
    if 'USD' in x['id']:
        symbols.append(x['id'])
    if len(symbols) == 20:
        break
print('Found (%s) symbols.' %(len(symbols)))

# import candles for each symbol
Thread(target=show_progress).start() # show progress
for sym in symbols:
    Thread(target=import_candles, args=(sym,)).start()

# wait until all candles are loaded
while go_on == False:
    time.sleep(1)
print('\nAll candles loaded.')

# calculate EMA values
print('Calculating EMA values and scanning for crosses...', end='', flush=True)
for sym in symbols:
    for period in ema_periods:
        iEMA = EMA([period]) # define EMA object
        for candle in candles[sym]:
            iEMA.add(candle['close']) # add all close prices
        lst_ema = []
        lst_ema.append(iEMA.v()) # add current EMA value
        for i in range(historic_window):
            # add historic EMA values
            lst_ema.append(iEMA.prev(i+1))
        if sym not in ema_values: # add symbol key to dictionary
            ema_values[sym] = {}
        ema_values[sym][period] = lst_ema # save EMA values

# identify EMA crosses
ema_results = {
    'cross-downs': [],
    'cross-ups': []
}
for sym in symbols:
    # get primary and secondary EMA lists, and reverse for oldest first
    ema_first = ema_values[sym][ema_periods[0]][:]
    ema_second = ema_values[sym][ema_periods[1]][:]
    ema_first.reverse()
    ema_second.reverse()

    # determine type of cross to look for
    if ema_first[0] > ema_second[0]:
        look_for = 'cross-down'
    elif ema_first[0] < ema_second[0]:
        look_for = 'cross-up'

    # filter out symbols that meet criteria
    for i in range(1, historic_window + 1):
        if look_for == 'cross-down':
            if ema_first[i] < ema_second[i]:
                # primary EMA has gone below secondary
                tmp = ema_results['cross-downs']
                if sym not in tmp:
                    tmp.append(sym) # update list
                ema_results['cross-downs'] = tmp # save list
                del tmp
        elif look_for == 'cross-up':
            if ema_first[i] > ema_second[i]:
                # primary EMA has gone above secondary
                tmp = ema_results['cross-ups']
                if sym not in tmp:
                    tmp.append(sym) # update list
                ema_results['cross-ups'] = tmp # save list
                del tmp
print('done')

# print results
print('Primary EMA Period: %s' %(ema_periods[0]))
print('Secondary EMA Period: %s\n' %(ema_periods[1]))
print('EMA(%s) cross below EMA(%s):\n' %(ema_periods[0], ema_periods[1]))
for x_down in ema_results['cross-downs']:
    print(x_down)
print('\nEMA(%s) cross above EMA(%s):\n' %(ema_periods[0], ema_periods[1]))
for x_up in ema_results['cross-ups']:
    print(x_up)
