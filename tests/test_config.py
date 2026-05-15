import json
import pytest
from pathlib import Path


def test_load_config_returns_all_keys(tmp_path, monkeypatch):
    cfg = {
        "sprout_url": "https://example.sprout.ph",
        "clock_in_time": "09:00",
        "clock_out_time": "18:00",
        "workdays": ["Monday", "Friday"],
        "timezone": "Asia/Manila",
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(cfg))
    monkeypatch.setattr("config.CONFIG_PATH", config_file)

    from config import load_config
    result = load_config()
    assert result["clock_in_time"] == "09:00"
    assert result["workdays"] == ["Monday", "Friday"]


def test_load_config_raises_on_missing_key(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"sprout_url": "https://x.com"}))
    monkeypatch.setattr("config.CONFIG_PATH", config_file)

    from config import load_config
    with pytest.raises(ValueError, match="Missing config keys"):
        load_config()


def test_load_config_raises_on_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("config.CONFIG_PATH", tmp_path / "nonexistent.json")

    from config import load_config
    with pytest.raises(FileNotFoundError):
        load_config()
