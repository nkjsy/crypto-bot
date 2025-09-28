import pandas as pd
import numpy as np
import ccxt
import config
from datetime import datetime

# Initialize Binance.US exchange using ccxt
exchange = ccxt.binanceus({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY
})


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
    atr = true_range.ewm(alpha=1/atr_period, min_periods=atr_period).mean()
    
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
    df.loc[df['supertrend'] & ~df['supertrend'].shift(1), 'signal'] = 1  # Buy signal
    df.loc[~df['supertrend'] & df['supertrend'].shift(1), 'signal'] = -1  # Sell signal
    
    return df

def execute_trade_from_signal(df, symbol, order_size):
    """
    Place real orders on Binance based on the most recent Supertrend signal.
    signal == 1 -> market buy; signal == -1 -> market sell
    """
    last_signal = int(df.iloc[-1]["signal"])
    if last_signal == 1:
        try:
            order = exchange.create_market_buy_order(symbol, order_size)
            print(f"BUY placed: {order}")
            in_position = True
        except Exception as e:
            print(f"BUY failed: {e}")

    elif last_signal == -1:
        try:
            order = exchange.create_market_sell_order(symbol, order_size)
            print(f"SELL placed: {order}")
            in_position = False
        except Exception as e:
            print(f"SELL failed: {e}")

def run_bot():
    symbol = 'ETH/USDT'
    timeframe = '1m'
    limit = 200
    atr_period = 10
    multiplier = 3.0
    order_size = 0.05

    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    # Exclude the most recent still-forming candle
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Compute signals
    df = implement_supertrend_signals(df, atr_period, multiplier)

    # Execute live order based on latest signal
    execute_trade_from_signal(df, symbol=symbol, order_size=order_size)