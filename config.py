import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
_REQUIRED_KEYS = {"sprout_url", "clock_in_time", "clock_out_time", "workdays", "timezone"}


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    missing = _REQUIRED_KEYS - config.keys()
    if missing:
        raise ValueError(f"Missing config keys: {missing}")
    return config
