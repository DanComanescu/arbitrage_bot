# exchanges/kraken.py

import ccxt

def create_kraken_client(cfg: dict) -> ccxt.kraken:
    """
    Create a Kraken Derivatives (Futures) client.
    Expects cfg keys:
      - apiKey, secret
      - sandbox: bool
    """
    exchange = ccxt.kraken({
        'apiKey': cfg['apiKey'],
        'secret': cfg['secret'],
        'enableRateLimit': True
    })
    if cfg.get('sandbox', False):
        # Kraken derivatives demo endpoint
        exchange.urls['api'] = 'https://demo-futures.kraken.com/derivatives/api/v3'
    return exchange