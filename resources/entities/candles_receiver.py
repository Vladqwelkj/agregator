from binance.websockets import BinanceSocketManager
from binance.client import Client

import time
import datetime
import requests
import json

from ..utils import in_new_thread, write_log
from resources.entities.candle_callback import Candle
from resources.entities.proxy_distributor import ProxyDistributor

#написать штуку, которая будет понимать, что пришла свечка
class CandlesReceiver:
    def __init__(self,
         client: Client, 
         proxy_distributor: ProxyDistributor,
         symbols: list,
         data_agregator_callback):
        self.bm = BinanceSocketManager(client)
        self.client = client
        self.proxy_distributor = proxy_distributor
        self.data_agregator_callback = data_agregator_callback
        self.symbols = symbols

        self.is_available_rest_api_candles_sender = True
        self._callback_15m_is_available = dict()
        for symbol in symbols:
            self._callback_15m_is_available[symbol] = True



    def start(self):
        self._start_sender_candles_by_rest_api()


    def _get_exchange_time(self):
        max_attempts = 5
        for _ in range(max_attempts): # пять попыток. Чтобы была возможность сменить прокси
            try:
                r = requests.get(
                    'https://api.binance.com/api/v3/time',
                    proxies=self.proxy_distributor.get_proxy()
                    ).text
                break
            except Exception as e:
                print('_send_last_candle_by_symbol ERROR:', e)
                continue
        t = json.loads(r)['serverTime']/1000
        return datetime.datetime.utcfromtimestamp(t-10)
        


    @in_new_thread
    def _send_last_candle_by_symbol(self, symbol: str, interval: str):
        '''Отправляет в data_agregator последнюю свечку'''
        max_attempts = 5
        for _ in range(max_attempts): # пять попыток. Чтобы была возможность сменить прокси
            try:
                r = requests.get( # такая реализация получения свечки работает быстрее, чем методы из библиотек с api binance
                    'https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit=2'.format(symbol, interval),
                    proxies=self.proxy_distributor.get_proxy()
                    ).text
                break
            except Exception as e:
                print('_send_last_candle_by_symbol ERROR:', e)
                continue
        candle = json.loads(r)[0]
        self.data_agregator_callback(callback_data=Candle(
            symbol=symbol,
            interval=interval,
            O=candle[1],
            H=candle[2],
            L=candle[3],
            C=candle[4],
            volume=candle[5],
            ))


    @in_new_thread
    def _start_sender_candles_by_rest_api(self):
        while True:
            time_now = self._get_exchange_time()
            print(time_now)
            if time_now.minute%15==0: #if new 15m
                for symbol in self.symbols:
                    self._send_last_candle_by_symbol(symbol, '15m')
            if time_now.minute==00: # if new hour
                for symbol in self.symbols:
                    self._send_last_candle_by_symbol(symbol, '1h')
                if time_now.hour==00: # if new day
                    for symbol in self.symbols:
                        self._send_last_candle_by_symbol(symbol, '1d')
            if time_now.minute==00 or time_now.minute%15==0:
                time.sleep(100) 
            time.sleep(0.5)

'''
    def _start_ws_time_updater(self):
        self.bm.start_multiplex_socket(['!miniTicker@arr'], self._callback_for_time_updating)
        self.bm.start()


    def _callback_for_time_updating(self, data: dict):
        #print(data['data'][-1])
        self.exchange_time = data['data'][-1]['E']
'''
