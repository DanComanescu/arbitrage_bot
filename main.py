"""
main.py
--------
Entry-point for the arbitrage bot.

• Configures logging (DEBUG heart-beats)  
• Loads exchange configs & instantiates Binance + Bybit clients  
• Pre-loads CCXT markets so order-calls won’t block  
• Starts the asynchronous spread-monitor
"""

import asyncio
import logging

# ─── Global logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("ccxt").setLevel(logging.WARNING)

from config.settings  import LOGGER_NAME
from config.loader    import load_exchanges_config
from utils.logger     import get_logger

from exchanges.binance import create_binance_client
from exchanges.bybit   import create_bybit_client

from strategies.spread_strategy import monitor_spread
from execution.trader           import open_position, close_position

EXCHANGE_FACTORIES = {
    "binance": create_binance_client,
    "bybit":   create_bybit_client,
    # add "coinbase": create_coinbase_client later if you like
}

TRADE_AMOUNT = 0.001  # BTC per leg

# ─── Callback hooks ──────────────────────────────────────────────────────────
def on_open(low_ex: str, high_ex: str, spread: float):
    logger.info(f"OPEN ▸ buy on {low_ex}, sell on {high_ex}  (spread={spread:.2f} %)")
    open_position(clients, low_ex, high_ex, "BTC/USDT", TRADE_AMOUNT)

def on_close(low_ex: str, high_ex: str, spread: float):
    logger.info(f"CLOSE ▸ exiting {low_ex}/{high_ex}  (spread {spread:.2f} %)")
    close_position(clients, low_ex, high_ex, "BTC/USDT", TRADE_AMOUNT)

# ─── Main routine ────────────────────────────────────────────────────────────
def main() -> None:
    global logger, clients
    logger = get_logger(LOGGER_NAME)
    logger.info("Starting arbitrage bot")

    # 1) read config ----------------------------------------------------------
    try:
        cfg = load_exchanges_config()
        logger.info(f"Configs found: {list(cfg)}")
    except Exception as exc:
        logger.error(f"Failed to load configs: {exc}")
        return

    # 2) spin-up exchange clients --------------------------------------------
    clients = {}
    for name in ("binance", "bybit"):
        if name not in cfg:
            logger.warning(f"No config for {name}, skip")
            continue
        try:
            clients[name] = EXCHANGE_FACTORIES[name](cfg[name])
            logger.info(f"Client ready → {name}")
        except Exception as exc:
            logger.error(f"{name} init failed: {exc}")

    if len(clients) < 2:
        logger.error("Need at least two exchanges, aborting.")
        return

    # 3) pre-load markets so CCXT orders work ---------------------------------
    for n, c in clients.items():
        try:
            c.load_markets()
            logger.info(f"Markets loaded for {n}")
        except Exception as exc:
            logger.warning(f"Couldn’t load markets for {n}: {exc}")

    # 4) fire-up spread monitor ----------------------------------------------
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        monitor_spread(
            clients         = clients,
            symbol          = "BTC/USDT",
            threshold_open  = 0.2,     # open ≥ 0 .2 %
            threshold_close = 0.1,     # close ≤ 0 .1 %
            on_open         = on_open,
            on_close        = on_close,
            poll_interval   = 1.0,     # seconds
        )
    )

if __name__ == "__main__":
    main()
