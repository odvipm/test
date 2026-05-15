from pathlib import Path

from playwright.sync_api import sync_playwright, Page

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"

_EMAIL_SELECTOR = "#username"
_PASSWORD_SELECTOR = "#password"
_SUBMIT_SELECTOR = "#kc-login"

# First click opens the dropdown
_TOGGLE_SELECTOR = (
    "#dashboard-container-fluid > div > div > div.col-md-8 > div > div:nth-child(6)"
    " > div > div.widget-title.widget-2.parent > div:nth-child(3)"
    " > button.btn.dropdown-toggle.dsk-btn > span"
)
# These appear after the dropdown opens
_CLOCK_IN_SELECTOR = (
    "#dashboard-container-fluid > div > div > div.col-md-8 > div > div:nth-child(6)"
    " > div > div.widget-title.widget-2.parent > div.dropdown.clock-in-out-dropdown.open"
    " > ul > li:nth-child(1) > a > span"
)
_CLOCK_OUT_SELECTOR = (
    "#dashboard-container-fluid > div > div > div.col-md-8 > div > div:nth-child(6)"
    " > div > div.widget-title.widget-2.parent > div.dropdown.clock-in-out-dropdown.open"
    " > ul > li:nth-child(2) > a > span"
)


def _is_session_valid(page: Page) -> bool:
    return not page.locator(_SUBMIT_SELECTOR).is_visible()


def _login(page: Page, sprout_url: str, username: str, password: str) -> None:
    page.goto(sprout_url)
    page.fill(_EMAIL_SELECTOR, username)
    page.fill(_PASSWORD_SELECTOR, password)
    page.click(_SUBMIT_SELECTOR)
    page.wait_for_load_state("networkidle", timeout=30000)


def _save_session(context) -> None:
    context.storage_state(path=str(AUTH_STATE_PATH))


def perform_clock_action(action: str, sprout_url: str, username: str, password: str) -> None:
    storage = str(AUTH_STATE_PATH) if AUTH_STATE_PATH.exists() else None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=storage)
        page = context.new_page()
        page.goto(sprout_url)

        if not _is_session_valid(page):
            _login(page, sprout_url, username, password)
            _save_session(context)

        # Wait for dashboard to fully load, then open the clock dropdown
        page.wait_for_selector(_TOGGLE_SELECTOR, timeout=30000)
        page.click(_TOGGLE_SELECTOR)

        # Wait for dropdown to open, then click Clock In or Clock Out
        selector = _CLOCK_IN_SELECTOR if action == "clock_in" else _CLOCK_OUT_SELECTOR
        page.wait_for_selector(selector, timeout=10000)
        page.click(selector)

        page.wait_for_timeout(2000)
        _save_session(context)
        browser.close()
