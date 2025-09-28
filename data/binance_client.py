import logging
from typing import Optional

import ccxt

import config

logger = logging.getLogger(__name__)

_exchange: Optional[ccxt.binance] = None


def create_exchange(force_refresh: bool = False, public: bool = True) -> ccxt.binance:
    """
    Instantiate (or reuse) a configured ccxt binance exchange client.

    Credentials are read directly from the config module, if use private API.
    """
    global _exchange

    if _exchange is not None and not force_refresh:
        return _exchange

    if not public:
        exchange = ccxt.binance(
            {
                "apiKey": getattr(config, "BINANCE_API_KEY", "") or "",
                "secret": getattr(config, "BINANCE_SECRET_KEY", "") or "",
                "enableRateLimit": True,
                "timeout": 10_000,
                "options": {
                    "adjustForTimeDifference": True,
                },
            }
        )

        try:
            if exchange.check_required_credentials():
                logger.info("Binance credentials loaded from config.")
            exchange.fetch_time()
        except ccxt.BaseError as exc:
            logger.warning("Binance connectivity check failed: %s", exc)
            raise

        _exchange = exchange
        return _exchange
    else:
        exchange = ccxt.binance(
            # {
            #     "enableRateLimit": True,
            #     "timeout": 10_000,
            #     "options": {
            #         "adjustForTimeDifference": True,
            #     },
            # }
        )

        try:
            exchange.fetch_time()
        except ccxt.BaseError as exc:
            logger.warning("Binance connectivity check failed: %s", exc)
            raise

        _exchange = exchange
        return _exchange