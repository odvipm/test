import argparse
import getpass
import os
import time
from datetime import datetime

import pytz

from auth import get_credentials, save_credentials
from browser import perform_clock_action
from config import load_config
from logger import write_entry, write_report
from notifier import notify
from reporter import check_missed_runs, generate_report, generate_report_html

MAX_RETRIES = 3
RETRY_WAIT = 30


def _is_workday(config: dict) -> bool:
    tz = pytz.timezone(config["timezone"])
    today = datetime.now(tz).strftime("%A")
    return today in config["workdays"]


def _run_action(action: str) -> None:
    config = load_config()
    if not _is_workday(config):
        return

    check_missed_runs()

    username, password = get_credentials()
    last_error = ""
    start = time.time()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            perform_clock_action(action, config["sprout_url"], username, password)
            duration = time.time() - start
            write_entry(action, "success", duration=duration)
            label = "in" if action == "clock_in" else "out"
            notify(
                f"Clocked {label} ✓",
                f"Clocked {label} at {datetime.now().strftime('%H:%M')}",
            )
            return
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT)

    write_entry(action, "failed", reason=f"{last_error} after {MAX_RETRIES} retries")
    label = "in" if action == "clock_in" else "out"
    notify(
        f"Clock-{label} failed ✗",
        f"Clock-{label} failed — please {action.replace('_', ' ')} manually",
    )


def _run_report() -> None:
    missed = check_missed_runs()
    report = generate_report()
    print(report)
    write_report(report)
    if missed:
        notify("Sprout: Missed entries ⚠", "\n".join(missed[:3]))


def _run_report_browser() -> None:
    check_missed_runs()
    html_path = generate_report_html()
    os.startfile(str(html_path))


def _run_setup() -> None:
    username = input("Sprout username (email): ")
    password = getpass.getpass("Sprout password: ")
    save_credentials(username, password)
    print("Credentials saved successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sprout Auto Clocker")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--action", choices=["clock_in", "clock_out"], help="Perform clock action")
    group.add_argument("--report", action="store_true", help="Show 7-day summary in terminal")
    group.add_argument("--report-browser", action="store_true", help="Open 7-day summary in browser")
    group.add_argument("--setup", action="store_true", help="Save Sprout credentials")
    args = parser.parse_args()

    if args.action:
        _run_action(args.action)
    elif args.report:
        _run_report()
    elif args.report_browser:
        _run_report_browser()
    elif args.setup:
        _run_setup()


if __name__ == "__main__":
    main()
