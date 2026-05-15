import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch


WORKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def _monday() -> date:
    return date(2026, 5, 11)  # This is a Monday


def test_get_previous_workday_skips_weekend():
    from reporter import get_previous_workday
    monday = _monday()
    assert monday.strftime("%A") == "Monday"
    prev = get_previous_workday(monday, WORKDAYS)
    assert prev.strftime("%A") == "Friday"
    assert prev == date(2026, 5, 8)


def test_get_previous_workday_normal_weekday():
    from reporter import get_previous_workday
    wednesday = date(2026, 5, 13)
    prev = get_previous_workday(wednesday, WORKDAYS)
    assert prev == date(2026, 5, 12)


def test_check_missed_runs_flags_missing_clock_in(tmp_path, mocker):
    import logger
    mocker.patch.object(logger, "LOG_PATH", tmp_path / "clocker.log")

    config = {
        "sprout_url": "https://x.com",
        "clock_in_time": "09:00",
        "clock_out_time": "18:00",
        "workdays": WORKDAYS,
        "timezone": "Asia/Manila",
    }
    mocker.patch("reporter.load_config", return_value=config)
    # Mock "today" to Wednesday 2026-05-13 — previous workday is Tuesday 2026-05-12
    mocker.patch("reporter._today", return_value=date(2026, 5, 13))

    from reporter import check_missed_runs
    missed = check_missed_runs()
    assert any("clock_in" in m for m in missed)


def test_generate_report_includes_today(tmp_path, mocker):
    import logger
    mocker.patch.object(logger, "LOG_PATH", tmp_path / "clocker.log")
    mocker.patch("reporter.load_config", return_value={
        "sprout_url": "https://x.com",
        "clock_in_time": "09:00",
        "clock_out_time": "18:00",
        "workdays": WORKDAYS,
        "timezone": "Asia/Manila",
    })
    mocker.patch("reporter._today", return_value=date(2026, 5, 15))

    logger.write_entry("clock_in", "success")

    from reporter import generate_report
    report = generate_report()
    assert "May 15" in report
    assert "Clocked in" in report
