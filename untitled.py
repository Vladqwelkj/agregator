import requests
import time
import threading
import json
p = {'http':'http://167.71.5.83:8080'}
p2 = {'http':'http://95.141.193.14:80'}
p3 = {'http':'http://194.79.56.6:80'}
pr = [{
		'http':'http://54.37.131.45:3128',
		'https':'https://54.37.131.45:3128'},

		None]
t = time.time()

def in_new_thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper


class Proxy:
	n = 0
	available = True
	def get_proxy(self):
		while True:
			if self.available:
				self.available = False
				if self.n==len(pr):
					self.n = 0
				out = pr[self.n]
				self.n += 1
				self.available = True
				return out
			time.sleep(0.001)


proxy = Proxy()

candles = []
@in_new_thread
def r(n):

	r = requests.get('https://api.binance.com/api/v1/klines?symbol=BTCUSDT&interval=1m&limit=40', proxies=proxy.get_proxy()).text
	#r = requests.get('https://api.binance.com/api/v1/klines?symbol=BTCUSDT&interval=1m', proxies=p2).text
	print(r[:100])
	candles.append(r)

	#print(r)

N = 2300
for n in range(N):
	r(n)
while len(candles)<N:
	time.sleep(0.05)
print(time.time() - t)
#print(json.loads(requests.get('https://api.binance.com/api/v1/klines?symbol={}&interval=1h&limit=2'.format('BTCUSDT')).text)[-1])