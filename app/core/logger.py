# app/core/logger.py
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from app.core.settings import Settings

class TaskLogger:
    """通用任务日志模块 - 支持结构化日志"""
    def __init__(self, task_name="task"):
        # 1. 确定日志目录
        self.log_dir = Path(Settings.get("paths.logs", "data/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 文件名 (按天或按次，这里按启动时间)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{task_name}_{timestamp}.log"
        
        # 3. 初始化 Logger
        self.logger = logging.getLogger(f"{task_name}_{timestamp}")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = [] # 防止重复添加

        # --- 文件输出 (详细) ---
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(file_handler)

        # --- 控制台输出 (醒目) ---
        console_handler = logging.StreamHandler(sys.stdout)
        # 控制台可以只显示时间+内容，不用太啰嗦
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
        self.logger.addHandler(console_handler)

    def __call__(self, log_data):
        """
        支持结构化日志调用
        
        参数:
            log_data: dict 或 str
                如果是 dict，格式为:
                {
                    "task": "1500",
                    "worker": 1,
                    "level": "info",  # info/error/success/warning
                    "action": "login",
                    "msg": "登录成功"
                }
                如果是 str，直接输出
        """
        if isinstance(log_data, dict):
            # 结构化日志
            level = log_data.get("level", "info")
            worker = log_data.get("worker", "")
            action = log_data.get("action", "")
            msg = log_data.get("msg", "")
            
            # 格式化输出
            prefix = f"[{worker}]" if worker else ""
            action_str = f"[{action}]" if action else ""
            formatted_msg = f"{prefix}{action_str} {msg}".strip()
            
            # 根据级别调用对应方法
            if level == "error":
                self.logger.error(f"❌ {formatted_msg}")
            elif level == "success":
                self.logger.info(f"✅ {formatted_msg}")
            elif level == "warning":
                self.logger.warning(f"⚠️ {formatted_msg}")
            else:  # info
                self.logger.info(formatted_msg)
                
            # 同时写入 JSON 格式到单独文件（可选，用于后续分析）
            # self._write_json_log(log_data)
        else:
            # 兼容旧的字符串格式
            self.logger.info(str(log_data))
    
    def info(self, msg):
        """兼容旧接口"""
        if isinstance(msg, dict):
            self(msg)
        else:
            self.logger.info(msg)

    def error(self, msg):
        """兼容旧接口"""
        if isinstance(msg, dict):
            self(msg)
        else:
            self.logger.error(f"❌ {msg}")

    def success(self, msg):
        """兼容旧接口"""
        if isinstance(msg, dict):
            self(msg)
        else:
            self.logger.info(f"✅ {msg}")
        
    def warning(self, msg):
        """兼容旧接口"""
        if isinstance(msg, dict):
            self(msg)
        else:
            self.logger.warning(f"⚠️ {msg}")