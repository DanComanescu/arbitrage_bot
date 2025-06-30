"""
main.py

Entry point for the arbitrage bot:
- Loads configuration and logger
- Instantiates exchange clients dynamically
- Loads markets for Binance & Bybit
- Starts the spread monitor on Binance and Bybit only
"""

import asyncio

from config.settings import LOGGER_NAME
from config.loader import load_exchanges_config
from utils.logger import get_logger

# Exchange factories
from exchanges.binance import create_binance_client
from exchanges.bybit import create_bybit_client
from exchanges.kraken import create_kraken_client
from exchanges.alpaca import create_alpaca_client
from exchanges.ibkr import create_ibkr_client

# Spread monitor
from strategies.spread_strategy import monitor_spread

# Order execution
from execution.trader import open_position, close_position

EXCHANGE_FACTORIES = {
    'binance': create_binance_client,
    'bybit':   create_bybit_client,
    'kraken':  create_kraken_client,
    'alpaca':  create_alpaca_client,
    'ibkr':    create_ibkr_client,
}

TRADE_AMOUNT = 0.001  # BTC per arbitrage leg, adjust as needed

def on_open(low_ex: str, high_ex: str, spread: float):
    """
    Called when the spread exceeds the open threshold.
    """
    logger.info(f"OPEN signal ➜ buy on {low_ex}, sell on {high_ex}, spread={spread:.2f}%")
    open_position(clients, low_ex, high_ex, 'BTC/USDT', TRADE_AMOUNT)

def on_close(low_ex: str, high_ex: str, spread: float):
    """
    Called when the spread falls back within the close threshold.
    """
    logger.info(f"CLOSE signal ➜ closing legs on {low_ex}/{high_ex}, spread={spread:.2f}%")
    close_position(clients, low_ex, high_ex, 'BTC/USDT', TRADE_AMOUNT)

def main():
    # Initialize logging
    global logger, clients
    logger = get_logger(LOGGER_NAME)
    logger.info("Starting arbitrage bot")

    # Load exchange configurations
    try:
        exchanges_cfg = load_exchanges_config()
        logger.info(f"Loaded exchange configs: {list(exchanges_cfg.keys())}")
    except Exception as e:
        logger.error(f"Config load failed: {e}")
        return

    # Instantiate each exchange client
    clients = {}
    for key, cfg in exchanges_cfg.items():
        factory = EXCHANGE_FACTORIES.get(key)
        if not factory:
            logger.error(f"No factory function for exchange '{key}'")
            continue
        try:
            clients[key] = factory(cfg)
            logger.info(f"Initialized client for {key}")
        except Exception as e:
            logger.error(f"Failed to initialize client for {key}: {e}")

    if not clients:
        logger.error("No exchange clients initialized—exiting.")
        return

    # Restrict to Binance and Bybit for spread monitoring
    spot_clients = {
        name: clients[name]
        for name in ('binance', 'bybit')
        if name in clients
    }

    if len(spot_clients) < 2:
        logger.error("Need both Binance and Bybit clients for spot arbitrage—exiting.")
        return

    # **NEW**: Pre-load markets on both clients so CCXT can place orders later
    for name, client in spot_clients.items():
        try:
            client.load_markets()
            logger.info(f"Loaded markets for {name}")
        except Exception as e:
            logger.warning(f"Could not load markets for {name}: {e}")

    # Start the asynchronous spread monitor on just Binance & Bybit
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        monitor_spread(
            clients         = spot_clients,
            symbol          = 'BTC/USDT',
            threshold_open  = 0.2,   # 0.2% to open
            threshold_close = 0.1,   # 0.1% to close
            on_open         = on_open,
            on_close        = on_close,
            poll_interval   = 1.0    # seconds between checks
        )
    )

if __name__ == "__main__":
    main()
