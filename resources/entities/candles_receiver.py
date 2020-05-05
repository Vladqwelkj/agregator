from binance.websockets import BinanceSocketManager
from binance.client import Client

import time
import datetime
import requests
import json

from ..utils import in_new_thread, write_log
from resources.entities.candle_callback import Candle
from resources.entities.proxy_distributor import ProxyDistributor


class CandlesReceiver:
    def __init__(self,
         client: Client, 
         proxy_distributor: ProxyDistributor,
         symbols: list,
         data_agregator_obj,
         data_agregator_callback):
        self.bm = BinanceSocketManager(client)
        self.client = client
        self.proxy_distributor = proxy_distributor
        self.data_agregator_obj = data_agregator_obj
        self.data_agregator_callback = data_agregator_callback
        self.symbols = symbols

        self.is_available_rest_api_candles_sender = True


    def start(self):
        self._start_sender_candles_by_rest_api()


    def stop_symbol_tracking(self, symbol):
        self.symbols.remove(symbol)

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
                print('_get_exchange_time ERROR:', e)
                time.sleep(1)
                continue
        t = json.loads(r)['serverTime']/1000
        return datetime.datetime.utcfromtimestamp(t)
        

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
                time.sleep(1)
                continue
        candle = json.loads(r)[0]
        candle = Candle(
            symbol=symbol,
            interval=interval,
            O=candle[1],
            H=candle[2],
            L=candle[3],
            C=candle[4],
            volume=candle[5],
            )
        if self._check_equality_of_last_data_agregator_candle_and_new_candle(new_candle=candle):
            time.sleep(10)
            self._send_last_candle_by_symbol(symbol, interval)
            return
        self.data_agregator_callback(callback_data=candle)


    def _check_equality_of_last_data_agregator_candle_and_new_candle(self, new_candle: Candle):
        if new_candle.interval=='15m':
            to_compare = self.data_agregator_obj.OHLCV_15m[new_candle.symbol]
        if new_candle.interval=='1h':
            to_compare = self.data_agregator_obj.OHLCV_1h[new_candle.symbol]
        if new_candle.interval=='1d':
            to_compare = self.data_agregator_obj.OHLCV_1d[new_candle.symbol]
        if (to_compare.O[-1]==new_candle.O
             and to_compare.H[-1]==new_candle.H
             and to_compare.L[-1]==new_candle.L 
             and to_compare.C[-1]==new_candle.C
             and to_compare.volume[-1]==new_candle.volume):
            return True


    @in_new_thread
    def _start_sender_candles_by_rest_api(self):
        while True:
            time_now = self._get_exchange_time()
            print(time_now)
            if time_now.minute==00 or time_now.minute%15==0:
                time.sleep(9) 
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
            time.sleep(1.5)
