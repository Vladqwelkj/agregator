import psycopg2
from binance.websockets import BinanceSocketManager
from binance.client import Client
from resources.entities.data_saver import DataSaver
from resources.entities.data_agregator import DataAgregator
from resources.entities.candles_receiver import CandlesReceiver
from resources.entities.candle_callback import CandleCallback
from resources.entities.proxy_distributor import ProxyDistributor
client = Client('', '')
print(client.get_all_tickers())
'''
if __name__=='__main__':

    symbols = list()
    [symbols.append(s['symbol']) for s in client.get_exchange_info()['symbols']]



    t = time.time()
    for s in symbols[750:]:
        for t in ['1m']:
            get_klines()
            '''
pr = [{
		#'http':'http://54.37.131.45:3128',
		'https':'https://54.37.131.45:3128'},
        {
        #'http':'http://2369A9:RSjpr0@217.29.63.159:16176',
        'https':'socks5://85.10.235.14:1080'},

		None]
# 'https':'https://82.119.170.106:8080'},

p = ProxyDistributor(pr)