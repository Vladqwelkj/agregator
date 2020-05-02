from ..utils import in_new_thread, write_log
import time
import os
import shutil
import time

from resources.entities.candle_callback import Candle



class DataSaver:
    def __init__(self, symbols):
        self.symbols = symbols
        self.main_path = 'datasets'
        self._delete_main_folder()
        time.sleep(0.5)
        self._generate_folders()


    def delete_symbol(self, symbol):
        shutil.rmtree(self.main_path+'/'+symbol+'/')


    def _delete_main_folder(self):
        try:
            shutil.rmtree(self.main_path+'/')
        except FileNotFoundError:
            pass

    def _generate_folders(self):
        os.mkdir(self.main_path)
        for symbol in self.symbols:
            os.mkdir(self.main_path+'/'+symbol)


    def _write_to_file(self, filename, symbol, line_data, rewrite=False):
        line_data = [str(v) for v in line_data]
        line_data = ' '.join(line_data)
        with open(self.main_path+'/'+symbol+'/'+filename+'.txt', 'w' if rewrite else 'a') as f:
            f.write('{} {}\n'.format(int(time.time()), line_data))


    def add_ohlcv(self, candle=Candle):
        self._write_to_file('ohlcv_'+candle.interval, candle.symbol, line_data=[
            candle.O,
            candle.H,
            candle.L,
            candle.C,
            candle.volume,
            ])


    def update_rsi(self, symbol, interval, value):
        self._write_to_file('rsi_'+interval, symbol, line_data=[round(value, 1)], rewrite=True)


    def update_rsi_1h_15m_diff(self, symbol, value):
        self._write_to_file('rsi_1h_15m_diff', symbol, line_data=[round(value, 2)], rewrite=True)


    def update_rsi_1h_15m_avg(self, symbol, value):
        self._write_to_file('rsi_1h_15m_avg', symbol, line_data=[round(value, 1)], rewrite=True)


    def update_bbands_width_15m(self, symbol, value):
        self._write_to_file('bbands_width_15m', symbol, line_data=[value,], rewrite=True)


    def update_avg_volume_10d_in_btc(self, symbol, value):
        self._write_to_file('avg_volume_10d_in_btc', symbol, line_data=[round(value, 2),], rewrite=True)