# app/core/db.py
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from app.core.settings import Settings

class DatabaseManager:
    """
    SQLite 数据库管理器
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        # 数据库文件放在 data/ 目录下
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        self.db_path = db_dir / "tasks.db"
        
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # 1. 生产表 (对应 Excel 的生产表)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_prod (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idx TEXT,
                task_type TEXT,
                phone TEXT,
                password TEXT,
                nick TEXT,
                dob TEXT,
                age TEXT,
                region TEXT,
                status TEXT,
                error TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # 2. 销售表 (对应 Excel 的销售表)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idx TEXT,
                task_type TEXT,
                phone TEXT,
                password TEXT,
                nick TEXT,
                dob TEXT,
                age TEXT,
                region TEXT,
                assign_status TEXT DEFAULT '未出',
                assign_user TEXT,
                assign_time TIMESTAMP,
                created_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def get_conn(self):
        return sqlite3.connect(str(self.db_path), check_same_thread=False)

    def insert_record(self, data: dict, age: str):
        """插入数据到数据库"""
        conn = self.get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # 插入生产表
            cursor.execute('''
                INSERT INTO tasks_prod (idx, task_type, phone, password, nick, dob, age, region, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(data.get("idx", "")),
                "1500",
                data.get("phone", ""),
                data.get("password", ""),
                data.get("nick", ""),
                data.get("dob", ""),
                age,
                data.get("region", ""),
                data.get("status", ""),
                data.get("error", ""),
                now
            ))
            
            # 如果成功，插入销售表
            if data.get("status") == "success":
                cursor.execute('''
                    INSERT INTO tasks_sale (idx, task_type, phone, password, nick, dob, age, region, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(data.get("idx", "")),
                    "1500",
                    data.get("phone", ""),
                    data.get("password", ""),
                    data.get("nick", ""),
                    data.get("dob", ""),
                    age,
                    data.get("region", ""),
                    now
                ))
            
            conn.commit()
        except Exception as e:
            print(f"❌ 数据库写入失败: {e}")
        finally:
            conn.close()