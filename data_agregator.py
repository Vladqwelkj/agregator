class DataAgregator:
    def __init__(self, client, symbol):
        self.client = client
        self.symbol = symbol


    @in_new_thread
    def get_initial_candles(self):
        self.candles_1d = client.get_historical_klines(
            self.symbol,
            '1d',
            start_str='30 day ago')[:-1]
        self.candles_1h = client.get_historical_klines(
            self.symbol,
            '1h',
            start_str='2 day ago')[:-1]
        self.candles_15m = client.get_historical_klines(
            self.symbol,
            '1d',
            start_str='12 hour ago')[:-1]