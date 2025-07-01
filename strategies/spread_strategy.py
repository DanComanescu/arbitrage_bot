"""
Spread-monitor logic (Binance + Bybit).
"""

import asyncio
import logging
from typing import Dict, Callable, Any
import requests

logger = logging.getLogger(__name__)

# ─── Price helpers ───────────────────────────────────────────────────────────
async def fetch_price(exchange: Any, symbol: str) -> float:
    """
    Return the latest *last* price for `symbol`.

    • Binance → REST `/api/v3/ticker/price`   
    • Bybit   → REST `/v5/market/tickers` (testnet)   
    • Anything else → `exchange.fetch_ticker`
    """
    loop = asyncio.get_running_loop()
    pair = symbol.replace("/", "")

    # Binance
    if getattr(exchange, "id", None) == "binance":
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
        res = await loop.run_in_executor(None, lambda: requests.get(url, timeout=5))
        res.raise_for_status()
        return float(res.json()["price"])

    # Bybit (test-net)
    if getattr(exchange, "id", None) == "bybit":
        url = (
            f"https://api-testnet.bybit.com/v5/market/tickers"
            f"?symbol={pair}&category=spot"
        )
        res = await loop.run_in_executor(None, lambda: requests.get(url, timeout=5))
        res.raise_for_status()
        data = res.json()
        return float(data["result"]["list"][0]["lastPrice"])

    # Fallback → ccxt
    ticker = await loop.run_in_executor(None, lambda: exchange.fetch_ticker(symbol))
    return ticker["last"]

# ─── Spread loop ─────────────────────────────────────────────────────────────
async def monitor_spread(
    clients: Dict[str, Any],
    symbol: str,
    threshold_open: float,
    threshold_close: float,
    on_open: Callable[[str, str, float], None],
    on_close: Callable[[str, str, float], None],
    poll_interval: float = 1.0,
) -> None:
    """
    Every *poll_interval* seconds:
      • fetch prices on all provided exchanges  
      • find the pair with the widest absolute % spread  
      • fire `on_open` / `on_close` when thresholds are crossed
    """
    names         = list(clients)
    position_open = False
    opened_pair   = (None, None)

    while True:
        logger.debug(f"Polling {symbol} prices on {names}…")

        # fetch concurrently
        tasks  = {n: asyncio.create_task(fetch_price(clients[n], symbol)) for n in names}
        prices = {}
        for n, t in tasks.items():
            try:
                prices[n] = await t
            except Exception as exc:
                logger.warning(f"[{n}] fetch error: {exc}")

        # need at least two valid quotes
        if len(prices) < 2:
            await asyncio.sleep(poll_interval)
            continue

        # locate max spread
        best_pair, best_spread = None, 0.0
        for ex1, p1 in prices.items():
            for ex2, p2 in prices.items():
                if ex1 == ex2:
                    continue
                spread = (p2 - p1) / p1 * 100
                if abs(spread) > abs(best_spread):
                    best_pair, best_spread = (ex1, ex2), spread

        low, high = best_pair
        logger.debug(f"Best spread: {low} vs {high} = {best_spread:.4f}%")

        if not position_open and abs(best_spread) >= threshold_open:
            on_open(low, high, best_spread)
            position_open, opened_pair = True, best_pair

        elif position_open and abs(best_spread) <= threshold_close:
            on_close(*opened_pair, best_spread)
            position_open = False

        await asyncio.sleep(poll_interval)
