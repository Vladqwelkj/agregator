class Candle:
	def __init__(self, symbol, interval, O, H, L, C, volume):
		self.symbol = symbol
		self.interval = interval
		self.O = float(O)
		self.H = float(H)
		self.L = float(L)
		self.C = float(C)
		self.volume = float(volume)
		