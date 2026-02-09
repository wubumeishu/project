# app/core/browser_manager.py

from typing import Dict, Optional
from app.services.browser.api import BitBrowserAPI
from app.services.browser.instance import BrowserInstance, BrowserStatus


class BrowserManager:
    def __init__(self):
        self.api = BitBrowserAPI()
        self.browsers: Dict[str, BrowserInstance] = {}

    def create_browser(self, account_id: str, payload: dict | None = None):
        browser_id = self.api.create(payload)
        ws = self.api.open(browser_id)

        instance = BrowserInstance(browser_id, account_id)
        instance.ws = ws  # 先存着，后面 Task 用
        self.browsers[browser_id] = instance
        return instance

    def acquire(self, account_id: str) -> Optional[BrowserInstance]:
        """
        获取一个可用浏览器（同账号只允许一个）
        """
        for browser in self.browsers.values():
            if (
                browser.account_id == account_id
                and browser.can_be_acquired()
            ):
                browser.mark_running()
                return browser
        return None

    def release(self, browser_id: str):
        """
        释放浏览器（任务完成）
        """
        browser = self.browsers.get(browser_id)
        if not browser:
            return

        if browser.status == BrowserStatus.WAIT_HUMAN:
            # 人工接管的窗口，系统不允许自动释放
            return

        browser.mark_idle()

    def mark_wait_human(self, browser_id: str):
        """
        标记为人工接管状态
        """
        browser = self.browsers.get(browser_id)
        if not browser:
            return

        browser.mark_wait_human()

    def close(self, browser_id: str):
        """
        关闭浏览器并移除管理
        """
        browser = self.browsers.get(browser_id)
        if not browser:
            return

        self.api.close(browser_id)
        browser.mark_closed()
        self.browsers.pop(browser_id, None)
