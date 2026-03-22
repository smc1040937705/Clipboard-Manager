"""
数据仓库模块
提供剪贴板记录的增删改查操作
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

from .database import get_db_manager
from ..shared.models import ClipboardRecord
from ..shared.constants import ClipboardType, MAX_HISTORY_ITEMS, CLIPBOARD_MAX_DUPLICATE_CHECK


class ClipboardRepository:
    """剪贴板记录仓库"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def _row_to_record(self, row: sqlite3.Row) -> ClipboardRecord:
        """将数据库行转换为记录对象"""
        record = ClipboardRecord(
            id=row['id'],
            content_type=ClipboardType(row['content_type']),
            text_content=row['text_content'],
            image_data=row['image_data'],
            file_paths=json.loads(row['file_paths']) if row['file_paths'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            is_favorite=bool(row['is_favorite']),
            is_pinned=bool(row['is_pinned']),
        )
        return record
    
    def create(self, record: ClipboardRecord) -> int:
        """创建新记录，返回记录 ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO clipboard_records 
                (content_type, text_content, image_data, file_paths, content_hash, 
                 is_favorite, is_pinned, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.content_type.value,
                record.text_content,
                record.image_data,
                json.dumps(record.file_paths) if record.file_paths else None,
                record.content_hash,
                int(record.is_favorite),
                int(record.is_pinned),
                record.updated_at.isoformat() if record.updated_at else None,
            ))
            
            record.id = cursor.lastrowid
            
            # 清理旧记录，保持数量限制
            self._cleanup_old_records(cursor)
            
            return record.id
    
    def _cleanup_old_records(self, cursor: sqlite3.Cursor):
        """清理旧记录，保持数量限制"""
        # 保留收藏和置顶的记录
        cursor.execute("""
            SELECT id FROM clipboard_records 
            WHERE is_favorite = 0 AND is_pinned = 0
            ORDER BY created_at DESC
            LIMIT -1 OFFSET ?
        """, (MAX_HISTORY_ITEMS,))
        
        old_ids = [row[0] for row in cursor.fetchall()]
        
        if old_ids:
            placeholders = ','.join('?' * len(old_ids))
            cursor.execute(f"""
                DELETE FROM clipboard_records 
                WHERE id IN ({placeholders})
            """, old_ids)
    
    def get_by_id(self, record_id: int) -> Optional[ClipboardRecord]:
        """根据 ID 获取记录"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM clipboard_records WHERE id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
            return None
    
    def get_all(self, filter_type: int = 0, limit: int = 100, offset: int = 0) -> List[ClipboardRecord]:
        """获取所有记录，支持过滤"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clause = "1=1"
            params = []
            
            if filter_type == ClipboardType.TEXT:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.TEXT.value)
            elif filter_type == ClipboardType.IMAGE:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.IMAGE.value)
            elif filter_type == ClipboardType.FILE:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.FILE.value)
            elif filter_type == 4:  # FAVORITE
                where_clause += " AND is_favorite = 1"
            
            # 置顶的记录排在最前面，然后按时间倒序
            query = f"""
                SELECT * FROM clipboard_records 
                WHERE {where_clause}
                ORDER BY is_pinned DESC, created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def search(self, keyword: str, filter_type: int = 0, limit: int = 100) -> List[ClipboardRecord]:
        """搜索记录"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用 FTS 进行全文搜索
            try:
                cursor.execute("""
                    SELECT r.* FROM clipboard_records r
                    JOIN clipboard_fts f ON r.id = f.rowid
                    WHERE clipboard_fts MATCH ?
                    ORDER BY r.is_pinned DESC, r.created_at DESC
                    LIMIT ?
                """, (keyword, limit))
                
                return [self._row_to_record(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                # FTS 查询失败时回退到 LIKE 查询
                return self._search_fallback(cursor, keyword, filter_type, limit)
    
    def _search_fallback(self, cursor: sqlite3.Cursor, keyword: str, 
                         filter_type: int, limit: int) -> List[ClipboardRecord]:
        """搜索回退方法（使用 LIKE）"""
        where_clause = "(text_content LIKE ? OR file_paths LIKE ?)"
        params = [f'%{keyword}%', f'%{keyword}%']
        
        if filter_type == ClipboardType.TEXT:
            where_clause += " AND content_type = ?"
            params.append(ClipboardType.TEXT.value)
        elif filter_type == ClipboardType.IMAGE:
            where_clause += " AND content_type = ?"
            params.append(ClipboardType.IMAGE.value)
        elif filter_type == ClipboardType.FILE:
            where_clause += " AND content_type = ?"
            params.append(ClipboardType.FILE.value)
        elif filter_type == 4:  # FAVORITE
            where_clause += " AND is_favorite = 1"
        
        query = f"""
            SELECT * FROM clipboard_records 
            WHERE {where_clause}
            ORDER BY is_pinned DESC, created_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        
        return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def update(self, record: ClipboardRecord) -> bool:
        """更新记录"""
        if record.id is None:
            return False
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE clipboard_records 
                SET is_favorite = ?, is_pinned = ?
                WHERE id = ?
            """, (
                int(record.is_favorite),
                int(record.is_pinned),
                record.id,
            ))
            
            return cursor.rowcount > 0
    
    def delete(self, record_id: int) -> bool:
        """删除记录"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM clipboard_records WHERE id = ?
            """, (record_id,))
            
            return cursor.rowcount > 0
    
    def delete_batch(self, record_ids: List[int]) -> int:
        """批量删除记录，返回删除数量"""
        if not record_ids:
            return 0
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                DELETE FROM clipboard_records WHERE id IN ({placeholders})
            """, record_ids)
            
            return cursor.rowcount
    
    def clear_all(self, keep_favorites: bool = True) -> int:
        """清空所有记录，可选择是否保留收藏"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if keep_favorites:
                cursor.execute("""
                    DELETE FROM clipboard_records 
                    WHERE is_favorite = 0
                """)
            else:
                cursor.execute("DELETE FROM clipboard_records")
            
            return cursor.rowcount
    
    def toggle_favorite(self, record_id: int) -> bool:
        """切换收藏状态"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE clipboard_records 
                SET is_pinned = NOT is_pinned
                WHERE id = ?
            """, (record_id,))
            
            return cursor.rowcount > 0
    
    def toggle_pin(self, record_id: int) -> bool:
        """切换置顶状态"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE clipboard_records 
                SET is_pinned = NOT is_pinned
                WHERE id = ?
            """, (record_id,))
            
            return cursor.rowcount > 0
    
    def check_duplicate(self, content_hash: str) -> Optional[int]:
        """检查是否存在重复内容，返回记录 ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM clipboard_records 
                WHERE content_hash = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (content_hash,))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_recent_hashes(self, limit: int = CLIPBOARD_MAX_DUPLICATE_CHECK) -> List[str]:
        """获取最近的内容哈希列表，用于快速去重检查"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT content_hash FROM clipboard_records 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_count(self, filter_type: int = 0) -> int:
        """获取记录数量"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = "1=1"
            params = []
            
            if filter_type == ClipboardType.TEXT:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.TEXT.value)
            elif filter_type == ClipboardType.IMAGE:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.IMAGE.value)
            elif filter_type == ClipboardType.FILE:
                where_clause += " AND content_type = ?"
                params.append(ClipboardType.FILE.value)
            elif filter_type == 4:  # FAVORITE
                where_clause += " AND is_favorite = 1"
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM clipboard_records WHERE {where_clause}
            """, params)
            
            return cursor.fetchone()[0]
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM clipboard_records")
            total = cursor.fetchone()[0]
            
            # 各类型数量
            cursor.execute("""
                SELECT content_type, COUNT(*) FROM clipboard_records
                GROUP BY content_type
            """)
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 收藏数量
            cursor.execute("""
                SELECT COUNT(*) FROM clipboard_records WHERE is_favorite = 1
            """)
            favorites = cursor.fetchone()[0]
            
            return {
                'total': total,
                'text': type_counts.get(ClipboardType.TEXT.value, 0),
                'image': type_counts.get(ClipboardType.IMAGE.value, 0),
                'file': type_counts.get(ClipboardType.FILE.value, 0),
                'favorites': favorites,
            }
