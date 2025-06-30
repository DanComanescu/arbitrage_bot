# execution/trader.py

import logging
from typing import Dict, Any
import ccxt

logger = logging.getLogger(__name__)

def open_position(
    clients: Dict[str, Any],
    low_ex: str,
    high_ex: str,
    symbol: str,
    amount: float
):
    """
    Open an arbitrage position:
    - Market buy on low_ex
    - Market sell on high_ex
    """
    buy_client = clients[low_ex]
    sell_client = clients[high_ex]

    # BUY leg
    try:
        buy_client.load_markets()
    except Exception as e:
        logger.warning(f"[{low_ex}] could not load markets before buy: {e}")
    try:
        logger.info(f"PLACING MARKET BUY {amount} {symbol} on {low_ex}")
        order = buy_client.create_market_buy_order(symbol, amount)
        logger.info(f"BUY order placed on {low_ex}: {order}")
    except Exception as e:
        logger.error(f"Error placing BUY on {low_ex}: {e}")

    # SELL leg
    try:
        sell_client.load_markets()
    except Exception as e:
        logger.warning(f"[{high_ex}] could not load markets before sell: {e}")
    try:
        logger.info(f"PLACING MARKET SELL {amount} {symbol} on {high_ex}")
        order = sell_client.create_market_sell_order(symbol, amount)
        logger.info(f"SELL order placed on {high_ex}: {order}")
    except Exception as e:
        logger.error(f"Error placing SELL on {high_ex}: {e}")

def close_position(
    clients: Dict[str, Any],
    low_ex: str,
    high_ex: str,
    symbol: str,
    amount: float
):
    """
    Close the arbitrage position:
    - Market sell on low_ex (where we bought)
    - Market buy on high_ex (where we sold)
    """
    # Close SELL leg
    try:
        clients[low_ex].load_markets()
    except Exception as e:
        logger.warning(f"[{low_ex}] could not load markets before close-sell: {e}")
    try:
        logger.info(f"PLACING CLOSE MARKET SELL {amount} {symbol} on {low_ex}")
        order = clients[low_ex].create_market_sell_order(symbol, amount)
        logger.info(f"CLOSE SELL on {low_ex}: {order}")
    except Exception as e:
        logger.error(f"Error placing close SELL on {low_ex}: {e}")

    # Close BUY leg
    try:
        clients[high_ex].load_markets()
    except Exception as e:
        logger.warning(f"[{high_ex}] could not load markets before close-buy: {e}")
    try:
        logger.info(f"PLACING CLOSE MARKET BUY {amount} {symbol} on {high_ex}")
        order = clients[high_ex].create_market_buy_order(symbol, amount)
        logger.info(f"CLOSE BUY on {high_ex}: {order}")
    except Exception as e:
        logger.error(f"Error placing close BUY on {high_ex}: {e}")
