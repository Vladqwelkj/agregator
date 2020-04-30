from binance.websockets import BinanceSocketManager
from binance.client import Client

import time
import datetime
import requests
import json

from .resources.utils import in_new_thread
from .resources.entities.candle_callback import CandleCallback



class CandlesReceiver:
    def __init__(self, client: Client, symbols: list, data_agregator_callback):
        self.bm = BinanceSocketManager(client)
        self.data_agregator_callback = data_agregator_callback
        self.symbols = symbols


    def start(self):
        self._start_15m_ws_candle_receiver()
        self._start_rest_api_1h_1d_candle_receiver()


    def _get_exchange_time(self):
        while True: # exchange_time не сразу определяется в _callback_when_15m_candle_received 
            try: # и нужно ждать, пока она впервые появится
                time = int(self.exchange_time)
                break
            except:
                time.sleep(1)
                continue
        return datetime.datetime.fromtimestamp(time/1000)


    @in_new_thread
    def _send_candle_by_symbol(self, symbol: str, interval: str):
        r = requests.get( # такая реализация получения свечки работает быстрее, чем методы из библиотек с api binance
            'https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit=2'.format(symbol, interval)
            ).text
        candle = json.loads(r)[0]
        self.data_agregator_callback(callback_data=CandleCallback(
            symbol=symbol,
            interval=interval,
            O=candle[1],
            H=candle[2],
            L=candle[3],
            C=candle[4],
            volume=candle[5],
            ))


    @in_new_thread
    def _start_rest_api_1h_1d_candle_receiver(self):
        while True:
            time_now = self._get_exchange_time()
            print(time_now)
            if time_now.minute==00: # if new hour
                for symbol in self.symbols:
                    self._send_candle_by_symbol(symbol, '1h')
                if time_now.hour==00: # if new day
                    for symbol in self.symbols:
                        self._send_candle_by_symbol(symbol, '1d')
                time.sleep(3000) # timeout. about 1 hour
            time.sleep(1)


    def _start_15m_ws_candle_receiver(self):
        streams_names = list()
        for symbol in symbols:
            streams_names.append(symbol.lower()+'@kline_15m')
        self.bm.start_multiplex_socket(streams_names, self._callback_when_15m_candle_received)
        self.bm.start()




    def _callback_when_15m_candle_received(self, data: dict):
        self.exchange_time = data['data']['e']
        candle = data['data']['k']
        if candle['x']: # Если свеча закрылась
            for callback in self._callbacks:
                self.data_agregator_callback(CandleCallback(
                    symbol=candle['s'],
                    interval='15m',
                    O=candle['o'],
                    H=candle['h'],
                    L=candle['l'],
                    C=candle['c'],
                    volume=candle['v'],
                    ))

                

