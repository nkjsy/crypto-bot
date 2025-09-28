import pandas as pd
import numpy as np
import ccxt
import config
from datetime import datetime


def calculate_supertrend(df, atr_period=10, multiplier=3.0):
    """
    Calculate Supertrend for a dataframe
    :param df: Dataframe with high, low, close columns
    :param atr_period: Period for ATR calculation
    :param multiplier: Multiplier for ATR
    :return: Dataframe with Supertrend columns
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # Calculate ATR
    atr = true_range.rolling(atr_period).mean()
    # atr = true_range.ewm(alpha=1/atr_period, min_periods=atr_period).mean()
    
    # Calculate Upper and Lower Bands
    hl2 = (high + low) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    # Initialize Supertrend
    supertrend = [True] * len(df)
    uband = [0.0] * len(df)
    lband = [0.0] * len(df)
    
    # Calculate final upper and lower bands
    for i in range(1, len(df)):
        if close.iloc[i] > uband[i-1]:
            supertrend[i] = True
        elif close.iloc[i] < lband[i-1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i-1]
            
            if supertrend[i] and lowerband.iloc[i] > lband[i-1]:
                lband[i] = lowerband.iloc[i]
            else:
                lband[i] = lband[i-1]
                
            if not supertrend[i] and upperband.iloc[i] < uband[i-1]:
                uband[i] = upperband.iloc[i]
            else:
                uband[i] = uband[i-1]
        
        # Update bands based on supertrend
        if supertrend[i]:
            uband[i] = upperband.iloc[i]
        else:
            lband[i] = lowerband.iloc[i]
            
    return pd.DataFrame({
        'supertrend': supertrend,
        'uband': uband,
        'lband': lband
    }, index=df.index)

# Compute signals
def implement_supertrend_signals(df, atr_period=10, multiplier=3.0):
    """
    Implement a trading strategy based on Supertrend
    :param df: Dataframe with OHLC data
    :param atr_period: Period for ATR calculation
    :param multiplier: Multiplier for ATR
    :return: Dataframe with signals
    """
    st = calculate_supertrend(df, atr_period, multiplier)
    df = df.join(st)
    
    # Create signals
    df['signal'] = 0
    df.loc[df['supertrend'] & ~df['supertrend'].shift(1, fill_value=False), 'signal'] = 1  # Buy signal
    df.loc[~df['supertrend'] & df['supertrend'].shift(1, fill_value=False), 'signal'] = -1  # Sell signal
    
    return df
