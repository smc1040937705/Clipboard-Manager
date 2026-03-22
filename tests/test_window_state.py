"""
窗口状态持久化测试
"""

import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.models import WindowState


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

    def test_custom_values(self):
        """测试自定义值"""
        state = WindowState(
            width=1920,
            height=1080,
            x=50,
            y=100,
            is_maximized=True,
            splitter_position=400,
            last_filter_type=2,
            last_search_text="test query",
            last_selected_id=42
        )

        self.assertEqual(state.width, 1920)
        self.assertEqual(state.height, 1080)
        self.assertEqual(state.x, 50)
        self.assertEqual(state.y, 100)
        self.assertTrue(state.is_maximized)
        self.assertEqual(state.splitter_position, 400)
        self.assertEqual(state.last_filter_type, 2)
        self.assertEqual(state.last_search_text, "test query")
        self.assertEqual(state.last_selected_id, 42)

    def test_to_dict(self):
        """测试转字典"""
        state = WindowState(
            width=1000,
            height=600,
            x=200,
            y=150,
            is_maximized=True,
            splitter_position=300,
            last_filter_type=1,
            last_search_text="hello",
            last_selected_id=10
        )

        data = state.to_dict()

        self.assertEqual(data['width'], 1000)
        self.assertEqual(data['height'], 600)
        self.assertEqual(data['x'], 200)
        self.assertEqual(data['y'], 150)
        self.assertTrue(data['is_maximized'])
        self.assertEqual(data['splitter_position'], 300)
        self.assertEqual(data['last_filter_type'], 1)
        self.assertEqual(data['last_search_text'], "hello")
        self.assertEqual(data['last_selected_id'], 10)

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'width': 800,
            'height': 600,
            'x': 10,
            'y': 20,
            'is_maximized': False,
            'splitter_position': 250,
            'last_filter_type': 3,
            'last_search_text': "world",
            'last_selected_id': 99
        }

        state = WindowState.from_dict(data)

        self.assertEqual(state.width, 800)
        self.assertEqual(state.height, 600)
        self.assertEqual(state.x, 10)
        self.assertEqual(state.y, 20)
        self.assertFalse(state.is_maximized)
        self.assertEqual(state.splitter_position, 250)
        self.assertEqual(state.last_filter_type, 3)
        self.assertEqual(state.last_search_text, "world")
        self.assertEqual(state.last_selected_id, 99)

    def test_from_dict_partial(self):
        """测试从部分字典创建（使用默认值）"""
        data = {
            'width': 900,
            'is_maximized': True
        }

        state = WindowState.from_dict(data)

        self.assertEqual(state.width, 900)
        self.assertEqual(state.height, 800)  # 默认值
        self.assertEqual(state.x, 100)  # 默认值
        self.assertEqual(state.y, 100)  # 默认值
        self.assertTrue(state.is_maximized)
        self.assertEqual(state.splitter_position, 350)  # 默认值

    def test_roundtrip_conversion(self):
        """测试往返转换（to_dict -> from_dict）"""
        original = WindowState(
            width=1440,
            height=900,
            x=100,
            y=50,
            is_maximized=False,
            splitter_position=500,
            last_filter_type=4,
            last_search_text="clipboard",
            last_selected_id=123
        )

        data = original.to_dict()
        restored = WindowState.from_dict(data)

        self.assertEqual(restored.width, original.width)
        self.assertEqual(restored.height, original.height)
        self.assertEqual(restored.x, original.x)
        self.assertEqual(restored.y, original.y)
        self.assertEqual(restored.is_maximized, original.is_maximized)
        self.assertEqual(restored.splitter_position, original.splitter_position)
        self.assertEqual(restored.last_filter_type, original.last_filter_type)
        self.assertEqual(restored.last_search_text, original.last_search_text)
        self.assertEqual(restored.last_selected_id, original.last_selected_id)

    def test_none_last_selected_id(self):
        """测试 last_selected_id 为 None 的情况"""
        state = WindowState(last_selected_id=None)

        data = state.to_dict()
        self.assertIsNone(data['last_selected_id'])

        restored = WindowState.from_dict(data)
        self.assertIsNone(restored.last_selected_id)


class TestWindowStatePersistence(unittest.TestCase):
    """测试窗口状态持久化（模拟 QSettings 行为）"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.temp_dir, 'settings.json')

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    def _save_state(self, state: WindowState):
        """模拟保存窗口状态到文件"""
        import json
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f)

    def _load_state(self) -> WindowState:
        """模拟从文件加载窗口状态"""
        import json
        if not os.path.exists(self.settings_file):
            return WindowState()

        with open(self.settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return WindowState.from_dict(data)

    def test_save_and_load(self):
        """测试保存和加载窗口状态"""
        original = WindowState(
            width=1600,
            height=900,
            x=200,
            y=100,
            is_maximized=True,
            splitter_position=450,
            last_filter_type=2,
            last_search_text="test",
            last_selected_id=5
        )

        self._save_state(original)
        loaded = self._load_state()

        self.assertEqual(loaded.width, 1600)
        self.assertEqual(loaded.height, 900)
        self.assertEqual(loaded.x, 200)
        self.assertEqual(loaded.y, 100)
        self.assertTrue(loaded.is_maximized)
        self.assertEqual(loaded.splitter_position, 450)
        self.assertEqual(loaded.last_filter_type, 2)
        self.assertEqual(loaded.last_search_text, "test")
        self.assertEqual(loaded.last_selected_id, 5)

    def test_load_without_save(self):
        """测试在没有保存文件时加载默认状态"""
        state = self._load_state()

        self.assertEqual(state.width, 1200)
        self.assertEqual(state.height, 800)
        self.assertEqual(state.x, 100)
        self.assertEqual(state.y, 100)
        self.assertFalse(state.is_maximized)

    def test_persistence_after_multiple_saves(self):
        """测试多次保存后的持久化"""
        # 第一次保存
        state1 = WindowState(width=800, height=600, last_search_text="first")
        self._save_state(state1)

        loaded1 = self._load_state()
        self.assertEqual(loaded1.last_search_text, "first")

        # 第二次保存
        state2 = WindowState(width=1024, height=768, last_search_text="second")
        self._save_state(state2)

        loaded2 = self._load_state()
        self.assertEqual(loaded2.width, 1024)
        self.assertEqual(loaded2.height, 768)
        self.assertEqual(loaded2.last_search_text, "second")

    def test_special_characters_in_search_text(self):
        """测试搜索文本中包含特殊字符"""
        state = WindowState(last_search_text="特殊字符: 中文 🎉 \"quoted\" 'single'")
        self._save_state(state)
        loaded = self._load_state()

        self.assertEqual(loaded.last_search_text, "特殊字符: 中文 🎉 \"quoted\" 'single'")


if __name__ == '__main__':
    unittest.main()
