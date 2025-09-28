from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence

import pandas as pd

from data.binance_client import create_exchange

__all__ = [
    "fetch_daily_ohlcv",
    "load_recent_daily",
]


_ONE_DAY_MS = 24 * 60 * 60 * 1000
_MAX_FETCH_LIMIT = 1000  # Binance limit for a single OHLCV request


def _ensure_exchange(exchange=None):
    return exchange or create_exchange()


def _fetch_batches(
    exchange,
    symbol: str,
    timeframe: str,
    total_required: int,
    since: Optional[int] = None,
) -> List[Sequence[float]]:
    ohlcv: List[Sequence[float]] = []
    fetch_since = since
    while len(ohlcv) < total_required:
        remaining = total_required - len(ohlcv)
        fetch_limit = min(_MAX_FETCH_LIMIT, remaining)
        batch = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=fetch_since,
            limit=fetch_limit,
        )
        if not batch:
            break
        ohlcv.extend(batch)
        last_ts = batch[-1][0]
        fetch_since = last_ts + _ONE_DAY_MS
        if len(batch) < fetch_limit:
            break
    return ohlcv


def fetch_daily_ohlcv(
    symbol: str,
    *,
    days: int,
    exchange=None,
    include_symbol: bool = True,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV candles for the requested number of days (most recent first).
    """
    if days <= 0:
        raise ValueError("Parameter 'days' must be positive.")
    exchange = _ensure_exchange(exchange)
    raw_ohlcv = _fetch_batches(exchange, symbol, "1d", total_required=days)
    if not raw_ohlcv:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "is_closed"])

    df = pd.DataFrame(
        raw_ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    df = df.tail(days)

    df = df.astype(
        {
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,
        }
    )

    if include_symbol:
        df["symbol"] = symbol

    df["is_closed"] = True
    return df


def load_recent_daily(
    symbol: str,
    *,
    days: int,
    exchange=None,
    refresh_live_close: bool = True,
) -> pd.DataFrame:
    """
    Load daily OHLCV data and flag whether the latest candle is closed.
    """
    exchange = _ensure_exchange(exchange)
    df = fetch_daily_ohlcv(symbol, days=days, exchange=exchange, include_symbol=True)
    if df.empty:
        return df

    now_utc = datetime.now(timezone.utc)
    last_index = df.index[-1]
    is_today = last_index.date() == now_utc.date()
    if is_today:
        df.at[last_index, "is_closed"] = False
        if refresh_live_close:
            try:
                ticker = exchange.fetch_ticker(symbol)
                live_close = ticker.get("last") or ticker.get("close")
                if live_close is not None:
                    df.at[last_index, "close"] = float(live_close)
            except Exception:
                # Non-fatal; keep existing close value
                pass
    else:
        if last_index + timedelta(days=1) <= now_utc.replace(hour=0, minute=0, second=0, microsecond=0):
            df.at[last_index, "is_closed"] = True

    return df