from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pytz

import logger
from config import load_config

REPORT_HTML_PATH = Path(__file__).parent / "report.html"


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


def generate_report_html() -> Path:
    config = load_config()
    tz = pytz.timezone(config["timezone"])
    today = _today(tz)
    start = today - timedelta(days=6)
    days = _workdays_in_range(start, today, config["workdays"])
    entries = logger.read_entries()
    generated = datetime.now(tz).strftime("%A, %B %d %Y %I:%M %p")

    rows = []
    for day in days:
        ci = next(
            (e for e in entries if e["timestamp"].date() == day and e["action"] == "clock_in" and e["status"] == "success"),
            None,
        )
        co = next(
            (e for e in entries if e["timestamp"].date() == day and e["action"] == "clock_out" and e["status"] == "success"),
            None,
        )
        ci_str = f'<span class="ok">✓ {ci["timestamp"].strftime("%H:%M")}</span>' if ci else '<span class="missed">✗ MISSED</span>'
        if day == today:
            co_str = f'<span class="ok">✓ {co["timestamp"].strftime("%H:%M")}</span>' if co else '<span class="pending">— pending</span>'
        else:
            co_str = f'<span class="ok">✓ {co["timestamp"].strftime("%H:%M")}</span>' if co else '<span class="missed">✗ MISSED</span>'
        rows.append(f"<tr><td>{day.strftime('%a, %b %d')}</td><td>{ci_str}</td><td>{co_str}</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sprout Attendance</title>
<style>
  body {{ font-family: Segoe UI, Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 40px; }}
  .card {{ background: white; max-width: 520px; margin: auto; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.1); padding: 32px; }}
  h2 {{ margin: 0 0 4px; font-size: 20px; color: #1a1a2e; }}
  .sub {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; color: #888; font-size: 12px; text-transform: uppercase; padding: 8px 10px; border-bottom: 2px solid #eee; }}
  td {{ padding: 12px 10px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
  tr:last-child td {{ border-bottom: none; }}
  .ok {{ color: #22a06b; font-weight: 600; }}
  .missed {{ color: #e5484d; font-weight: 600; }}
  .pending {{ color: #aaa; }}
</style>
</head>
<body>
<div class="card">
  <h2>Sprout Attendance</h2>
  <div class="sub">Generated {generated}</div>
  <table>
    <tr><th>Day</th><th>Clock In</th><th>Clock Out</th></tr>
    {"".join(rows)}
  </table>
</div>
</body>
</html>"""

    REPORT_HTML_PATH.write_text(html, encoding="utf-8")
    return REPORT_HTML_PATH
