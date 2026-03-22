"""
SQLite 数据库管理模块
负责数据库连接、表创建和迁移
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from ..shared.constants import DATA_DIR, DB_PATH, DB_TIMEOUT


class DatabaseManager:
    """数据库管理器"""
    
    # 数据库版本，用于迁移
    CURRENT_VERSION = 1
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库，创建表和索引"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建剪贴板记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type INTEGER NOT NULL,
                    text_content TEXT,
                    image_data BLOB,
                    file_paths TEXT,
                    content_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_favorite INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON clipboard_records(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_type 
                ON clipboard_records(content_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON clipboard_records(content_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_favorite 
                ON clipboard_records(is_favorite)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_pinned 
                ON clipboard_records(is_pinned)
            """)
            
            # 创建 FTS 虚拟表用于全文搜索
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS clipboard_fts USING fts5(
                    text_content,
                    file_paths,
                    content='clipboard_records',
                    content_rowid='id'
                )
            """)
            
            # 创建触发器以保持 FTS 索引同步
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS clipboard_ai AFTER INSERT ON clipboard_records BEGIN
                    INSERT INTO clipboard_fts(rowid, text_content, file_paths)
                    VALUES (new.id, new.text_content, new.file_paths);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS clipboard_ad AFTER DELETE ON clipboard_records BEGIN
                    INSERT INTO clipboard_fts(clipboard_fts, rowid, text_content, file_paths)
                    VALUES ('delete', old.id, old.text_content, old.file_paths);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS clipboard_au AFTER UPDATE ON clipboard_records BEGIN
                    INSERT INTO clipboard_fts(clipboard_fts, rowid, text_content, file_paths)
                    VALUES ('delete', old.id, old.text_content, old.file_paths);
                    INSERT INTO clipboard_fts(rowid, text_content, file_paths)
                    VALUES (new.id, new.text_content, new.file_paths);
                END
            """)
            
            # 创建元数据表记录版本
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # 插入或更新版本号
            cursor.execute("""
                INSERT OR REPLACE INTO db_metadata (key, value)
                VALUES ('version', ?)
            """, (str(self.CURRENT_VERSION),))
    
    def get_version(self) -> int:
        """获取数据库版本"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM db_metadata WHERE key = 'version'"
                )
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except sqlite3.OperationalError:
            return 0
    
    def migrate(self):
        """执行数据库迁移"""
        current_version = self.get_version()
        
        if current_version < self.CURRENT_VERSION:
            # 执行迁移
            for version in range(current_version, self.CURRENT_VERSION):
                self._migrate_to_version(version + 1)
    
    def _migrate_to_version(self, target_version: int):
        """迁移到指定版本"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if target_version == 1:
                # 版本 1 的迁移逻辑（初始版本，无需操作）
                pass
            
            # 更新版本号
            cursor.execute("""
                INSERT OR REPLACE INTO db_metadata (key, value)
                VALUES ('version', ?)
            """, (str(target_version),))
    
    def vacuum(self):
        """优化数据库（压缩空间）"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
    
    def close(self):
        """关闭数据库连接（上下文管理器会自动处理）"""
        pass


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.init_database()
    return _db_manager
