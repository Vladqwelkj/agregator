class OHLCV_candles:
	def __init__(self, ):
		self.O = list()
		self.H = list()
		self.L = list()
		self.C = list()
		self.volume = list()

	def add_new_OHLCV_candle(self, O, H, L, C, volume):
		self.O.append(float(O))
		self.H.append(float(H))
		self.L.append(float(L))
		self.C.append(float(C))
		self.volume.append(float(volume))
		self._delete_first_candle()

	def _delete_first_candle(self):
		for lst in [self.O, self.H, self.L, self.C, self.volume]:
			del lst[0]