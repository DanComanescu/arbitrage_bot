# strategies/spread_strategy.py

import asyncio
from typing import Dict, Callable, Any
import requests
import logging

logger = logging.getLogger(__name__)

async def fetch_price(exchange: Any, symbol: str) -> float:
    """
    Fetch the latest price for `symbol`:
    - For Binance: direct REST on mainnet
    - For Bybit: direct REST on testnet (v5 endpoint)
    - Otherwise: CCXT fetch_ticker in a thread
    """
    loop = asyncio.get_running_loop()
    pair = symbol.replace('/', '')

    # 1) Binance via public REST
    if getattr(exchange, 'id', None) == 'binance':
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={pair}'
        try:
            resp = await loop.run_in_executor(None, lambda: requests.get(url, timeout=5))
            resp.raise_for_status()
            return float(resp.json()['price'])
        except Exception as e:
            logger.warning(f"[binance direct] error fetching {symbol}: {e}")
            raise

    # 2) Bybit Testnet via public REST (v5)
    elif getattr(exchange, 'id', None) == 'bybit':
        url = f'https://api-testnet.bybit.com/v5/market/tickers?symbol={pair}&category=spot'
        try:
            resp = await loop.run_in_executor(None, lambda: requests.get(url, timeout=5))
            resp.raise_for_status()
            data = resp.json()
            if int(data.get('retCode', -1)) != 0:
                raise Exception(f"Bybit API error retCode={data.get('retCode')}")
            items = data.get('result', {}).get('list') or []
            if not items or 'lastPrice' not in items[0]:
                raise Exception("Bybit API returned unexpected structure")
            return float(items[0]['lastPrice'])
        except Exception as e:
            logger.warning(f"[bybit direct] error fetching {symbol}: {e}")
            raise

    # 3) Fallback: CCXT for any others
    else:
        try:
            ticker = await loop.run_in_executor(None, lambda: exchange.fetch_ticker(symbol))
            return ticker['last']
        except Exception as e:
            eid = getattr(exchange, 'id', 'unknown')
            logger.warning(f"[{eid}] error fetching {symbol}: {e}")
            raise

async def monitor_spread(
    clients: Dict[str, Any],
    symbol: str,
    threshold_open: float,
    threshold_close: float,
    on_open: Callable[[str, str, float], None],
    on_close: Callable[[str, str, float], None],
    poll_interval: float = 1.0
):
    """
    Continuously monitor the spread between two exchanges and trigger callbacks.
    """
    ex1_name, ex2_name = list(clients)[:2]
    ex1, ex2 = clients[ex1_name], clients[ex2_name]

    position_open = False

    while True:
        try:
            task1 = asyncio.create_task(fetch_price(ex1, symbol))
            task2 = asyncio.create_task(fetch_price(ex2, symbol))
            price1, price2 = await asyncio.gather(task1, task2)
        except Exception:
            await asyncio.sleep(poll_interval)
            continue

        spread = (price2 - price1) / price1 * 100

        if not position_open and abs(spread) >= threshold_open:
            low, high = (ex1_name, ex2_name) if spread > 0 else (ex2_name, ex1_name)
            on_open(low, high, spread)
            position_open = True

        elif position_open and abs(spread) <= threshold_close:
            on_close(ex1_name, ex2_name, spread)
            position_open = False

        await asyncio.sleep(poll_interval)
