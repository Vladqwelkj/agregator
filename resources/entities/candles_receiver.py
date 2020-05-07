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
        


    def _convert_15m_candles(self, symbol, candles_15m: list, new_interval: str):
        if new_interval=='1d':
            coef_15m = 96 # 24*60 / 15
        if new_interval=='1h': 
            coef_15m = 4  # 60 / 15

        to_convert = candles_15m[-coef_15m:]
        volume = 0
        open_ = float(to_convert[0][1])
        close_ = float(to_convert[-1][4])
        low, high = list(), list()
        for candle in to_convert:
            low.append(float(candle[3]))
            high.append(float(candle[2]))
            volume += float(candle[5])
        return Candle(
            symbol=symbol,
            interval=new_interval,
            O=open_,
            H=max(high),
            L=min(low),
            C=close_,
            volume=volume,
            )



    @in_new_thread
    def _send_last_candles_by_symbol(self, symbol: str, interval_1d: bool, interval_1h: bool, interval_15m=True, recursion_level=0):
        '''Отправляет в data_agregator последнюю свечку'''
        if recursion_level > 2: # если уже полминуты нельзя получить новую свечку, значит новой свечки нет (мертвые торги)
            return
        limit = 2
        if interval_1h:
            limit = 5
        if interval_1d:
            limit = 97

        max_attempts = 5
        for _ in range(max_attempts): # пять попыток. Чтобы была возможность сменить прокси
            try:
                r = requests.get( # такая реализация получения свечки работает быстрее, чем методы из библиотек с api binance
                    'https://api.binance.com/api/v1/klines?symbol={}&interval=15m&limit={}'.format(symbol, limit),
                    proxies=self.proxy_distributor.get_proxy()
                    ).text
                received_closed_candles = json.loads(r)[:-1]
                break
            except Exception as e:
                print('_send_last_candles_by_symbol ERROR:', e)
                time.sleep(1)
                continue
        last_closed_15m_candle = received_closed_candles[-1]
        last_closed_15m_candle = Candle(
            symbol=symbol,
            interval='15m',
            O=last_closed_15m_candle[1],
            H=last_closed_15m_candle[2],
            L=last_closed_15m_candle[3],
            C=last_closed_15m_candle[4],
            volume=last_closed_15m_candle[5],
            )
        if self._check_equality_of_last_data_agregator_candle_and_new_candle(new_candle=last_closed_15m_candle): # Если получили устаревшую свечку
            time.sleep(10)
            self._send_last_candles_by_symbol(symbol, interval_1d, interval_1h, recursion_level=recursion_level+1)
            return

        self.data_agregator_callback(callback_data=last_closed_15m_candle)
        if interval_1h:
            last_closed_1h_candle = self._convert_15m_candles(symbol, received_closed_candles, '1h')
            self.data_agregator_callback(callback_data=last_closed_1h_candle)
        if interval_1d:
            last_closed_1d_candle = self._convert_15m_candles(symbol, received_closed_candles, '1d')
            self.data_agregator_callback(callback_data=last_closed_1d_candle)
        


    def _check_equality_of_last_data_agregator_candle_and_new_candle(self, new_candle: Candle):
        '''Проверяет, является ли переданная новая свечка равной последней свечке.'''
        old_candels = self.data_agregator_obj.OHLCV_15m[new_candle.symbol]
        if (old_candels.O[-1]==new_candle.O
             and old_candels.H[-1]==new_candle.H
             and old_candels.L[-1]==new_candle.L 
             and old_candels.C[-1]==new_candle.C
             and old_candels.volume[-1]==new_candle.volume):
            return True


    @in_new_thread
    def _start_sender_candles_by_rest_api(self):
        while True:
            time_now = self._get_exchange_time()
            print(time_now)
            if time_now.minute%15==0:
                interval_1h = False
                interval_1d = False
                time.sleep(9) 
                if time_now.minute==00: # if new hour
                    interval_1h = True
                    if time_now.hour==00: # if new day
                        interval_1d = True
                for symbol in self.symbols:
                    self._send_last_candles_by_symbol(symbol, interval_1d, interval_1h)
                time.sleep(800) # чтобы второй раз свечка не отправилась
            time.sleep(1.5)
