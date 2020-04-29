from binance.websockets import BinanceSocketManager

class CandlesReceiver:
    def __init__(self, client, symbol, interval):
        self.bm = BinanceSocketManager(client)
        self._callbacks = [] 

    def start(self):
        bm.start_kline_socket(symbol, self._callback_when_candle_receive, interval=interval)

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def _callback_when_candle_receive(self, msg):
        if msg['k']['x']: # Если свеча закрылась
            for callback in self._callbacks:
                callback(msg)

                

