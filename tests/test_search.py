"""
搜索功能测试
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
from src.core.search_engine import SearchEngine, SearchOptions


class TestSearchEngine(unittest.TestCase):
    """测试搜索引擎"""
    
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
        
        # 创建搜索引擎
        self.search_engine = SearchEngine(self.repository)
        
        # 创建测试记录
        self._create_test_records()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_records(self):
        """创建测试记录"""
        records_data = [
            ("Hello World", ClipboardType.TEXT),
            ("Hello Python", ClipboardType.TEXT),
            ("Goodbye World", ClipboardType.TEXT),
            ("Test Image", ClipboardType.IMAGE),
            (["/path/to/document.txt"], ClipboardType.FILE),
        ]
        
        for content, content_type in records_data:
            if content_type == ClipboardType.TEXT:
                record = ClipboardRecord(
                    content_type=content_type,
                    text_content=content
                )
            elif content_type == ClipboardType.IMAGE:
                record = ClipboardRecord(
                    content_type=content_type,
                    image_data=b"image_data"
                )
            else:
                record = ClipboardRecord(
                    content_type=content_type,
                    file_paths=content
                )
            
            self.repository.create(record)
    
    def test_search_no_keyword(self):
        """测试无关键词搜索"""
        options = SearchOptions(keyword="")
        results = self.search_engine.search(options)
        
        self.assertEqual(len(results), 5)
    
    def test_search_with_keyword(self):
        """测试关键词搜索"""
        options = SearchOptions(keyword="Hello")
        results = self.search_engine.search(options)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("Hello", result.record.text_content)
    
    def test_search_with_filter(self):
        """测试带过滤的搜索"""
        options = SearchOptions(
            keyword="",
            filter_type=ClipboardType.TEXT
        )
        results = self.search_engine.search(options)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.record.content_type, ClipboardType.TEXT)
    
    def test_search_no_match(self):
        """测试无匹配结果"""
        options = SearchOptions(keyword="xyz123")
        results = self.search_engine.search(options)
        
        self.assertEqual(len(results), 0)
    
    def test_search_relevance_score(self):
        """测试相关度分数"""
        # 创建置顶记录
        pinned_record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello Pinned",
            is_pinned=True
        )
        self.repository.create(pinned_record)
        
        options = SearchOptions(keyword="Hello")
        results = self.search_engine.search(options)
        
        # 置顶记录应该排在前面
        self.assertTrue(len(results) > 0)
        # 检查是否有置顶记录
        pinned_results = [r for r in results if r.record.is_pinned]
        self.assertEqual(len(pinned_results), 1)
    
    def test_find_matches(self):
        """测试查找匹配位置"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello Hello World"
        )
        
        matches = self.search_engine._find_matches(record, "Hello", False)
        
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0], (0, 5))
        self.assertEqual(matches[1], (6, 11))
    
    def test_find_matches_case_sensitive(self):
        """测试区分大小写的匹配"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello hello HELLO"
        )
        
        matches = self.search_engine._find_matches(record, "Hello", True)
        
        self.assertEqual(len(matches), 1)
    
    def test_get_highlighted_content(self):
        """测试获取高亮内容"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello World"
        )
        
        result = self.search_engine.get_highlighted_content(record, "World")
        
        self.assertIn("<span", result)
        self.assertIn("World", result)
    
    def test_quick_search(self):
        """测试快速搜索"""
        records = self.search_engine.quick_search("Hello")
        
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertIn("Hello", record.text_content)


if __name__ == '__main__':
    unittest.main()
