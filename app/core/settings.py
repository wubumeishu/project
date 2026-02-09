# app/core/settings.py
# 配置管理模块 - 项目唯一配置入口（只读）

import json
from pathlib import Path
from typing import Any


class Settings:
    """
    配置管理类（单例模式，只读）
    
    使用方式：
        from app.core.settings import Settings
        
        # 读取配置
        api_base = Settings.get("bit_browser.api_base")
        token = Settings.get("firefox_sms.token")
        
        # 重新加载配置
        Settings.reload()
    """
    
    _instance = None
    _config = None
    _file_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def _get_file_path(cls) -> Path:
        """获取配置文件路径"""
        if cls._file_path is None:
            base_dir = Path(__file__).resolve().parents[2]
            cls._file_path = base_dir / "settings" / "settings.json"
        return cls._file_path
    
    @classmethod
    def _load(cls) -> dict:
        """从文件加载配置"""
        file_path = cls._get_file_path()
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    
    @classmethod
    def _ensure_loaded(cls):
        """确保配置已加载"""
        if cls._config is None:
            cls._config = cls._load()
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）
        
        示例:
            Settings.get("bit_browser.api_base")
            Settings.get("firefox_sms.token")
            Settings.get("not.exist.key", "default_value")
        """
        cls._ensure_loaded()
        
        keys = key.split(".")
        value = cls._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def reload(cls):
        """重新加载配置文件"""
        cls._config = cls._load()
    
    @classmethod
    def all(cls) -> dict:
        """获取完整配置字典（只读副本）"""
        cls._ensure_loaded()
        return cls._config.copy()
    
    # ============================================================
    # 快捷访问属性（常用配置的便捷方法）
    # ============================================================
    
    @classmethod
    def bit_browser_api_base(cls) -> str:
        """比特浏览器 API 地址"""
        return cls.get("bit_browser.api_base", "http://127.0.0.1:54345")
    
    @classmethod
    def bit_browser_timeout(cls) -> int:
        """比特浏览器超时时间（秒）"""
        return cls.get("bit_browser.default_timeout", 60)
    
    @classmethod
    def firefox_sms_token(cls) -> str:
        """火狐狸短信平台 Token"""
        return cls.get("firefox_sms.token", "")
    
    @classmethod
    def path_assets_root(cls) -> str:
        """资源根目录"""
        return cls.get("paths.assets_root", "assets")
    
    @classmethod
    def path_avatars(cls) -> str:
        """头像目录"""
        return cls.get("paths.avatars", "assets/avatars")
    
    @classmethod
    def path_names(cls) -> str:
        """昵称文件路径"""
        return cls.get("paths.names", "resources/names.txt")
    
    @classmethod
    def path_images(cls) -> str:
        """认证图片目录"""
        return cls.get("paths.images", "images")
    
    @classmethod
    def path_logs(cls) -> str:
        """日志目录"""
        return cls.get("paths.logs", "data/logs")
    
    @classmethod
    def path_records(cls) -> str:
        """记录目录"""
        return cls.get("paths.records", "data/records")
    
    @classmethod
    def runtime_headless(cls) -> bool:
        """是否无头模式"""
        return cls.get("runtime.headless", False)
    
    @classmethod
    def runtime_debug(cls) -> bool:
        """是否调试模式"""
        return cls.get("runtime.debug", True)
