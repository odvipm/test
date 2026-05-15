import json
import os
from pathlib import Path

import keyring

_SERVICE = "SproutAutoClocker"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"


def save_credentials(username: str, password: str) -> None:
    try:
        keyring.set_password(_SERVICE, "username", username)
        keyring.set_password(_SERVICE, "password", password)
    except Exception:
        _write_credentials_file(username, password)


def get_credentials() -> tuple[str, str]:
    try:
        username = keyring.get_password(_SERVICE, "username")
        password = keyring.get_password(_SERVICE, "password")
        if username and password:
            return username, password
    except Exception:
        pass
    return _read_credentials_file()


def _write_credentials_file(username: str, password: str) -> None:
    CREDENTIALS_PATH.write_text(json.dumps({"username": username, "password": password}))
    os.chmod(CREDENTIALS_PATH, 0o600)


def _read_credentials_file() -> tuple[str, str]:
    if not CREDENTIALS_PATH.exists():
        raise RuntimeError(
            "No credentials found. Run: python clocker.py --setup"
        )
    data = json.loads(CREDENTIALS_PATH.read_text())
    return data["username"], data["password"]
