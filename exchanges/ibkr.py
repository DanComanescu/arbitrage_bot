# exchanges/ibkr.py
from ib_insync import IB, Crypto


def create_ibkr_client(cfg: dict) -> IB:
    """
    Connect to IB Gateway / TWS and cache a reusable Crypto contract
    for BTC-USD on the Paxos venue.
    """
    ib = IB()

    host      = cfg.get("host", "127.0.0.1")
    port      = cfg.get("port", 4002)       # 4002 = paper / Gateway default
    client_id = cfg.get("clientId", 1)

    # readonly=True lets the bot request data without trading if desired
    ib.connect(host, port, client_id, readonly=cfg.get("readonly", False))

    # ---- cache contract so we don’t re-build it on every price poll ----
    # Crypto(symbol, exchange, currency)
    ib._btc_contract = Crypto("BTC", "PAXOS", "USD")   # ✔ correct order  :contentReference[oaicite:0]{index=0}

    return ib
