from .candle_callback import CandleCallback
from .data_saver import DataSaver
from .ohlcv import OHLCV_candles
from .proxy_distributor import ProxyDistributor
from ..utils import in_new_thread
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
        self.data_saver = data_saver
        self.symbols = symbols
        self.rsi_n = rsi_n
        self.bbands_n = bbands_n
        self.bbands_std = bbands_std

        self._all_pairs_and_quote_assets = dict()
        self._rates_for_all_quote_assets_and_btc = dict()

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

        self._timestamp_from_last_quote_assets_rates_calculating = 0


    def _get_all_pairs_and_quote_assets(self):
        '''Создает словарь с отношением пар и котировочных валют.
        Создает множество всех котировочных активов, кроме BTC.
        Вызывается в calc_initial_data_for_all_symbols.'''
        for s in self.client.get_exchange_info()['symbols']:
            self._all_pairs_and_quote_assets[s['symbol']] = s['quoteAsset']
        self._all_quote_assets = set(self._all_pairs_and_quote_assets.keys())
        self._all_quote_assets.remove('BTC')


    def _calc_rates_for_all_quote_assets_and_btc(self):
        '''Обновляет курсы котировочных валют к BTC.
        Вызывается в каждом callback`е во время получения 15м свечки
        и при вызове calc_initial_data_for_all_symbols.
        Должен раз в 15 минут обновлять курс котировочных валют к BTC.'''
        first_time = False
        if self._timestamp_from_last_quote_assets_rates_calculating==0:
            self._timestamp_from_last_quote_assets_rates_calculating = time.time()
            first_time = True
        if (time.time() - self._timestamp_from_last_quote_assets_rates_calculating > 60*15) or first_time:
            tickers_for_all_symbols = self.client.get_all_tickers()
            for quote_asset in self._all_quote_assets:
                self._rates_for_all_quote_assets_and_btc[quote_asset] = None
                for ticker in tickers_for_all_symbols:
                    if ticker['symbol']==quote_asset+'BTC':
                        self._rates_for_all_quote_assets_and_btc[quote_asset] = float(ticker['price'])
                    if ticker['symbol']=='BTC'+quote_asset: # для случаев, когда попадаются фиатные валюты
                        self._rates_for_all_quote_assets_and_btc[quote_asset] = float(ticker['price'])
                    if self._rates_for_all_quote_assets_and_btc[quote_asset]: # Если цена была найдена
                        tickers_for_all_symbols.remove(ticker) # Чтобы больше пара не попадалась
                        break 




    @in_new_thread
    def get_initial_candles_for_all_symbols(self):
         '''Запускать нужно один раз после объявление экземпляра DataAgregator'''
        for symbol in self.symbols:
            self.OHLCV_15m[symbol] = OHLCV_candles()
            self.OHLCV_1h[symbol] = OHLCV_candles()
            self.OHLCV_1d[symbol] = OHLCV_candles()
            self._get_initial_candles_by_symbol(symbol)
            # save to db....


    @in_new_thread
    def calc_initial_data_for_all_symbols(self):
        '''Создает все индикаторы для всех символов.
        Запускать нужно один раз после объявление экземпляра DataAgregator
        и после вызова get_initial_candles_for_all_symbols'''
        self._get_all_pairs_and_quote_assets()
        self._calc_rates_for_all_quote_assets_and_btc()
        for symbol in self.symbols:
            self.RSI_15m[symbol] = calc_last_RSI(self.OHLCV_15m[symbol].C, self.rsi_n)
            self.bbands_width_15m[symbol] = calc_last_bbands_width(
                self.OHLCV_15m[symbol].C, self.bbands_std, self.bbands_n)
            self.RSI_1h[symbol] = calc_last_RSI(self.OHLCV_1h[symbol].C, self.rsi_n)
            self.RSI_1h_15m_diff[symbol] = abs(self.RSI_1h[symbol] - self.RSI_15m[symbol])
            self.RSI_1h_15m_avg[symbol] = (self.RSI_1h[symbol] + self.RSI_15m[symbol])/2
            self.RSI_1d[symbol] = self.calc_last_RSI(self.OHLCV_1d[symbol].C, self.rsi_n)
            self.avg_volume_10d_in_btc[symbol] = (
                sum(self.OHLCV_1d[symbol].volume[-10:])/10
                *_get_rates_for_quote_asset_and_btc(symbol))
            # save to db....


    def _calc_all_indicators_for_symbol_and_interval(self, symbol, interval):
        '''Расчитыват все возможные индикаторы для данного символа и таймфрейма.'''
        if interval=='15m':
            self.RSI_15m[symbol] = calc_last_RSI(self.OHLCV_15m[symbol].C, self.rsi_n)
            self.bbands_width_15m[symbol] = calc_last_bbands_width(
                self.OHLCV_15m[symbol].C, self.bbands_std, self.bbands_n)
        if interval=='1h':
            self.RSI_1h[symbol] = calc_last_RSI(self.OHLCV_1h[symbol].C, self.rsi_n)
        if interval in ['1h', '15m']:
            self.RSI_1h_15m_diff[symbol] = abs(self.RSI_1h[symbol] - self.RSI_15m[symbol])
            self.RSI_1h_15m_avg[symbol] = (self.RSI_1h[symbol] + self.RSI_15m[symbol])/2
        if interval=='1d':
            self.RSI_1d[symbol] = self.calc_last_RSI(self.OHLCV_1d[symbol].C, self.rsi_n)
            self.avg_volume_10d_in_btc[symbol] = (
                sum(self.OHLCV_1d[symbol].volume[-10:])/10
                *_get_rates_for_quote_asset_and_btc(symbol))
        # save to db....


    def _get_rates_for_quote_asset_and_btc(self, symbol):
        '''Узнает курс котировочной валюты к BTC.
        Если котировочная валюта - BTC, то возвращается 1.
        Нужно для подсчета объема в BTC'''
        quote_asset = self._all_pairs_and_quote_assets[symbol]
        if quote_asset=='BTC':
            return 1
        else:
            rate = self._rates_for_all_quote_assets_and_btc[quote_asset]
            return rate


    def _get_candles_by_symbol(self, symbol, interval: str, limit: int):
        r = requests.get( # такая реализация получения свечки работает быстрее, чем методы из библиотек с api binance
            'https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit={}'.format(symbol, interval, limit)
            ).text
        candles = json.loads(r)
        return candles



    @in_new_thread
    def _get_initial_candles_by_symbol(self, symbol):
        candles_1d = self._get_candles_by_symbol(symbol, '1d', 40)[:-1]
        candles_1h = self._get_candles_by_symbol(symbol, '1h', 40)[:-1]
        candles_15m = self._get_candles_by_symbol(symbol, '15m', 40)[:-1]

        for c in candles_1d:
            for ohlcv in [OHLCV_1d, OHLCV_1h, OHLCV_15m]:
                self.ohlcv[symbol].add_new_OHLCV_candle(
                    c[1], c[2], c[3], c[4], c[5],
                    delete_first_candle=False)
        # save to db....


    @in_new_thread
    def callback_for_candle_receiver(self, callback_data: CandleCallback):
        if callback_data.interval=='15m':
            self._calc_rates_for_all_quote_assets_and_btc()
            self.OHLCV_15m[callback_data.symbol].add_new_OHLCV_candle(
                callback_data.O,
                callback_data.H,
                callback_data.L,
                callback_data.C,
                callback_data.volume,)
        if callback_data.interval=='1h':
            self.OHLCV_1h[callback_data.symbol].add_new_OHLCV_candle(
                callback_data.O,
                callback_data.H,
                callback_data.L,
                callback_data.C,
                callback_data.volume,)
        if callback_data.interval=='1d':
            self.OHLCV_1d[callback_data.symbol].add_new_OHLCV_candle(
                callback_data.O,
                callback_data.H,
                callback_data.L,
                callback_data.C,
                callback_data.volume,)
        self._calc_all_indicators_for_symbol_and_interval(callback_data.symbol, callback_data.interval)