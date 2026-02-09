# app/services/tasks/base_task.py

from abc import ABC, abstractmethod
from app.core.settings import Settings


class BaseTask(ABC):
    task_name: str = "base"
    item_id: int | None = None

    def __init__(self):
        self.settings = Settings
        self.running = False
        self.paused = False

    # === 生命周期 ===
    def start(self):
        self.running = True
        self.run()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    # === 通用配置 ===
    @property
    def sms_token(self) -> str:
        return self.settings.firefox_sms_token()

    # === 业务入口 ===
    @abstractmethod
    def run(self):
        """
        子类实现具体业务逻辑
        """
        pass
