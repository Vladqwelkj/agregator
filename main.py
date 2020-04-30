import psycopg2
from binance.websockets import BinanceSocketManager
from binance.client import Client
from binance.enums import *
from resources import ta_indicators
import threading
import time
from resources.utils import in_new_thread

@in_new_thread
def f():
    time.sleep(10)
    print('!')

for n in range(9800):
    print(n)
    f()
'''
candles = Client('', '').get_historical_klines('BTCUSDT', '1h', start_str='2 day ago')
print(candles)
closes = []
for c in candles:
    closes.append(float(c[4]))
[print(v) for v in closes]
bb = ta_indicators.calc_bbands(closes, 2, 20)
print(bb)


candles = client.get_historical_klines('BTCUSDT', '15m', start_str='12 hour ago')
print(candles)
closes = []
for c in candles:
    closes.append(float(c[4]))
[print(v) for v in closes]
bb = ta_indicators.calc_bbands(closes[:-1], 2, 20)

bm = BinanceSocketManager(client)
conn_key = bm.start_multiplex_socket(['btcusdt@kline_1m'], print)
bm.start()

# start any sockets here, i.e a trade socket
def print_if_candle_close(msg):
    #print(msg)
    msg = msg['data']
    if msg['k']['x']:
        print(msg['k']['c'])
symbols = list()
streams_names = list()

[symbols.append(s['symbol']) for s in client.get_exchange_info()['symbols']]

times = []

def in_new_thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

@in_new_thread
def get_klines():
    client.get_historical_klines(
        s,
        '1d',
        start_str='30 day ago')[:-1]
    client.get_historical_klines(
        s,
        '1h',
        start_str='2 day ago')[:-1]
    print('!')

t = time.time()
for s in symbols[750:]:
    for t in ['1m']:
        get_klines()
        

print((time.time()-t)/len(symbols[750:]))

exit()

# then start the socket manager
bm.start()
#print(9999)'''