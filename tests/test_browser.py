import pytest
from unittest.mock import MagicMock, patch


def _make_mock_playwright(page_url="https://example.sprout.ph/home"):
    mock_page = MagicMock()
    mock_page.url = page_url
    mock_context = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_p = MagicMock()
    mock_p.chromium.launch.return_value = mock_browser
    return mock_p, mock_page, mock_context


def test_perform_clock_in_clicks_correct_button(mocker, tmp_path):
    mock_p, mock_page, mock_context = _make_mock_playwright()
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")

    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        perform_clock_action(
            "clock_in",
            "https://example.sprout.ph",
            "user@test.com",
            "s3cr3t",
        )

    mock_page.click.assert_any_call("button:has-text('Clock In')")


def test_perform_clock_out_clicks_correct_button(mocker, tmp_path):
    mock_p, mock_page, mock_context = _make_mock_playwright()
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")

    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        perform_clock_action(
            "clock_out",
            "https://example.sprout.ph",
            "user@test.com",
            "s3cr3t",
        )

    mock_page.click.assert_any_call("button:has-text('Clock Out')")


def test_login_is_called_when_session_invalid(mocker, tmp_path):
    mock_p, mock_page, mock_context = _make_mock_playwright(
        page_url="https://example.sprout.ph/login"
    )
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")

    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        perform_clock_action(
            "clock_in",
            "https://example.sprout.ph",
            "user@test.com",
            "s3cr3t",
        )

    assert mock_page.fill.called
