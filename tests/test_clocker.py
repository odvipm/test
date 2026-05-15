import pytest
from unittest.mock import patch, MagicMock


CONFIG = {
    "sprout_url": "https://example.sprout.ph",
    "clock_in_time": "09:00",
    "clock_out_time": "18:00",
    "workdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "timezone": "Asia/Manila",
}


def test_clock_in_on_workday_succeeds(mocker):
    mocker.patch("clocker.load_config", return_value=CONFIG)
    mocker.patch("clocker._is_workday", return_value=True)
    mocker.patch("clocker.check_missed_runs", return_value=[])
    mocker.patch("clocker.get_credentials", return_value=("user", "pass"))
    mock_action = mocker.patch("clocker.perform_clock_action")
    mock_notify = mocker.patch("clocker.notify")
    mock_log = mocker.patch("clocker.write_entry")

    from clocker import _run_action
    _run_action("clock_in")

    mock_action.assert_called_once()
    mock_notify.assert_called_once()
    assert mock_log.call_args[0][1] == "success"


def test_clock_in_on_non_workday_exits_early(mocker):
    mocker.patch("clocker.load_config", return_value=CONFIG)
    mocker.patch("clocker._is_workday", return_value=False)
    mock_action = mocker.patch("clocker.perform_clock_action")

    from clocker import _run_action
    _run_action("clock_in")

    mock_action.assert_not_called()


def test_retries_three_times_on_failure(mocker):
    mocker.patch("clocker.load_config", return_value=CONFIG)
    mocker.patch("clocker._is_workday", return_value=True)
    mocker.patch("clocker.check_missed_runs", return_value=[])
    mocker.patch("clocker.get_credentials", return_value=("user", "pass"))
    mock_action = mocker.patch("clocker.perform_clock_action", side_effect=Exception("timeout"))
    mock_notify = mocker.patch("clocker.notify")
    mock_log = mocker.patch("clocker.write_entry")
    mocker.patch("clocker.time.sleep")  # skip actual 30s waits

    from clocker import _run_action
    _run_action("clock_in")

    assert mock_action.call_count == 3
    assert mock_log.call_args[0][1] == "failed"
    mock_notify.assert_called_once()


def test_report_action_prints_and_notifies_on_missed(mocker, capsys):
    mocker.patch("clocker.check_missed_runs", return_value=["clock_in MISSED on 2026-05-14"])
    mocker.patch("clocker.generate_report", return_value="Week summary...")
    mocker.patch("clocker.write_report")
    mock_notify = mocker.patch("clocker.notify")

    from clocker import _run_report
    _run_report()

    captured = capsys.readouterr()
    assert "Week summary" in captured.out
    mock_notify.assert_called_once()
