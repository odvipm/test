from pathlib import Path

from playwright.sync_api import sync_playwright, Page

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"

# Selectors — update these with values discovered by inspecting the live Sprout app
_EMAIL_SELECTOR = "input[name='email']"
_PASSWORD_SELECTOR = "input[type='password']"
_SUBMIT_SELECTOR = "button[type='submit']"
_CLOCK_IN_SELECTOR = "button:has-text('Clock In')"
_CLOCK_OUT_SELECTOR = "button:has-text('Clock Out')"


def _is_session_valid(page: Page) -> bool:
    return "login" not in page.url.lower()


def _login(page: Page, sprout_url: str, username: str, password: str) -> None:
    page.goto(sprout_url)
    page.fill(_EMAIL_SELECTOR, username)
    page.fill(_PASSWORD_SELECTOR, password)
    page.click(_SUBMIT_SELECTOR)
    page.wait_for_load_state("networkidle", timeout=15000)


def _save_session(context) -> None:
    context.storage_state(path=str(AUTH_STATE_PATH))


def perform_clock_action(action: str, sprout_url: str, username: str, password: str) -> None:
    """Perform clock_in or clock_out via headless Playwright browser."""
    storage = str(AUTH_STATE_PATH) if AUTH_STATE_PATH.exists() else None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=storage)
        page = context.new_page()
        page.goto(sprout_url)

        if not _is_session_valid(page):
            _login(page, sprout_url, username, password)
            _save_session(context)

        selector = _CLOCK_IN_SELECTOR if action == "clock_in" else _CLOCK_OUT_SELECTOR
        page.click(selector)
        page.wait_for_timeout(2000)
        _save_session(context)
        browser.close()
