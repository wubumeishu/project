# app/services/browser/instance.py

from enum import Enum


class BrowserStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAIT_HUMAN = "WAIT_HUMAN"
    CLOSED = "CLOSED"


class BrowserInstance:
    def __init__(self, browser_id: str, account_id: str):
        self.browser_id = browser_id
        self.account_id = account_id
        self.status = BrowserStatus.IDLE

    def mark_running(self):
        self.status = BrowserStatus.RUNNING

    def mark_idle(self):
        self.status = BrowserStatus.IDLE

    def mark_wait_human(self):
        self.status = BrowserStatus.WAIT_HUMAN

    def mark_closed(self):
        self.status = BrowserStatus.CLOSED

    def can_be_acquired(self) -> bool:
        return self.status == BrowserStatus.IDLE

    def __repr__(self):
        return f"<Browser {self.browser_id} {self.status}>"
