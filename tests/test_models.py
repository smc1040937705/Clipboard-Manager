"""
数据模型测试
"""

import unittest
import hashlib
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.models import ClipboardRecord, SearchResult, WindowState
from src.shared.constants import ClipboardType


class TestClipboardRecord(unittest.TestCase):
    """测试剪贴板记录模型"""
    
    def test_text_record_creation(self):
        """测试文本记录创建"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello World"
        )
        
        self.assertEqual(record.content_type, ClipboardType.TEXT)
        self.assertEqual(record.text_content, "Hello World")
        self.assertIsNone(record.image_data)
        self.assertIsNone(record.file_paths)
    
    def test_image_record_creation(self):
        """测试图片记录创建"""
        image_data = b"fake_image_data"
        record = ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=image_data
        )
        
        self.assertEqual(record.content_type, ClipboardType.IMAGE)
        self.assertEqual(record.image_data, image_data)
        self.assertIsNone(record.text_content)
    
    def test_file_record_creation(self):
        """测试文件记录创建"""
        file_paths = ["/path/to/file1.txt", "/path/to/file2.txt"]
        record = ClipboardRecord(
            content_type=ClipboardType.FILE,
            file_paths=file_paths
        )
        
        self.assertEqual(record.content_type, ClipboardType.FILE)
        self.assertEqual(record.file_paths, file_paths)
    
    def test_display_title_text(self):
        """测试文本记录的显示标题"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Hello World\nSecond line"
        )
        
        self.assertEqual(record.display_title, "Hello World")
    
    def test_display_title_empty_text(self):
        """测试空文本记录的显示标题"""
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content=""
        )
        
        self.assertEqual(record.display_title, "(空文本)")
    
    def test_display_title_image(self):
        """测试图片记录的显示标题"""
        record = ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=b"data"
        )
        
        self.assertEqual(record.display_title, "(图片)")
    
    def test_display_title_single_file(self):
        """测试单文件记录的显示标题"""
        record = ClipboardRecord(
            content_type=ClipboardType.FILE,
            file_paths=["/path/to/file.txt"]
        )
        
        self.assertEqual(record.display_title, "(文件) /path/to/file.txt")
    
    def test_display_title_multiple_files(self):
        """测试多文件记录的显示标题"""
        record = ClipboardRecord(
            content_type=ClipboardType.FILE,
            file_paths=["/path/file1.txt", "/path/file2.txt"]
        )
        
        self.assertEqual(record.display_title, "(2 个文件)")
    
    def test_content_hash_text(self):
        """测试文本内容哈希"""
        text = "Hello World"
        record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content=text
        )
        
        expected_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        self.assertEqual(record.content_hash, expected_hash)
    
    def test_content_hash_image(self):
        """测试图片内容哈希"""
        image_data = b"fake_image_data"
        record = ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=image_data
        )
        
        expected_hash = hashlib.md5(image_data).hexdigest()
        self.assertEqual(record.content_hash, expected_hash)
    
    def test_to_dict_text(self):
        """测试文本记录转字典"""
        record = ClipboardRecord(
            id=1,
            content_type=ClipboardType.TEXT,
            text_content="Hello",
            is_favorite=True
        )
        
        data = record.to_dict()
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['content_type'], 1)
        self.assertEqual(data['text_content'], "Hello")
        self.assertTrue(data['is_favorite'])
    
    def test_from_dict_text(self):
        """测试从字典创建文本记录"""
        data = {
            'id': 1,
            'content_type': 1,
            'text_content': 'Hello',
            'is_favorite': True,
            'created_at': '2024-01-01T12:00:00'
        }
        
        record = ClipboardRecord.from_dict(data)
        
        self.assertEqual(record.id, 1)
        self.assertEqual(record.content_type, ClipboardType.TEXT)
        self.assertEqual(record.text_content, 'Hello')
        self.assertTrue(record.is_favorite)
    
    def test_csv_headers(self):
        """测试 CSV 表头"""
        headers = ClipboardRecord.get_csv_headers()
        
        self.assertIn('id', headers)
        self.assertIn('content_type', headers)
        self.assertIn('content', headers)
        self.assertIn('created_at', headers)


class TestWindowState(unittest.TestCase):
    """测试窗口状态模型"""
    
    def test_default_values(self):
        """测试默认值"""
        state = WindowState()
        
        self.assertEqual(state.width, 1200)
        self.assertEqual(state.height, 800)
        self.assertEqual(state.x, 100)
        self.assertEqual(state.y, 100)
        self.assertFalse(state.is_maximized)
        self.assertEqual(state.splitter_position, 350)
        self.assertEqual(state.last_filter_type, 0)
        self.assertEqual(state.last_search_text, "")
        self.assertIsNone(state.last_selected_id)
    
    def test_to_dict(self):
        """测试转字典"""
        state = WindowState(
            width=1000,
            height=600,
            x=200,
            y=150,
            is_maximized=True,
            splitter_position=400,
            last_filter_type=1,
            last_search_text="test",
            last_selected_id=42
        )
        
        data = state.to_dict()
        
        self.assertEqual(data['width'], 1000)
        self.assertEqual(data['height'], 600)
        self.assertEqual(data['x'], 200)
        self.assertEqual(data['y'], 150)
        self.assertTrue(data['is_maximized'])
        self.assertEqual(data['splitter_position'], 400)
        self.assertEqual(data['last_filter_type'], 1)
        self.assertEqual(data['last_search_text'], "test")
        self.assertEqual(data['last_selected_id'], 42)
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'width': 800,
            'height': 600,
            'x': 150,
            'y': 100,
            'is_maximized': False,
            'splitter_position': 300,
            'last_filter_type': 2,
            'last_search_text': 'hello',
            'last_selected_id': 42
        }
        
        state = WindowState.from_dict(data)
        
        self.assertEqual(state.width, 800)
        self.assertEqual(state.height, 600)
        self.assertEqual(state.x, 150)
        self.assertEqual(state.y, 100)
        self.assertFalse(state.is_maximized)
        self.assertEqual(state.splitter_position, 300)
        self.assertEqual(state.last_filter_type, 2)
        self.assertEqual(state.last_search_text, 'hello')
        self.assertEqual(state.last_selected_id, 42)
    
    def test_from_dict_with_partial_data(self):
        """测试从部分字典创建（缺失字段使用默认值）"""
        data = {
            'width': 800,
            'height': 600,
            'last_selected_id': 10
        }
        
        state = WindowState.from_dict(data)
        
        self.assertEqual(state.width, 800)
        self.assertEqual(state.height, 600)
        self.assertEqual(state.x, 100)  # 默认值
        self.assertEqual(state.y, 100)  # 默认值
        self.assertFalse(state.is_maximized)  # 默认值
        self.assertEqual(state.splitter_position, 350)  # 默认值
        self.assertEqual(state.last_filter_type, 0)  # 默认值
        self.assertEqual(state.last_search_text, "")  # 默认值
        self.assertEqual(state.last_selected_id, 10)
    
    def test_roundtrip_serialization(self):
        """测试序列化/反序列化的完整性"""
        original = WindowState(
            width=1024,
            height=768,
            x=50,
            y=50,
            is_maximized=False,
            splitter_position=380,
            last_filter_type=4,
            last_search_text="search query",
            last_selected_id=99
        )
        
        # 序列化后再反序列化
        state_dict = original.to_dict()
        restored = WindowState.from_dict(state_dict)
        
        self.assertEqual(restored.width, 1024)
        self.assertEqual(restored.height, 768)
        self.assertEqual(restored.x, 50)
        self.assertEqual(restored.y, 50)
        self.assertEqual(restored.is_maximized, False)
        self.assertEqual(restored.splitter_position, 380)
        self.assertEqual(restored.last_filter_type, 4)
        self.assertEqual(restored.last_search_text, "search query")
        self.assertEqual(restored.last_selected_id, 99)


if __name__ == '__main__':
    unittest.main()
