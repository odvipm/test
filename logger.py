import re
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent / "logs" / "clocker.log"

_ENTRY_PATTERN = re.compile(
    r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] ACTION: (\w+) \| STATUS: (\w+)'
)


def write_entry(action: str, status: str, reason: str = "", duration: float = 0.0) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"ACTION: {action}", f"STATUS: {status}"]
    if duration:
        parts.append(f"Duration: {duration:.1f}s")
    if reason:
        parts.append(f"Reason: {reason}")
    line = f"[{ts}] {' | '.join(parts)}\n"
    with open(LOG_PATH, "a") as f:
        f.write(line)


def write_report(text: str) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{ts}] REPORT: {text}\n")


def read_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    entries = []
    with open(LOG_PATH) as f:
        for line in f:
            m = _ENTRY_PATTERN.search(line)
            if m:
                entries.append({
                    "timestamp": datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"),
                    "action": m.group(2),
                    "status": m.group(3),
                })
    return entries


def get_entries_for_date(target: "datetime.date") -> list[dict]:
    return [e for e in read_entries() if e["timestamp"].date() == target]


def has_missed_report(date_str: str, action: str) -> bool:
    """Return True if a MISSED REPORT for this date+action was already written."""
    if not LOG_PATH.exists():
        return False
    needle = f"REPORT: {action} MISSED on {date_str}"
    with open(LOG_PATH) as f:
        return any(needle in line for line in f)
