from app.services.browser.browser_controller import (
    create_browser,
    open_browser,
    close_browser
)


class BitBrowserAPI:
    def create(self, payload=None) -> str:
        return create_browser()

    def open(self, browser_id: str) -> str:
        return open_browser(browser_id)

    def close(self, browser_id: str):
        close_browser(browser_id)
