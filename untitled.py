import requests
import time
import threading
import json
p = {'http':'http://1.0.0.151:80'}
t = time.time()

def in_new_thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

@in_new_thread
def r():
	print(requests.get('https://api.binance.com/api/v1/klines?symbol=BTCUSDT&interval=1m', proxies=p).text)

'''for _ in range(100):
	r()'''
print(json.loads(requests.get('https://api.binance.com/api/v1/klines?symbol={}&interval=1h&limit=2'.format('BTCUSDT')).text)[-1])