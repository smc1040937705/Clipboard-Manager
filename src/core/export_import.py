"""
导入导出模块
支持 JSON 和 CSV 格式的导入导出
"""

import json
import csv
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable
from io import StringIO

from ..shared.models import ClipboardRecord
from ..shared.constants import JSON_EXPORT_VERSION, APP_NAME, APP_VERSION
from ..storage.repository import ClipboardRepository


class ExportImportManager:
    """导入导出管理器"""
    
    def __init__(self, repository: Optional[ClipboardRepository] = None):
        self.repository = repository or ClipboardRepository()
    
    def export_to_json(self, record_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None) -> str:
        """
        导出记录为 JSON 格式
        
        Args:
            record_ids: 要导出的记录 ID 列表，None 表示导出全部
            file_path: 导出文件路径，None 则返回 JSON 字符串
            
        Returns:
            JSON 字符串或文件路径
        """
        # 获取记录
        if record_ids:
            records = []
            for rid in record_ids:
                record = self.repository.get_by_id(rid)
                if record:
                    records.append(record)
        else:
            records = self.repository.get_all(limit=10000)
        
        # 构建导出数据
        export_data = {
            "version": JSON_EXPORT_VERSION,
            "app": APP_NAME,
            "app_version": APP_VERSION,
            "export_time": datetime.now().isoformat(),
            "record_count": len(records),
            "records": [record.to_dict() for record in records]
        }
        
        # 转换为 JSON
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        # 保存到文件
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return file_path
        
        return json_str
    
    def export_to_csv(self, record_ids: Optional[List[int]] = None,
                      file_path: Optional[str] = None) -> str:
        """
        导出记录为 CSV 格式
        
        Args:
            record_ids: 要导出的记录 ID 列表，None 表示导出全部
            file_path: 导出文件路径，None 则返回 CSV 字符串
            
        Returns:
            CSV 字符串或文件路径
        """
        # 获取记录
        if record_ids:
            records = []
            for rid in record_ids:
                record = self.repository.get_by_id(rid)
                if record:
                    records.append(record)
        else:
            records = self.repository.get_all(limit=10000)
        
        # 构建 CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=ClipboardRecord.get_csv_headers())
        writer.writeheader()
        
        for record in records:
            writer.writerow(record.to_csv_row())
        
        csv_str = output.getvalue()
        output.close()
        
        # 保存到文件
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_str)
            return file_path
        
        return csv_str
    
    def import_from_json(self, file_path: str, 
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> dict:
        """
        从 JSON 文件导入记录
        
        Args:
            file_path: JSON 文件路径
            progress_callback: 进度回调函数 (current, total)
            
        Returns:
            导入结果统计
        """
        result = {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证版本
            version = data.get('version', '1.0')
            
            records_data = data.get('records', [])
            total = len(records_data)
            
            # 获取现有哈希用于去重
            existing_hashes = set(self.repository.get_recent_hashes(limit=10000))
            
            for i, record_data in enumerate(records_data):
                try:
                    # 创建记录对象
                    record = ClipboardRecord.from_dict(record_data)
                    
                    # 检查重复
                    if record.content_hash in existing_hashes:
                        result['skipped'] += 1
                        continue
                    
                    # 重置 ID 以便创建新记录
                    record.id = None
                    
                    # 保存到数据库
                    self.repository.create(record)
                    existing_hashes.add(record.content_hash)
                    result['imported'] += 1
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback(i + 1, total)
                
                except Exception as e:
                    result['errors'].append(f"记录 {i+1}: {str(e)}")
            
            result['success'] = True
        
        except json.JSONDecodeError as e:
            result['errors'].append(f"JSON 解析错误: {str(e)}")
        except FileNotFoundError:
            result['errors'].append(f"文件不存在: {file_path}")
        except Exception as e:
            result['errors'].append(f"导入失败: {str(e)}")
        
        return result
    
    def import_from_csv(self, file_path: str,
                        progress_callback: Optional[Callable[[int, int], None]] = None) -> dict:
        """
        从 CSV 文件导入记录
        
        Args:
            file_path: CSV 文件路径
            progress_callback: 进度回调函数 (current, total)
            
        Returns:
            导入结果统计
        """
        result = {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            total = len(rows)
            
            # 获取现有哈希用于去重
            existing_hashes = set(self.repository.get_recent_hashes(limit=10000))
            
            from ..shared.constants import ClipboardType
            
            for i, row in enumerate(rows):
                try:
                    # 解析内容类型
                    content_type_name = row.get('content_type', 'TEXT')
                    content_type = ClipboardType[content_type_name]

                    # 创建记录
                    record = ClipboardRecord(
                        content_type=content_type,
                        is_favorite=row.get('is_favorite', '0') == '1',
                        is_pinned=row.get('is_pinned', '0') == '1',
                    )

                    # 设置内容
                    if content_type == ClipboardType.TEXT:
                        record.text_content = row.get('content', '')
                    elif content_type == ClipboardType.FILE:
                        file_paths_str = row.get('file_paths', '')
                        if file_paths_str:
                            record.file_paths = file_paths_str.split('|')
                    elif content_type == ClipboardType.IMAGE:
                        # 从 Base64 解码图片数据
                        image_data_str = row.get('image_data', '')
                        if image_data_str:
                            record.image_data = base64.b64decode(image_data_str)

                    # 解析时间
                    created_at_str = row.get('created_at', '')
                    if created_at_str:
                        record.created_at = datetime.fromisoformat(created_at_str)

                    # 检查重复
                    if record.content_hash in existing_hashes:
                        result['skipped'] += 1
                        continue

                    # 保存到数据库
                    self.repository.create(record)
                    existing_hashes.add(record.content_hash)
                    result['imported'] += 1

                    # 进度回调
                    if progress_callback:
                        progress_callback(i + 1, total)

                except Exception as e:
                    result['errors'].append(f"行 {i+1}: {str(e)}")
            
            result['success'] = True
        
        except FileNotFoundError:
            result['errors'].append(f"文件不存在: {file_path}")
        except Exception as e:
            result['errors'].append(f"导入失败: {str(e)}")
        
        return result
    
    def validate_import_file(self, file_path: str) -> dict:
        """验证导入文件"""
        result = {
            'valid': False,
            'format': None,
            'record_count': 0,
            'error': None
        }
        
        try:
            if not os.path.exists(file_path):
                result['error'] = "文件不存在"
                return result
            
            ext = Path(file_path).suffix.lower()
            
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result['format'] = 'json'
                result['record_count'] = len(data.get('records', []))
                result['valid'] = True
            
            elif ext == '.csv':
                with open(file_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                result['format'] = 'csv'
                result['record_count'] = len(rows)
                result['valid'] = True
            
            else:
                result['error'] = "不支持的文件格式"
        
        except json.JSONDecodeError as e:
            result['error'] = f"JSON 解析错误: {str(e)}"
        except Exception as e:
            result['error'] = str(e)
        
        return result
