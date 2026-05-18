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
    " > button.btn.dropdown-toggle.dsk-btn"
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
# Confirmation modals that appear after selecting clock in/out
_CLOCK_IN_CONFIRM_SELECTOR = (
    "body > div.modal.fade.clock-in-dialog.in > div > div"
    " > div.modal-footer > button.btn.btn-primary.our-button"
)
_CLOCK_OUT_CONFIRM_SELECTOR = (
    "body > div.modal.fade.clock-out-dialog.in > div > div"
    " > div.modal-footer > button.btn.btn-primary.our-button"
)
# Success modals differ between clock-in and clock-out
_CLOCK_IN_SUCCESS_TITLE = "Time Entry Confirmation"
_CLOCK_OUT_SUCCESS_TITLE = "Clocking Status Update"
_SUCCESS_MODAL_OK = "button:has-text('Ok')"
_SUCCESS_MODAL_SELECTOR = "div.modal.in:has-text('{title}')"


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

        # Wait for dashboard to attach to DOM, then dispatch JS click (bypasses all visibility checks)
        page.wait_for_selector(_TOGGLE_SELECTOR, state="attached", timeout=30000)
        page.locator(_TOGGLE_SELECTOR).dispatch_event("click")
        # Give Bootstrap's dropdown animation time to complete before clicking the item
        page.wait_for_timeout(800)

        # Wait for dropdown items to attach, then dispatch click
        selector = _CLOCK_IN_SELECTOR if action == "clock_in" else _CLOCK_OUT_SELECTOR
        page.wait_for_selector(selector, state="attached", timeout=10000)
        page.locator(selector).dispatch_event("click")

        # Confirm the "Are you sure?" modal
        confirm = _CLOCK_IN_CONFIRM_SELECTOR if action == "clock_in" else _CLOCK_OUT_CONFIRM_SELECTOR
        page.wait_for_selector(confirm, timeout=10000)
        page.locator(confirm).click()

        # Wait for the action-specific success modal and verify it confirms success
        success_title = _CLOCK_IN_SUCCESS_TITLE if action == "clock_in" else _CLOCK_OUT_SUCCESS_TITLE
        success_modal_selector = _SUCCESS_MODAL_SELECTOR.format(title=success_title)
        page.wait_for_selector(success_modal_selector, timeout=15000)
        success_modal = page.locator(success_modal_selector)
        modal_text = success_modal.inner_text()
        if "success" not in modal_text.lower():
            raise RuntimeError(f"Clock action returned unexpected result: {modal_text}")
        success_modal.locator(_SUCCESS_MODAL_OK).click()

        _save_session(context)
        browser.close()
