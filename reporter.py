from datetime import datetime, timedelta
from typing import Optional

import pytz

import logger
from config import load_config


def _today(tz: pytz.BaseTzInfo) -> "datetime.date":
    return datetime.now(tz).date()


def get_previous_workday(today: "datetime.date", workdays: list[str]) -> Optional["datetime.date"]:
    candidate = today - timedelta(days=1)
    for _ in range(7):
        if candidate.strftime("%A") in workdays:
            return candidate
        candidate -= timedelta(days=1)
    return None


def _workdays_in_range(start: "datetime.date", end: "datetime.date", workdays: list[str]) -> list:
    days, current = [], start
    while current <= end:
        if current.strftime("%A") in workdays:
            days.append(current)
        current += timedelta(days=1)
    return days


def check_missed_runs() -> list[str]:
    config = load_config()
    tz = pytz.timezone(config["timezone"])
    today = _today(tz)
    prev = get_previous_workday(today, config["workdays"])
    if prev is None:
        return []

    entries = logger.read_entries()
    missed = []
    for action in ("clock_in", "clock_out"):
        has_entry = any(
            e["timestamp"].date() == prev and e["action"] == action and e["status"] == "success"
            for e in entries
        )
        if not has_entry:
            msg = f"{action} MISSED on {prev} (no record found — laptop was likely off or disconnected)"
            logger.write_report(msg)
            missed.append(msg)
    return missed


def generate_report() -> str:
    config = load_config()
    tz = pytz.timezone(config["timezone"])
    today = _today(tz)
    start = today - timedelta(days=6)
    days = _workdays_in_range(start, today, config["workdays"])
    entries = logger.read_entries()

    lines = [f"Week summary ({start.strftime('%b')} {start.day} – {today.strftime('%b')} {today.day}):"]
    for day in days:
        ci = next(
            (e for e in entries if e["timestamp"].date() == day and e["action"] == "clock_in" and e["status"] == "success"),
            None,
        )
        co = next(
            (e for e in entries if e["timestamp"].date() == day and e["action"] == "clock_out" and e["status"] == "success"),
            None,
        )
        ci_str = f"✓ Clocked in {ci['timestamp'].strftime('%H:%M')}" if ci else "✗ Clock-in MISSED"
        if day == today:
            co_str = f"✓ Clocked out {co['timestamp'].strftime('%H:%M')}" if co else "— (pending)"
        else:
            co_str = f"✓ Clocked out {co['timestamp'].strftime('%H:%M')}" if co else "✗ Clock-out MISSED"
        lines.append(f"  {day.strftime('%a %b')} {day.day}  {ci_str}  {co_str}")

    return "\n".join(lines)
