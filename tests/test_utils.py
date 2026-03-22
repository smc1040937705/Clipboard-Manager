"""
工具函数测试
"""

import unittest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.utils import (
    format_timestamp, truncate_text, highlight_text,
    get_image_format_from_data, format_file_size
)


class TestFormatTimestamp(unittest.TestCase):
    """测试时间格式化"""
    
    def test_just_now(self):
        """测试刚刚"""
        now = datetime.now()
        result = format_timestamp(now)
        self.assertEqual(result, "刚刚")
    
    def test_minutes_ago(self):
        """测试几分钟前"""
        dt = datetime.now() - timedelta(minutes=5)
        result = format_timestamp(dt)
        self.assertEqual(result, "5 分钟前")
    
    def test_hours_ago(self):
        """测试几小时前"""
        dt = datetime.now() - timedelta(hours=3)
        result = format_timestamp(dt)
        self.assertEqual(result, "3 小时前")
    
    def test_yesterday(self):
        """测试昨天"""
        dt = datetime.now() - timedelta(days=1)
        result = format_timestamp(dt)
        self.assertTrue(result.startswith("昨天"))
    
    def test_days_ago(self):
        """测试几天前"""
        dt = datetime.now() - timedelta(days=3)
        result = format_timestamp(dt)
        self.assertEqual(result, "3 天前")
    
    def test_date_format(self):
        """测试日期格式"""
        dt = datetime.now() - timedelta(days=10)
        result = format_timestamp(dt)
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")


class TestTruncateText(unittest.TestCase):
    """测试文本截断"""
    
    def test_no_truncate_short_text(self):
        """测试短文本不截断"""
        text = "Short text"
        result = truncate_text(text, max_length=100)
        self.assertEqual(result, text)
    
    def test_truncate_long_text(self):
        """测试长文本截断"""
        text = "A" * 100
        result = truncate_text(text, max_length=50)
        self.assertEqual(len(result), 50)
        self.assertTrue(result.endswith("..."))
    
    def test_custom_suffix(self):
        """测试自定义后缀"""
        text = "A" * 100
        result = truncate_text(text, max_length=50, suffix="[更多]")
        self.assertTrue(result.endswith("[更多]"))


class TestHighlightText(unittest.TestCase):
    """测试文本高亮"""
    
    def test_no_keyword(self):
        """测试无关键词"""
        text = "Hello World"
        result, positions = highlight_text(text, "")
        self.assertEqual(result, text)
        self.assertEqual(positions, [])
    
    def test_single_match(self):
        """测试单个匹配"""
        text = "Hello World"
        result, positions = highlight_text(text, "World")
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0], (6, 11))
        self.assertIn("<span", result)
    
    def test_multiple_matches(self):
        """测试多个匹配"""
        text = "Hello Hello Hello"
        result, positions = highlight_text(text, "Hello")
        self.assertEqual(len(positions), 3)
    
    def test_case_insensitive(self):
        """测试不区分大小写"""
        text = "Hello World"
        result, positions = highlight_text(text, "hello")
        self.assertEqual(len(positions), 1)
    
    def test_no_match(self):
        """测试无匹配"""
        text = "Hello World"
        result, positions = highlight_text(text, "xyz")
        self.assertEqual(positions, [])
        self.assertEqual(result, text)


class TestGetImageFormat(unittest.TestCase):
    """测试图片格式识别"""
    
    def test_png(self):
        """测试 PNG"""
        data = b'\x89PNG\r\n\x1a\n'
        result = get_image_format_from_data(data)
        self.assertEqual(result, 'PNG')
    
    def test_jpeg(self):
        """测试 JPEG"""
        data = b'\xff\xd8'
        result = get_image_format_from_data(data)
        self.assertEqual(result, 'JPEG')
    
    def test_gif(self):
        """测试 GIF"""
        data = b'GIF89a'
        result = get_image_format_from_data(data)
        self.assertEqual(result, 'GIF')
    
    def test_unknown(self):
        """测试未知格式"""
        data = b'unknown'
        result = get_image_format_from_data(data)
        self.assertIsNone(result)


class TestFormatFileSize(unittest.TestCase):
    """测试文件大小格式化"""
    
    def test_bytes(self):
        """测试字节"""
        result = format_file_size(500)
        self.assertEqual(result, "500 B")
    
    def test_kilobytes(self):
        """测试 KB"""
        result = format_file_size(1024)
        self.assertEqual(result, "1.0 KB")
    
    def test_megabytes(self):
        """测试 MB"""
        result = format_file_size(1024 * 1024)
        self.assertEqual(result, "1.0 MB")
    
    def test_gigabytes(self):
        """测试 GB"""
        result = format_file_size(1024 * 1024 * 1024)
        self.assertEqual(result, "1.0 GB")


if __name__ == '__main__':
    unittest.main()
