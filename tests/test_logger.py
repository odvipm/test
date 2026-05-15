import pytest
from datetime import datetime, date
from pathlib import Path


def test_write_and_read_action_entry(tmp_path, monkeypatch):
    import logger
    monkeypatch.setattr(logger, "LOG_PATH", tmp_path / "clocker.log")

    logger.write_entry("clock_in", "success", duration=3.2)
    entries = logger.read_entries()

    assert len(entries) == 1
    assert entries[0]["action"] == "clock_in"
    assert entries[0]["status"] == "success"
    assert isinstance(entries[0]["timestamp"], datetime)


def test_write_failed_entry_with_reason(tmp_path, monkeypatch):
    import logger
    monkeypatch.setattr(logger, "LOG_PATH", tmp_path / "clocker.log")

    logger.write_entry("clock_out", "failed", reason="Login timeout after 3 retries")
    entries = logger.read_entries()

    assert entries[0]["status"] == "failed"


def test_get_entries_for_date_filters_correctly(tmp_path, monkeypatch):
    import logger
    monkeypatch.setattr(logger, "LOG_PATH", tmp_path / "clocker.log")

    logger.write_entry("clock_in", "success")
    today = datetime.now().date()
    entries = logger.get_entries_for_date(today)

    assert len(entries) == 1
    assert entries[0]["action"] == "clock_in"


def test_read_entries_returns_empty_when_no_log(tmp_path, monkeypatch):
    import logger
    monkeypatch.setattr(logger, "LOG_PATH", tmp_path / "nonexistent.log")

    entries = logger.read_entries()
    assert entries == []


def test_report_entries_are_excluded_from_read_entries(tmp_path, monkeypatch):
    import logger
    monkeypatch.setattr(logger, "LOG_PATH", tmp_path / "clocker.log")

    logger.write_entry("clock_in", "success")
    logger.write_report("Some report text")
    entries = logger.read_entries()

    assert len(entries) == 1  # REPORT lines are not returned by read_entries
