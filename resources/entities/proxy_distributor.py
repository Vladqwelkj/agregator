import requests
import time

class ProxyDistributor:
	'''Предоставляет прокси.
	При каждом новом запросе на получение прокси отдается следующий прокси в списке.
	Если список закончился - начать отдавать с первого прокси (бесконечная очередь)'''
	def __init__(self, proxies: list):
		self.n = 0
		self.available = True
		self.proxies = list()
		self._validate_and_add(proxies)


	def _validate_and_add(self, proxies):
		for p in proxies:
			try:
				resp = requests.get('https://api.binance.com/api/v3/ping', proxies=p)
			except Exception as e:
				print(p, e)
				continue
			if resp.status_code==200:
				print('proxy OK', p['https'] if p else '(without proxy)')
				self.proxies.append(p)


	def get_proxy(self):
		while True:
			if self.available:
				self.available = False
				if self.n==len(self.proxies):
					self.n = 0
				out = self.proxies[self.n]
				self.n += 1
				self.available = True
				return out
			time.sleep(0.01)

