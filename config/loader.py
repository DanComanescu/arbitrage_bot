# config/loader.py

import yaml
import os
from pathlib import Path

def load_exchanges_config(path: str = None) -> dict:
    """
    Load exchanges configuration from a YAML file.

    Args:
        path: Optional path to exchanges.yaml. Defaults to config/exchanges.yaml.

    Returns:
        A dict mapping exchange keys to config dicts.
    """
    config_path = Path(path or Path(__file__).parent / "exchanges.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Optionally override with environment variables
    for key, conf in cfg.items():
        env_api = os.getenv(f"{key.upper()}_APIKEY")
        env_secret = os.getenv(f"{key.upper()}_SECRET")
        if env_api:
            conf["apiKey"] = env_api
        if env_secret:
            conf["secret"] = env_secret

    return cfg