import ccxt

def create_binance_client(cfg: dict) -> ccxt.binance:
    """
    Create a Binance Spot client that:
    - Only calls the public ticker endpoint
    - Never loads markets or currencies (avoids margin/allPairs and exchangeInfo)
    """
    exchange = ccxt.binance({
        'apiKey':          cfg['apiKey'],
        'secret':          cfg['secret'],
        'enableRateLimit': True,
    })
    # Override methods that fetch markets or currencies
    exchange.load_markets = lambda *args, **kwargs: {}
    exchange.fetch_currencies = lambda *args, **kwargs: {}
    return exchange
