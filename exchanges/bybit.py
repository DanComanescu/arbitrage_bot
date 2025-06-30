# exchanges/bybit.py

import time
import hmac
import hashlib
import requests

class BybitRestClient:
    """
    Minimal Bybit Demo Trading client using direct HTTP.
    Provides:
      - fetch_ticker(symbol)
      - load_markets() (no-op)
      - create_market_buy_order(symbol, amount)
      - create_market_sell_order(symbol, amount)
    """
    def __init__(self, apiKey: str, secret: str):
        self.apiKey = apiKey
        self.secret = secret
        self.base = 'https://api-demo.bybit.com'

    def load_markets(self):
        # no-op so CCXT-style calls won't fail
        return {}

    def fetch_ticker(self, symbol: str) -> dict:
        pair = symbol.replace('/', '')
        url = f'{self.base}/v5/market/tickers'
        params = {'symbol': pair, 'category': 'spot'}
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if int(data.get('retCode', -1)) != 0:
            raise Exception(f"Bybit ticker error retCode={data.get('retCode')}")
        price = float(data['result']['list'][0]['lastPrice'])
        return {'last': price}

    def _sign(self, recvWindow: int = 5000) -> dict:
        ts = str(int(time.time() * 1000))
        payload = ts + self.apiKey + str(recvWindow)
        signature = hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return {'X-BAPI-API-KEY': self.apiKey,
                'X-BAPI-TIMESTAMP': ts,
                'X-BAPI-RECV-WINDOW': str(recvWindow),
                'X-BAPI-SIGN': signature,
                'Content-Type': 'application/json'}

    def create_market_buy_order(self, symbol: str, amount: float) -> dict:
        return self._place_order(symbol, amount, 'Buy')

    def create_market_sell_order(self, symbol: str, amount: float) -> dict:
        return self._place_order(symbol, amount, 'Sell')

    def _place_order(self, symbol: str, amount: float, side: str) -> dict:
        pair = symbol.replace('/', '')
        url = f'{self.base}/v5/order/create'
        body = {
            "category": "spot",
            "symbol": pair,
            "side": side,
            "orderType": "Market",
            "qty": str(amount),
            "timeInForce": "GTC"
        }
        headers = self._sign()
        resp = requests.post(url, json=body, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if int(data.get('retCode', -1)) != 0:
            raise Exception(f"Bybit order error: retCode={data.get('retCode')}, msg={data.get('retMsg')}")
        return data['result']

def create_bybit_client(cfg: dict) -> BybitRestClient:
    return BybitRestClient(cfg['apiKey'], cfg['secret'])
