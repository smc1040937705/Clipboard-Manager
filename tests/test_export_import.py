"""
导入导出测试
"""

import unittest
import os
import tempfile
import json
import shutil

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.shared.models import ClipboardRecord
from src.shared.constants import ClipboardType
from src.storage.database import DatabaseManager
from src.storage.repository import ClipboardRepository
from src.core.export_import import ExportImportManager


class TestExportImport(unittest.TestCase):
    """测试导入导出功能"""
    
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
        
        # 创建导入导出管理器
        self.export_manager = ExportImportManager(self.repository)
        
        # 创建测试记录
        self._create_test_records()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_records(self):
        """创建测试记录"""
        # 文本记录
        self.text_record = ClipboardRecord(
            content_type=ClipboardType.TEXT,
            text_content="Test text content",
            is_favorite=True
        )
        self.text_id = self.repository.create(self.text_record)
        
        # 图片记录
        self.image_record = ClipboardRecord(
            content_type=ClipboardType.IMAGE,
            image_data=b"fake_image_data",
            is_pinned=True
        )
        self.image_id = self.repository.create(self.image_record)
        
        # 文件记录
        self.file_record = ClipboardRecord(
            content_type=ClipboardType.FILE,
            file_paths=["/path/to/file1.txt", "/path/to/file2.txt"]
        )
        self.file_id = self.repository.create(self.file_record)
    
    def test_export_to_json(self):
        """测试导出为 JSON"""
        file_path = os.path.join(self.temp_dir, 'export.json')
        
        result = self.export_manager.export_to_json(file_path=file_path)
        
        self.assertEqual(result, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # 验证内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['record_count'], 3)
        self.assertEqual(len(data['records']), 3)
    
    def test_export_to_json_string(self):
        """测试导出为 JSON 字符串"""
        json_str = self.export_manager.export_to_json()
        
        data = json.loads(json_str)
        self.assertEqual(data['record_count'], 3)
    
    def test_export_selected_records(self):
        """测试导出选中记录"""
        file_path = os.path.join(self.temp_dir, 'export_selected.json')
        
        self.export_manager.export_to_json(
            record_ids=[self.text_id],
            file_path=file_path
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['record_count'], 1)
    
    def test_export_to_csv(self):
        """测试导出为 CSV"""
        file_path = os.path.join(self.temp_dir, 'export.csv')
        
        result = self.export_manager.export_to_csv(file_path=file_path)
        
        self.assertEqual(result, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # 验证内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('content_type', content)
        self.assertIn('TEXT', content)
    
    def test_import_from_json(self):
        """测试从 JSON 导入"""
        # 先导出
        export_path = os.path.join(self.temp_dir, 'export.json')
        self.export_manager.export_to_json(file_path=export_path)
        
        # 清空数据库
        self.repository.clear_all(keep_favorites=False)
        
        # 导入
        result = self.export_manager.import_from_json(export_path)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported'], 3)
        self.assertEqual(result['skipped'], 0)
        
        # 验证
        records = self.repository.get_all()
        self.assertEqual(len(records), 3)
    
    def test_import_duplicate_skip(self):
        """测试导入时跳过重复"""
        # 先导出
        export_path = os.path.join(self.temp_dir, 'export.json')
        self.export_manager.export_to_json(file_path=export_path)
        
        # 再次导入（应该跳过）
        result = self.export_manager.import_from_json(export_path)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['skipped'], 3)
    
    def test_import_from_csv(self):
        """测试从 CSV 导入"""
        # 先导出
        export_path = os.path.join(self.temp_dir, 'export.csv')
        self.export_manager.export_to_csv(file_path=export_path)
        
        # 清空数据库
        self.repository.clear_all(keep_favorites=False)
        
        # 导入
        result = self.export_manager.import_from_csv(export_path)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported'], 3)
    
    def test_validate_import_file_json(self):
        """测试验证 JSON 导入文件"""
        # 创建有效文件
        export_path = os.path.join(self.temp_dir, 'export.json')
        self.export_manager.export_to_json(file_path=export_path)
        
        result = self.export_manager.validate_import_file(export_path)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['format'], 'json')
        self.assertEqual(result['record_count'], 3)
    
    def test_validate_import_file_csv(self):
        """测试验证 CSV 导入文件"""
        # 创建有效文件
        export_path = os.path.join(self.temp_dir, 'export.csv')
        self.export_manager.export_to_csv(file_path=export_path)
        
        result = self.export_manager.validate_import_file(export_path)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['format'], 'csv')
        self.assertEqual(result['record_count'], 3)
    
    def test_validate_import_file_not_found(self):
        """测试验证不存在的文件"""
        result = self.export_manager.validate_import_file('/nonexistent/file.json')
        
        self.assertFalse(result['valid'])
        self.assertIn('不存在', result['error'])
    
    def test_validate_import_file_invalid_format(self):
        """测试验证无效格式"""
        invalid_file = os.path.join(self.temp_dir, 'invalid.txt')
        with open(invalid_file, 'w') as f:
            f.write("invalid content")
        
        result = self.export_manager.validate_import_file(invalid_file)
        
        self.assertFalse(result['valid'])


if __name__ == '__main__':
    unittest.main()
