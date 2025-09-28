import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from supertrend_strategy import implement_supertrend_strategy


def backtest_supertrend(df, initial_capital=10000):
    """
    Backtest a Supertrend strategy
    :param df: Dataframe with OHLC data and signals
    :param initial_capital: Initial capital for backtest
    :return: Performance metrics
    """
    # Create a copy of the dataframe
    bt = df.copy()
    
    # Initial conditions
    bt['position'] = 0
    bt['position'] = bt['signal'].cumsum()
    bt['position'] = bt['position'].clip(lower=0, upper=1)  # Ensure we're either in or out
    
    # Calculate returns
    bt['returns'] = bt['close'].pct_change()
    bt['strategy_returns'] = bt['position'].shift(1) * bt['returns']
    
    # Calculate cumulative returns
    bt['cumulative_returns'] = (1 + bt['returns']).cumprod()
    bt['cumulative_strategy_returns'] = (1 + bt['strategy_returns']).cumprod()
    
    # Calculate drawdowns
    bt['peak'] = bt['cumulative_strategy_returns'].cummax()
    bt['drawdown'] = (bt['cumulative_strategy_returns'] - bt['peak']) / bt['peak']
    
    # Calculate metrics
    total_return = bt['cumulative_strategy_returns'].iloc[-1] - 1
    max_drawdown = bt['drawdown'].min()
    sharpe_ratio = bt['strategy_returns'].mean() / bt['strategy_returns'].std() * np.sqrt(252)  # Assuming daily data
    
    # Calculate equity
    bt['equity'] = initial_capital * bt['cumulative_strategy_returns']
    
    return {
        'dataframe': bt,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio
    }

def plot_results(results):
    """
    Plot backtest results
    :param results: Results from backtest
    """
    bt = results['dataframe']
    
    # Plot price and signals
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(bt.index, bt['close'], label='Price')
    plt.plot(bt[bt['signal'] == 1].index, bt['close'][bt['signal'] == 1], '^', markersize=10, color='g', label='Buy Signal')
    plt.plot(bt[bt['signal'] == -1].index, bt['close'][bt['signal'] == -1], 'v', markersize=10, color='r', label='Sell Signal')
    plt.title('Supertrend Strategy - Signals')
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(bt.index, bt['equity'], label='Strategy Equity')
    plt.title(f'Equity Curve (Total Return: {results["total_return"]:.2%}, Max DD: {results["max_drawdown"]:.2%}, Sharpe: {results["sharpe_ratio"]:.2f})')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

df = implement_supertrend_strategy(df, atr_period=atr_period, multiplier=multiplier)

# Example usage:
# 1. Get your price data (OHLC)
# df = pd.read_csv('your_price_data.csv')
# 
# 2. Apply the strategy
# df = implement_supertrend_strategy(df)
#
# 3. Backtest the strategy
# results = backtest_supertrend(df)
#
# 4. Plot results
# plot_results(results)