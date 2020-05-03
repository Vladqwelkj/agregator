import pandas
import matplotlib.pyplot as plt
from binance.client import Client
c = Client('', '').get_historical_klines('BTCUSDT', '1d', start_str='200 day ago')
print(c)
# Window length for moving average
window_length = 14

x = [1, 2, 3,2,3,4,5,3,4,3,5,3,6,7,8,7,6,8,9,10,9,12]

close = pandas.Series([float(v[4]) for v in c])
# Get the difference in price from previous step
delta = close.diff()
# Get rid of the first row, which is NaN since it did not have a previous 
# row to calculate the differences
delta = delta[1:] 

# Make the positive gains (up) and negative gains (down) Series
up, down = delta.copy(), delta.copy()
up[up < 0] = 0
down[down > 0] = 0

# Calculate the EWMA
roll_up1 = up.ewm(span=window_length, min_periods=0,adjust=False,ignore_na=False).mean()
roll_down1 = down.abs().ewm(span=window_length, min_periods=0,adjust=False,ignore_na=False).mean()

# Calculate the RSI based on EWMA
RS1 = roll_up1 / roll_down1
RSI1 = 100.0 - (100.0 / (1.0 + RS1))

plt.figure()
RSI1.plot()
plt.show()