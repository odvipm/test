import pytest
from unittest.mock import MagicMock, patch

_CLOCK_IN_MODAL_TEXT = (
    "Time Entry Confirmation\n"
    "You have successfully clocked in. Your work hours are now being recorded."
)
_CLOCK_OUT_MODAL_TEXT = (
    "Clocking Status Update\n"
    "Success! You've clocked out. Your work hours for this day have been logged."
)


def _make_mock_playwright(modal_text=_CLOCK_IN_MODAL_TEXT):
    mock_page = MagicMock()
    mock_page.locator.return_value.is_visible.return_value = False
    mock_page.locator.return_value.inner_text.return_value = modal_text
    mock_page.locator.return_value.locator.return_value.inner_text.return_value = modal_text
    mock_context = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_p = MagicMock()
    mock_p.chromium.launch.return_value = mock_browser
    return mock_p, mock_page, mock_context


def _run_action(action, mocker, tmp_path, mock_p):
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")
    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        perform_clock_action(action, "https://example.sprout.ph", "user@test.com", "s3cr3t")


def test_clock_in_dispatches_click(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright(_CLOCK_IN_MODAL_TEXT)
    _run_action("clock_in", mocker, tmp_path, mock_p)
    dispatch_calls = [str(c) for c in mock_page.locator.return_value.dispatch_event.call_args_list]
    assert any("click" in c for c in dispatch_calls)


def test_clock_out_dispatches_click(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright(_CLOCK_OUT_MODAL_TEXT)
    _run_action("clock_out", mocker, tmp_path, mock_p)
    dispatch_calls = [str(c) for c in mock_page.locator.return_value.dispatch_event.call_args_list]
    assert any("click" in c for c in dispatch_calls)


def test_clock_in_success_modal_ok_clicked(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright(_CLOCK_IN_MODAL_TEXT)
    _run_action("clock_in", mocker, tmp_path, mock_p)
    mock_page.locator.return_value.locator.assert_called_with("button:has-text('Ok')")


def test_clock_in_success_reads_modal_container_not_title_parent(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright()

    default_locator = MagicMock()
    default_locator.is_visible.return_value = False

    title_locator = MagicMock()
    title_locator.locator.return_value.inner_text.return_value = "×\nTime Entry Confirmation"

    modal_locator = MagicMock()
    modal_locator.inner_text.return_value = _CLOCK_IN_MODAL_TEXT

    def locator_for(selector):
        if selector == "text=Time Entry Confirmation":
            return title_locator
        if selector == "div.modal.in:has-text('Time Entry Confirmation')":
            return modal_locator
        return default_locator

    mock_page.locator.side_effect = locator_for

    _run_action("clock_in", mocker, tmp_path, mock_p)

    modal_locator.locator.assert_called_with("button:has-text('Ok')")


def test_clock_out_success_modal_ok_clicked(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright(_CLOCK_OUT_MODAL_TEXT)
    _run_action("clock_out", mocker, tmp_path, mock_p)
    mock_page.locator.return_value.locator.assert_called_with("button:has-text('Ok')")


def test_raises_when_clock_in_modal_has_no_success_text(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright()
    mock_page.locator.return_value.inner_text.return_value = (
        "Time Entry Confirmation\nError! Something went wrong."
    )
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")
    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        with pytest.raises(RuntimeError, match="unexpected result"):
            perform_clock_action("clock_in", "https://example.sprout.ph", "u", "p")


def test_raises_when_clock_out_modal_has_no_success_text(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright(_CLOCK_OUT_MODAL_TEXT)
    mock_page.locator.return_value.inner_text.return_value = (
        "Clocking Status Update\nError! Something went wrong."
    )
    mocker.patch("browser.AUTH_STATE_PATH", tmp_path / "auth_state.json")
    with patch("browser.sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__.return_value = mock_p
        from browser import perform_clock_action
        with pytest.raises(RuntimeError, match="unexpected result"):
            perform_clock_action("clock_out", "https://example.sprout.ph", "u", "p")


def test_login_called_when_session_expired(mocker, tmp_path):
    mock_p, mock_page, _ = _make_mock_playwright()
    mock_page.locator.return_value.is_visible.return_value = True
    _run_action("clock_in", mocker, tmp_path, mock_p)
    assert mock_page.fill.called


def test_session_saved_after_success(mocker, tmp_path):
    mock_p, mock_page, mock_context = _make_mock_playwright()
    _run_action("clock_in", mocker, tmp_path, mock_p)
    assert mock_context.storage_state.called
