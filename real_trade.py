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