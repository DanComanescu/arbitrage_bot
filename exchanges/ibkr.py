# exchanges/ibkr.py

from ib_insync import IB

def create_ibkr_client(cfg: dict) -> IB:
    ib = IB()
    host = cfg.get('host', '127.0.0.1')
    # Use port 4002 for IB Gateway paper trading (per your API settings)
    port = cfg.get('port', 4002)
    client_id = cfg.get('clientId', 1)
    # If you enabled Read-Only in API settings, add readonly=True
    ib.connect(host, port, client_id, readonly=cfg.get('readonly', False))
    return ib