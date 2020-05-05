import numpy as np
import pandas


def calc_last_RSI(source_prices, n):
    print(source_prices)
    #source_prices = source_prices.reverse()
    src = pandas.Series(source_prices)
    # Get the difference in price from previous step
    delta = src.diff()
    # Get rid of the first row, which is NaN since it did not have a previous 
    # row to calculate the differences
    delta = delta[1:] 
    # Make the positive gains (up) and negative gains (down) Series
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    # Calculate the EWMA
    roll_up1 = up.ewm(span=n, min_periods=0,adjust=False,ignore_na=False).mean()
    roll_down1 = down.abs().ewm(span=n, min_periods=0,adjust=False,ignore_na=False).mean()

    # Calculate the RSI based on EWMA
    RS1 = roll_up1 / roll_down1
    RSI1 = 100.0 - (100.0 / (1.0 + RS1))

    return RSI1.tolist()[-1]



def calc_bbands(source_prices, std, sma_period):
    df = pandas.DataFrame({
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