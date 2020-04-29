import numpy as np
import pandas as pd


def calc_RSI(source_prices, n):
    deltas = np.diff(source_prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(source_prices)
    rsi[:n] = 100. - 100./(1.+rs)
    for i in range(n, len(source_prices)):
        delta = deltas[i-1] # cause the diff is 1 shorter
        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(n-1) + upval)/n
        down = (down*(n-1) + downval)/n
        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)
    return rsi


def calc_bbands(source_prices, std, sma_period):
    df = pd.DataFrame({
        'price': source_prices
        })
    #Calculate rolling mean and standard deviation using number of days set above
    rolling_mean = df.rolling(sma_period).mean()
    rolling_std = df.rolling(sma_period).std()
    #create two new DataFrame columns to hold values of upper and lower Bollinger bands
    middle = [x[0] for x in rolling_mean.values.tolist()]
    upper = [x[0] for x in (rolling_mean + (rolling_std * std)).values.tolist()]
    lower = [x[0] for x in (rolling_mean - (rolling_std * std)).values.tolist()]
    return {'source_prices': source_prices[sma_period:],
        'lower': lower[sma_period:],
        'middle': middle[sma_period:], 
        'upper': upper[sma_period:],
    }


def calc_last_bbands_width(source_prices, std, sma_period):
    bbands = calc_bbands(source_prices, std, sma_period)
    last_lower = bbands['lower'][-1]
    last_middle = bbands['middle'][-1]
    last_upper = bbands['upper'][-1]
    return (last_upper - last_lower)/last_middle