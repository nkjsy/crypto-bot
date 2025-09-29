from __future__ import annotations

from typing import Optional

import mplfinance as mpf
import pandas as pd

if pd.__version__ < "1.0":
    raise ImportError("pandas >= 1.0 is required for the visualization module.")


def render_kline(
    result,
    *,
    show: bool = True,
    output_path: Optional[str] = None,
    volume: bool = False,
    style: str = "yahoo",
) -> None:
    """
    Render a K-line (candlestick) chart for a BacktestResult.

    Parameters
    ----------
    result : BacktestResult
        Output from backtesting routines containing the enriched dataframe and metadata.
    show : bool, default True
        Whether to display the chart interactively via matplotlib.
    output_path : str, optional
        If provided, the chart is saved to this location.
    volume : bool, default False
        Toggle to display the volume subplot (requires a 'volume' column).
    style : str, default "yahoo"
        mplfinance style name controlling colors and aesthetics.
    mav : int or tuple, optional
        Moving average window(s) forwarded to mplfinance.
    """
    df = result.dataframe.copy()

    required_columns = {"open", "high", "low", "close"}
    missing = required_columns - set(df.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Missing columns required for candlestick plotting: {missing_cols}")

    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_convert(None)

    add_plots = []
    if "supertrend" in df.columns:
        add_plots.append(
            mpf.make_addplot(
                df["supertrend"],
                color="dodgerblue",
                width=1.0,
                linestyle="--",
            )
        )

    if "signal" in df.columns:
        buy_points = df["close"].where(df["signal"] == 1)
        sell_points = df["close"].where(df["signal"] == -1)
        if not buy_points.dropna().empty:
            add_plots.append(
                mpf.make_addplot(
                    buy_points,
                    type="scatter",
                    markersize=100,
                    marker="^",
                    color="green",
                    label="Buy",
                )
            )
        if not sell_points.dropna().empty:
            add_plots.append(
                mpf.make_addplot(
                    sell_points,
                    type="scatter",
                    markersize=100,
                    marker="v",
                    color="red",
                    label="Sell",
                )
            )

    if hasattr(result, "equity_curve") and isinstance(result.equity_curve, pd.Series):
        equity_series = result.equity_curve.copy()
        equity_series.index = pd.to_datetime(equity_series.index)
        if getattr(equity_series.index, "tz", None) is not None:
            equity_series.index = equity_series.index.tz_convert(None)
        equity = equity_series.reindex(df.index, method="ffill")
        add_plots.append(
            mpf.make_addplot(
                equity,
                panel=1,
                color="navy",
                width=0.7,
                ylabel="Equity",
            )
        )
        panels = dict(main=0, equity=1)
    else:
        panels = dict(main=0)

    fig, axes = mpf.plot(
        df,
        type="candle",
        style=style,
        addplot=add_plots if add_plots else None,
        volume=volume and "volume" in df.columns,
        returnfig=True,
        panel_ratios=(2, 1) if len(panels) > 1 else None,
        figsize=(14, 8),
        title=f"{result.strategy_name} K-Line",
    )
    # Add legend for buy/sell markers if present on the main axis
    try:
        main_ax = axes[0] if isinstance(axes, (list, tuple)) else axes
        handles, labels = main_ax.get_legend_handles_labels()
        if labels:
            main_ax.legend(loc="best")
    except Exception:
        pass

    # Add summary text box to the plot
    metrics = result.metrics
    summary_text = (
        f"Total Return: {metrics.get('total_return', 0):.2%}\n"
        f"Max DD: {metrics.get('max_drawdown', 0):.2%}\n"
        f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f}"
    )
    fig.text(
        0.02,
        0.95,
        summary_text,
        ha="left",
        va="top",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
        transform=fig.transFigure,
    )

    if output_path:
        fig.savefig(output_path, bbox_inches="tight")

    if show:
        import matplotlib.pyplot as plt

        plt.show()
    else:
        import matplotlib.pyplot as plt

        plt.close(fig)