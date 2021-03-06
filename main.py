from binance.client import Client
from resources.entities.data_saver import DataSaver
from resources.entities.data_agregator import DataAgregator
from resources.entities.candles_receiver import CandlesReceiver
from resources.entities.candle_callback import Candle
from resources.entities.proxy_distributor import ProxyDistributor
from resources.utils import write_log

import time
import datetime

RSI_N = 14
BBANDS_N = 20
BBANDS_STD = 2

'''Число запросов в минуту не превысит 2400. Хватит трех прокси. + один дополнительный.
    None - работа без прокси. Нужен только https ключ. Пойдет практически любой socks5'''
PROXIES_FOR_REQUESTS = [
{'https':'https://8f14GB:szmSDZ@193.31.101.227:9666'},
{'https':'https://8f14GB:szmSDZ@193.31.101.197:9404'},
    {'https':'https://DfxFwZ:WcnJYV@185.221.163.141:9829'},
    {'https':'https://DfxFwZ:WcnJYV@185.221.161.226:9157'},
    None,
    ]



if __name__=='__main__':
    if datetime.datetime.now().minute%15==0:
        time.sleep(100) # чтобы избежать коллизий со свечками
    client = Client('', '')
    proxy_distributor = ProxyDistributor(PROXIES_FOR_REQUESTS)

    all_symbols = [s['symbol'] for s in client.get_exchange_info()['symbols']  if s['status']=='TRADING']
    needed_symbols = all_symbols[0:]
    needed_symbols.sort()
    print('\nNEEDED SYMBOLS:', needed_symbols)

    data_saver = DataSaver(needed_symbols)
    data_agregator = DataAgregator(
        client=client,
        data_saver=data_saver,
        proxy_distributor=proxy_distributor,
        symbols=needed_symbols,
        rsi_n=RSI_N,
        bbands_n=BBANDS_N,
        bbands_std=BBANDS_STD,
        )
    data_agregator.create_initial_candles_for_all_symbols()
    data_agregator.calc_initial_data_for_all_symbols()
    candles_receiver = CandlesReceiver(
        client=Client,
        proxy_distributor=proxy_distributor,
        symbols=needed_symbols,
        data_agregator_obj=data_agregator,
        data_agregator_callback=data_agregator.callback_for_candle_receiver)
    candles_receiver.start()

    while True:
        time.sleep(100)