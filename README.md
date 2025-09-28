# crypto-bot

Lightweight crypto trading research sandbox built with Python, pandas, and ccxt.

## Environment setup (Windows PowerShell)

1. Install Python 3.
2. Create and activate a virtual environment.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

> `mplfinance` is included for candlestick (K-line) visualization.

## Configure API keys

Update [`config.py`](config.py:1) with your Binance API credentials. Never commit real keys to version control.

## Run a Supertrend backtest with K-line visualization

```python
import pandas as pd
from backtest import run_supertrend_backtest

# Load your OHLCV data indexed by timestamp
df = pd.read_csv(
    "your_price_data.csv",
    parse_dates=["timestamp"],
    index_col="timestamp",
)

result = run_supertrend_backtest(
    df,
    atr_period=10,
    multiplier=3.0,
    visualize=True,       # display or save the K-line chart
    output_path="kline.png",  # optional: save the figure
)
print(result.summary())
```

## Live trading experiment (optional)

The helper in [`supertrend_strategy.py`](supertrend_strategy.py:117) demonstrates how to pull data from Binance.US and act on the latest Supertrend signal. Use with caution and test thoroughly before trading real funds.