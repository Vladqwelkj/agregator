from .resources.entities.candle_callback import CandleCallback
from .resources.entities.data_saver import DataSaver
from .resources.entities.ohlcv import OHLCV_candles
from .resources.utils import in_new_thread
from .resources import ta_indicators

from numba import jit
from binance.client import Client


class DataAgregator:
    def __init__(self, client: Client, data_saver: DataSaver, symbols: list, rsi_n=14, bbands_n=20, bbands_std=2):
        self.client = client
        self.data_saver = data_saver
        self.symbols = symbols
        self.rsi_n = rsi_n
        self.bbands_n = bbands_n
        self.bbands_std = bbands_std

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

    @in_new_thread
    def get_initial_candles_for_all_symbols(self):
        for symbol in self.symbols:
            self.OHLCV_15m[symbol] = OHLCV_candles()
            self.OHLCV_1h[symbol] = OHLCV_candles()
            self.OHLCV_1d[symbol] = OHLCV_candles()
            self._get_initial_candles_by_symbol(symbol)
            # save to db....

    @in_new_thread
    def calc_initial_data_for_all_symbols(self):
        for symbol in self.symbols:
            self.RSI_15m[symbol] = ta_indicators.calc_last_RSI(self.OHLCV_15m[symbol].C, self.rsi_n)
            self.bbands_width_15m[symbol] = ta_indicators.calc_last_bbands_width(
                self.OHLCV_15m[symbol].C, self.bbands_std, self.bbands_n)
            self.RSI_1h[symbol] = ta_indicators.calc_last_RSI(self.OHLCV_1h[symbol].C, self.rsi_n)
            self.RSI_1h_15m_diff[symbol] = abs(self.RSI_1h[symbol] - self.RSI_15m[symbol])
            self.RSI_1h_15m_avg[symbol] = (self.RSI_1h[symbol] + self.RSI_15m[symbol])/2
            self.RSI_1d[symbol] = self.calc_last_RSI(self.OHLCV_1d[symbol].C, self.rsi_n)
            self.avg_volume_10d_in_btc[symbol] = sum(self.OHLCV_1d[symbol].volume[-10:])/10
            # save to db....

    def _calc_all_indicators(self, symbol, interval):
        if interval=='15m':
            self.RSI_15m[symbol] = ta_indicators.calc_last_RSI(self.OHLCV_15m[symbol].C, self.rsi_n)
            self.bbands_width_15m[symbol] = ta_indicators.calc_last_bbands_width(
                self.OHLCV_15m[symbol].C, self.bbands_std, self.bbands_n)
        if interval=='1h':
            self.RSI_1h[symbol] = ta_indicators.calc_last_RSI(self.OHLCV_1h[symbol].C, self.rsi_n)
        if interval in ['1h', '15m']:
            self.RSI_1h_15m_diff[symbol] = abs(self.RSI_1h[symbol] - self.RSI_15m[symbol])
            self.RSI_1h_15m_avg[symbol] = (self.RSI_1h[symbol] + self.RSI_15m[symbol])/2
        if interval=='1d':
            self.RSI_1d[symbol] = self.calc_last_RSI(self.OHLCV_1d[symbol].C, self.rsi_n)
            self.avg_volume_10d_in_btc[symbol] = sum(self.OHLCV_1d[symbol].volume[-10:])/10
        # save to db....



    @in_new_thread
    def _get_initial_candles_by_symbol(self, symbol):
        candles_1d = client.get_historical_klines(
            self.symbol,
            '1d',
            start_str='30 day ago')[:-1]
        candles_1h = client.get_historical_klines(
            self.symbol,
            '1h',
            start_str='2 day ago')[:-1]
        candles_15m = client.get_historical_klines(
            self.symbol,
            '15m',
            start_str='15 hour ago')[:-1]

        for c in candles_1d:
            self.OHLCV_1d[symbol].add_new_OHLCV_candle(c[1], c[2], c[3], c[4], c[5])
        for c in candles_1h:
            self.OHLCV_1h[symbol].add_new_OHLCV_candle(c[1], c[2], c[3], c[4], c[5])
        for c in candles_15m:
            self.OHLCV_15m[symbol].add_new_OHLCV_candle(c[1], c[2], c[3], c[4], c[5])
        # save to db....


    @in_new_thread
    def callback_for_candle_receiver(self, callback_data: CandleCallback):
        if callback_data.interval=='15m':
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
        self._calc_all_indicators(callback_data.symbol, callback_data.interval)