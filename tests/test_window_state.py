"""
窗口状态持久化测试
"""

import unittest
import os
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.models import WindowState


class TestWindowState(unittest.TestCase):
    """测试窗口状态持久化"""
    
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
    
    def test_custom_values(self):
        """测试自定义值"""
        state = WindowState(
            width=1920,
            height=1080,
            x=0,
            y=0,
            is_maximized=True,
            splitter_position=400,
            last_filter_type=1,
            last_search_text="test",
            last_selected_id=42
        )
        
        self.assertEqual(state.width, 1920)
        self.assertEqual(state.height, 1080)
        self.assertEqual(state.x, 0)
        self.assertEqual(state.y, 0)
        self.assertTrue(state.is_maximized)
        self.assertEqual(state.splitter_position, 400)
        self.assertEqual(state.last_filter_type, 1)
        self.assertEqual(state.last_search_text, "test")
        self.assertEqual(state.last_selected_id, 42)
    
    def test_to_dict(self):
        """测试转换为字典"""
        state = WindowState(
            width=800,
            height=600,
            x=50,
            y=50,
            is_maximized=False,
            splitter_position=300,
            last_filter_type=2,
            last_search_text="search",
            last_selected_id=10
        )
        
        data = state.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data['width'], 800)
        self.assertEqual(data['height'], 600)
        self.assertEqual(data['x'], 50)
        self.assertEqual(data['y'], 50)
        self.assertFalse(data['is_maximized'])
        self.assertEqual(data['splitter_position'], 300)
        self.assertEqual(data['last_filter_type'], 2)
        self.assertEqual(data['last_search_text'], "search")
        self.assertEqual(data['last_selected_id'], 10)
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'width': 1024,
            'height': 768,
            'x': 200,
            'y': 150,
            'is_maximized': True,
            'splitter_position': 500,
            'last_filter_type': 3,
            'last_search_text': 'keyword',
            'last_selected_id': 99
        }
        
        state = WindowState.from_dict(data)
        
        self.assertEqual(state.width, 1024)
        self.assertEqual(state.height, 768)
        self.assertEqual(state.x, 200)
        self.assertEqual(state.y, 150)
        self.assertTrue(state.is_maximized)
        self.assertEqual(state.splitter_position, 500)
        self.assertEqual(state.last_filter_type, 3)
        self.assertEqual(state.last_search_text, 'keyword')
        self.assertEqual(state.last_selected_id, 99)
    
    def test_from_dict_partial(self):
        """测试从部分字典创建（使用默认值）"""
        data = {
            'width': 1600,
            'height': 900
        }
        
        state = WindowState.from_dict(data)
        
        self.assertEqual(state.width, 1600)
        self.assertEqual(state.height, 900)
        self.assertEqual(state.x, 100)  # 默认值
        self.assertEqual(state.y, 100)  # 默认值
        self.assertFalse(state.is_maximized)  # 默认值
        self.assertEqual(state.splitter_position, 350)  # 默认值
    
    def test_serialization_roundtrip(self):
        """测试序列化往返"""
        original = WindowState(
            width=1440,
            height=900,
            x=100,
            y=50,
            is_maximized=False,
            splitter_position=380,
            last_filter_type=4,
            last_search_text="hello world",
            last_selected_id=123
        )
        
        data = original.to_dict()
        restored = WindowState.from_dict(data)
        
        self.assertEqual(original.width, restored.width)
        self.assertEqual(original.height, restored.height)
        self.assertEqual(original.x, restored.x)
        self.assertEqual(original.y, restored.y)
        self.assertEqual(original.is_maximized, restored.is_maximized)
        self.assertEqual(original.splitter_position, restored.splitter_position)
        self.assertEqual(original.last_filter_type, restored.last_filter_type)
        self.assertEqual(original.last_search_text, restored.last_search_text)
        self.assertEqual(original.last_selected_id, restored.last_selected_id)
    
    def test_empty_search_text(self):
        """测试空搜索文本"""
        state = WindowState(last_search_text="")
        data = state.to_dict()
        restored = WindowState.from_dict(data)
        
        self.assertEqual(restored.last_search_text, "")
    
    def test_none_selected_id(self):
        """测试 None 选中 ID"""
        state = WindowState(last_selected_id=None)
        data = state.to_dict()
        restored = WindowState.from_dict(data)
        
        self.assertIsNone(restored.last_selected_id)


if __name__ == '__main__':
    unittest.main()
