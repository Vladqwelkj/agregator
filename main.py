import psycopg2
from binance.websockets import BinanceSocketManager
from binance.client import Client
from binance.enums import *
import ta_indicators
import threading



client = Client('', '')
'''
candles = client.get_historical_klines('BTCUSDT', '15m', start_str='12 hour ago')
print(candles)
closes = []
for c in candles:
    closes.append(float(c[4]))
[print(v) for v in closes]
bb = ta_indicators.calc_bbands(closes[:-1], 2, 20)



ё   '
bm = BinanceSocketManager(client)
# start any sockets here, i.e a trade socket
def print_if_candle_close(msg):
    #print(msg)
    msg = msg['data']
    if msg['k']['x']:
        print(msg['k']['c'])
symbols = list()
streams_names = list()

[symbols.append(s['symbol']) for s in client.get_exchange_info()['symbols']]

for s in symbols:
    for t in ['1m']:
        streams_names.append(s.lower()+'@kline_'+t)
print(len(streams_names))


conn_key = bm.start_multiplex_socket(streams_names, print_if_candle_close)
# then start the socket manager
bm.start()
#print(9999)