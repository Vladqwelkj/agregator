from .candle_callback import Candle
from .data_saver import DataSaver
from .ohlcv import OHLCV_candles
from .proxy_distributor import ProxyDistributor
from ..utils import in_new_thread, write_log
from ..ta_indicators import *

import time
import json

import requests
from binance.client import Client


class DataAgregator:
    def __init__(self,
         client: Client,
         data_saver: DataSaver,
         proxy_distributor: ProxyDistributor,
         symbols: list,
         rsi_n=14,
         bbands_n=20,
         bbands_std=2):

        self.client = client
        self.db = data_saver
        self.proxy_distributor = proxy_distributor
        self.symbols = symbols
        self.rsi_n = rsi_n
        self.bbands_n = bbands_n
        self.bbands_std = bbands_std

        self._all_pairs_and_base_assets = dict()
        self._rates_for_all_base_assets_and_btc = dict()

        self.OHLCV_15m = dict()
        self.OHLCV_1h = dict()
        self.OHLCV_1d = dict()

        self.RSI_15m = dict()
        self.RSI_1h = dict()
        self.RSI_1d = dict()
        self.RSI_1h_15m_diff = dict()
        self.RSI_1h_15m_avg = dict()
        self.bbands_width_15m = dict()
        self.avg_volume_10d_in_btc = dict()

        self._timestamp_from_last_base_assets_rates_calculating = 0
        self.ignored_symbols = list()
        self.MIN_CANDLES_LEN = 25


    def _get_all_pairs_and_base_assets(self):
        '''Создает словарь с отношением пар и котировочных валют.
        Создает множество всех котировочных активов, кроме BTC.
        Вызывается в calc_initial_data_for_all_symbols.
        Нужно для подсчета обьема в BTC.'''
        for s in self.client.get_exchange_info()['symbols']:
            self._all_pairs_and_base_assets[s['symbol']] = s['baseAsset']
        self._all_base_assets = set(self._all_pairs_and_base_assets.values())
        #print(self._all_base_assets)
        self._all_base_assets.remove('BTC')


    def _update_rates_for_all_base_assets_and_btc(self):
        '''Обновляет курсы базовых(первой в паре) валют к BTC.
        Вызывается в каждом callback`е во время получения 15м свечки
        и при вызове calc_initial_data_for_all_symbols.
        Должен раз в 15 минут обновлять курс котировочных валют к BTC.
        Нужно для подсчета обьема в BTC.'''
        first_time = False
        if self._timestamp_from_last_base_assets_rates_calculating==0:
            self._timestamp_from_last_base_assets_rates_calculating = time.time()
            first_time = True
        if (time.time() - self._timestamp_from_last_base_assets_rates_calculating > 60*15) or first_time:
            self._timestamp_from_last_base_assets_rates_calculating = time.time()
            tickers_for_all_symbols = self.client.get_all_tickers()
            for base_asset in self._all_base_assets:
                self._rates_for_all_base_assets_and_btc[base_asset] = None
                for ticker in tickers_for_all_symbols:
                    if ticker['symbol']==base_asset+'BTC':
                        self._rates_for_all_base_assets_and_btc[base_asset] = float(ticker['price'])
                    if ticker['symbol']=='BTC'+base_asset: #Если попадается фиатная пара
                        self._rates_for_all_base_assets_and_btc[base_asset] = 1/float(ticker['price'])
                    if self._rates_for_all_base_assets_and_btc[base_asset]: # Если цена была найдена
                        tickers_for_all_symbols.remove(ticker) # Чтобы больше пара не попадалась
                        break 


    def create_initial_candles_for_all_symbols(self):
        '''Запускать нужно один раз после объявление экземпляра DataAgregator'''
        for symbol in self.symbols:
            self.OHLCV_15m[symbol] = OHLCV_candles()
            self.OHLCV_1h[symbol] = OHLCV_candles()
            self.OHLCV_1d[symbol] = OHLCV_candles()
            self._get_initial_candles_by_symbol(symbol)


    @in_new_thread
    def calc_initial_data_for_all_symbols(self):
        '''Создает все индикаторы для всех символов.
        Запускать нужно один раз после объявление экземпляра DataAgregator
        и после вызова create_initial_candles_for_all_symbols'''
        self._get_all_pairs_and_base_assets()
        self._update_rates_for_all_base_assets_and_btc()
        for symbol in self.symbols:
            self._calc_all_indicators_for_symbol_and_interval(symbol, first_time=True)


    @in_new_thread
    def _calc_all_indicators_for_symbol_and_interval(self, symbol, interval=None, first_time=False):
        '''Расчитывает все возможные индикаторы для данного символа и таймфрейма.'''
        if first_time:
            while True: # Проверка наличия свечек
                if self.OHLCV_1d[symbol].C and self.OHLCV_1h[symbol].C and self.OHLCV_15m[symbol].C:
                    break
                time.sleep(0.5)
            time.sleep(5)
            if len(self.OHLCV_1d[symbol].C)+3 < self.MIN_CANDLES_LEN: # Убираем символы, у которых недостаточно свечей.
                self.ignored_symbols.append(symbol)
                print("Не хватает свечек. Удален", symbol)
                self.db.delete_symbol(symbol)
                return

        if interval=='15m' or first_time:
            self.RSI_15m[symbol] = calc_last_RSI(self.OHLCV_15m[symbol].C, self.rsi_n)
            self.bbands_width_15m[symbol] = calc_last_bbands_width(
                self.OHLCV_15m[symbol].C, self.bbands_std, self.bbands_n)
            self.db.update_rsi(symbol, '15m', self.RSI_15m[symbol])
            self.db.update_bbands_width_15m(symbol, self.bbands_width_15m[symbol])

        if interval=='1h' or first_time:
            self.RSI_1h[symbol] = calc_last_RSI(self.OHLCV_1h[symbol].C, self.rsi_n)
            self.db.update_rsi(symbol, '1h', self.RSI_1h[symbol])

        if interval in ['1h', '15m'] or first_time:
            self.RSI_1h_15m_diff[symbol] = abs(self.RSI_1h[symbol] - self.RSI_15m[symbol])
            self.RSI_1h_15m_avg[symbol] = (self.RSI_1h[symbol] + self.RSI_15m[symbol])/2
            self.db.update_rsi_1h_15m_diff(symbol, self.RSI_1h_15m_diff[symbol])
            self.db.update_rsi_1h_15m_avg(symbol, self.RSI_1h_15m_avg[symbol])

        if interval=='1d' or first_time:
            self.RSI_1d[symbol] = calc_last_RSI(self.OHLCV_1d[symbol].C, self.rsi_n)
            self.db.update_rsi(symbol, '1d', self.RSI_1d[symbol])
            try:
                self.avg_volume_10d_in_btc[symbol] = (
                    sum(self.OHLCV_1d[symbol].volume[-10:])/10
                    *self._get_rates_for_base_asset_and_btc(symbol))
            except TypeError: #Значит нельзя найти курс для валюты и btc
                return
            self.db.update_avg_volume_10d_in_btc(symbol, self.avg_volume_10d_in_btc[symbol])


    def _get_rates_for_base_asset_and_btc(self, symbol):
        '''Узнает курс котировочной валюты к BTC.
        Если котировочная валюта - BTC, то возвращается 1.
        Нужно для подсчета объема в BTC'''
        base_asset = self._all_pairs_and_base_assets[symbol]
        if base_asset=='BTC':
            return 1
        rate = self._rates_for_all_base_assets_and_btc[base_asset]
        return rate


    def _get_candles_by_symbol(self, symbol, interval: str, limit: int):
        max_attempts = 5
        for _ in range(max_attempts): # пять попыток. Чтобы была возможность сменить прокси
            try:
                r = requests.get( # такая реализация получения свечки работает быстрее, чем методы из библиотек с api binance
                    'https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit={}'.format(symbol, interval, limit),
                    proxies=self.proxy_distributor.get_proxy()
                    ).text
                break
            except:
                continue
        candles = json.loads(r)
        return candles



    @in_new_thread
    def _get_initial_candles_by_symbol(self, symbol):
        candles_1d = self._get_candles_by_symbol(symbol, '1d', self.MIN_CANDLES_LEN)[:-1]
        candles_1h = self._get_candles_by_symbol(symbol, '1h', self.MIN_CANDLES_LEN)[:-1]
        candles_15m = self._get_candles_by_symbol(symbol, '15m', self.MIN_CANDLES_LEN)[:-1]
        #print(candles_1d)
        tmp_candle_pairs = [
            (candles_1d, self.OHLCV_1d),
            (candles_1h, self.OHLCV_1h), 
            (candles_15m, self.OHLCV_15m)
            ]
        for candle_in, candle_out in tmp_candle_pairs:
            for c in candle_in:
                candle_out[symbol].add_new_OHLCV_candle(
                    c[1], c[2], c[3], c[4], c[5],
                    delete_first_candle=False)
                if candle_out is self.OHLCV_1d:
                    interval = '1d'
                if candle_out is self.OHLCV_1h:
                    interval = '1h'
                if candle_out is self.OHLCV_15m:
                    interval = '15m'
                self.db.add_ohlcv(Candle(
                    symbol,
                    interval,
                    c[1], c[2], c[3], c[4], c[5],))


    @in_new_thread
    def callback_for_candle_receiver(self, callback_data: Candle):
        if callback_data.symbol in self.ignored_symbols:
            return
        '''сallback функция, которая передается в СandlesReceiver.
        Вызывается, когда получена новая свечка 15 минутка.'''
        if callback_data.interval=='15m':
            self._update_rates_for_all_base_assets_and_btc()
            current_candle = self.OHLCV_1d
        if callback_data.interval=='1h':
            current_candle = self.OHLCV_1d
        if callback_data.interval=='1d':
            current_candle = self.OHLCV_1d
        current_candle[callback_data.symbol].add_new_OHLCV_candle(
            callback_data.O,
            callback_data.H,
            callback_data.L,
            callback_data.C,
            callback_data.volume,)
        self.db.add_ohlcv(callback_data)
        self._calc_all_indicators_for_symbol_and_interval(callback_data.symbol, callback_data.interval)