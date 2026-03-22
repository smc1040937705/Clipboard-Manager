"""
存储层测试
"""

import unittest
import os
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.models import ClipboardRecord
from src.shared.constants import ClipboardType
from src.storage.database import DatabaseManager
from src.storage.repository import ClipboardRepository


class TestClipboardRepository(unittest.TestCase):
    """测试剪贴板记录仓库"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.init_database()
        
        # 创建仓库
        self.repository = ClipboardRepository()
        self.repository.db_manager = self.db_manager
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_create_text_record(self):
        """测试创建文本记录"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test content"
        )
        
        record_id = self.repository.create(record)
        
        self.assertIsNotNone(record_id)
        self.assertEqual(record.id, record_id)
    
    def test_get_by_id(self):
        """测试根据 ID 获取记录"""
        # 创建记录
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test content"
        )
        record_id = self.repository.create(record)
        
        # 获取记录
        fetched = self.repository.get_by_id(record_id)
        
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, record_id)
        self.assertEqual(fetched.text_content, "Test content")
    
    def test_get_by_id_not_found(self):
        """测试获取不存在的记录"""
        fetched = self.repository.get_by_id(99999)
        self.assertIsNone(fetched)
    
    def test_get_all(self):
        """测试获取所有记录"""
        # 创建多条记录
        for i in range(5):
            record = ClipboardRecord(
                content_type=ClipboardType.TEXT,
                text_content=f"Content {i}"
            )
            self.repository.create(record)
        
        # 获取所有记录
        records = self.repository.get_all()
        
        self.assertEqual(len(records), 5)
    
    def test_filter_by_type(self):
        """测试按类型过滤"""
        # 创建不同类型的记录
        text_record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Text"
        )
        image_record = ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=b"image"
        )
        
        self.repository.create(text_record)
        self.repository.create(image_record)
        
        # 过滤文本类型
        text_records = self.repository.get_all(filter_type=ClipboardType.TEXT)
        self.assertEqual(len(text_records), 1)
        self.assertEqual(text_records[0].content_type, ClipboardType.TEXT)
    
    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        # 创建记录
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test"
        )
        record_id = self.repository.create(record)
        
        # 切换收藏
        result = self.repository.toggle_favorite(record_id)
        self.assertTrue(result)
        
        # 验证
        fetched = self.repository.get_by_id(record_id)
        self.assertTrue(fetched.is_favorite)
        
        # 再次切换
        self.repository.toggle_favorite(record_id)
        fetched = self.repository.get_by_id(record_id)
        self.assertFalse(fetched.is_favorite)
    
    def test_toggle_pin(self):
        """测试切换置顶状态"""
        # 创建记录
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test"
        )
        record_id = self.repository.create(record)
        
        # 切换置顶
        result = self.repository.toggle_pin(record_id)
        self.assertTrue(result)
        
        # 验证
        fetched = self.repository.get_by_id(record_id)
        self.assertTrue(fetched.is_pinned)
    
    def test_delete(self):
        """测试删除记录"""
        # 创建记录
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test"
        )
        record_id = self.repository.create(record)
        
        # 删除
        result = self.repository.delete(record_id)
        self.assertTrue(result)
        
        # 验证
        fetched = self.repository.get_by_id(record_id)
        self.assertIsNone(fetched)
    
    def test_delete_not_found(self):
        """测试删除不存在的记录"""
        result = self.repository.delete(99999)
        self.assertFalse(result)
    
    def test_clear_all(self):
        """测试清空记录"""
        # 创建记录
        for i in range(5):
            record = ClipboardRecord(
                content_type=ClipboardType.TEXT,
                text_content=f"Content {i}"
            )
            self.repository.create(record)
        
        # 清空
        count = self.repository.clear_all(keep_favorites=False)
        self.assertEqual(count, 5)
        
        # 验证
        records = self.repository.get_all()
        self.assertEqual(len(records), 0)
    
    def test_clear_all_keep_favorites(self):
        """测试清空时保留收藏"""
        # 创建普通记录
        normal_record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Normal"
        )
        normal_id = self.repository.create(normal_record)
        
        # 创建收藏记录
        fav_record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Favorite",
            is_favorite=True
        )
        fav_id = self.repository.create(fav_record)
        
        # 清空（保留收藏）
        count = self.repository.clear_all(keep_favorites=True)
        self.assertEqual(count, 1)
        
        # 验证
        self.assertIsNone(self.repository.get_by_id(normal_id))
        self.assertIsNotNone(self.repository.get_by_id(fav_id))
    
    def test_search(self):
        """测试搜索功能"""
        # 创建记录
        record1 = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello World"
        )
        record2 = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Goodbye World"
        )
        
        self.repository.create(record1)
        self.repository.create(record2)
        
        # 搜索
        results = self.repository.search("Hello")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text_content, "Hello World")
    
    def test_check_duplicate(self):
        """测试重复检查"""
        # 创建记录
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Duplicate test"
        )
        record_id = self.repository.create(record)
        
        # 检查重复
        content_hash = record.content_hash
        duplicate_id = self.repository.check_duplicate(content_hash)
        
        self.assertEqual(duplicate_id, record_id)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 创建不同类型的记录
        self.repository.create(ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Text 1"
        ))
        self.repository.create(ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Text 2"
        ))
        self.repository.create(ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=b"image"
        ))
        
        # 获取统计
        stats = self.repository.get_statistics()
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['text'], 2)
        self.assertEqual(stats['image'], 1)


if __name__ == '__main__':
    unittest.main()
