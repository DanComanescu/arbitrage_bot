# exchanges/alpaca.py

import ccxt

def create_alpaca_client(cfg: dict) -> ccxt.alpaca:
    """
    Create an Alpaca client for stock/crypto.
    Expects cfg keys:
      - apiKey, secret
      - sandbox: bool
      - baseUrl: URL string for live or paper
    """
    exchange = ccxt.alpaca({
        'apiKey': cfg['apiKey'],
        'secret': cfg['secret'],
        'enableRateLimit': True,
        'urls': {
            'api': cfg.get('baseUrl', 'https://api.alpaca.markets')
        }
    })
    # no explicit sandbox mode in CCXT for Alpaca — baseUrl covers it
    return exchange