"""
数据模型模块
定义剪贴板记录的数据结构和相关操作
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Union
import json
import base64

from .constants import ClipboardType


@dataclass
class ClipboardRecord:
    """剪贴板记录数据类"""
    
    id: Optional[int] = None
    content_type: ClipboardType = ClipboardType.TEXT
    text_content: Optional[str] = None
    image_data: Optional[bytes] = None
    file_paths: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_favorite: bool = False
    is_pinned: bool = False
    updated_at: datetime = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.content_type == ClipboardType.FILE and self.file_paths is None:
            self.file_paths = []
    
    @property
    def display_title(self) -> str:
        """获取显示标题"""
        if self.content_type == ClipboardType.TEXT:
            text = self.text_content or ""
            # 取第一行，限制长度
            first_line = text.split('\n')[0][:50]
            return first_line if first_line else "(空文本)"
        elif self.content_type == ClipboardType.IMAGE:
            return "(图片)"
        elif self.content_type == ClipboardType.FILE:
            if self.file_paths:
                count = len(self.file_paths)
                if count == 1:
                    return f"(文件) {self.file_paths[0]}"
                else:
                    return f"({count} 个文件)"
            return "(文件)"
        return "(未知)"
    
    @property
    def content_hash(self) -> str:
        """生成内容哈希，用于去重"""
        import hashlib
        
        if self.content_type == ClipboardType.TEXT and self.text_content:
            return hashlib.md5(self.text_content.encode('utf-8')).hexdigest()
        elif self.content_type == ClipboardType.IMAGE and self.image_data:
            return hashlib.md5(self.image_data).hexdigest()
        elif self.content_type == ClipboardType.FILE and self.file_paths:
            paths_str = '|'.join(sorted(self.file_paths))
            return hashlib.md5(paths_str.encode('utf-8')).hexdigest()
        return ""
    
    def to_dict(self) -> dict:
        """转换为字典（用于导出）"""
        data = {
            "id": self.id,
            "content_type": self.content_type.value,
            "created_at": self.created_at.isoformat(),
            "is_favorite": self.is_favorite,
            "is_pinned": self.is_pinned,
        }
        
        if self.content_type == ClipboardType.TEXT:
            data["text_content"] = self.text_content
        elif self.content_type == ClipboardType.IMAGE and self.image_data:
            # Base64 编码图片数据
            data["image_data"] = base64.b64encode(self.image_data).decode('utf-8')
        elif self.content_type == ClipboardType.FILE:
            data["file_paths"] = self.file_paths
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClipboardRecord':
        """从字典创建实例（用于导入）"""
        record = cls(
            id=data.get("id"),
            content_type=ClipboardType(data.get("content_type", 1)),
            is_favorite=data.get("is_favorite", False),
            is_pinned=data.get("is_pinned", False),
        )
        
        # 解析时间
        if "created_at" in data:
            record.created_at = datetime.fromisoformat(data["created_at"])
        
        # 根据类型设置内容
        if record.content_type == ClipboardType.TEXT:
            record.text_content = data.get("text_content")
        elif record.content_type == ClipboardType.IMAGE:
            image_b64 = data.get("image_data")
            if image_b64:
                record.image_data = base64.b64decode(image_b64)
        elif record.content_type == ClipboardType.FILE:
            record.file_paths = data.get("file_paths", [])
        
        return record
    
    def to_csv_row(self) -> dict:
        """转换为 CSV 行数据"""
        image_data_b64 = ""
        if self.content_type == ClipboardType.IMAGE and self.image_data:
            image_data_b64 = base64.b64encode(self.image_data).decode('utf-8')
        
        return {
            "id": self.id,
            "content_type": self.content_type.name,
            "content": self.text_content or "",
            "image_data": image_data_b64,
            "file_paths": "|".join(self.file_paths) if self.file_paths else "",
            "created_at": self.created_at.isoformat(),
            "is_favorite": "1" if self.is_favorite else "0",
            "is_pinned": "1" if self.is_pinned else "0",
        }
    
    @staticmethod
    def get_csv_headers() -> List[str]:
        """获取 CSV 表头"""
        return ["id", "content_type", "content", "image_data", "file_paths", "created_at", "is_favorite", "is_pinned"]


@dataclass
class SearchResult:
    """搜索结果数据类"""
    
    record: ClipboardRecord
    match_positions: List[tuple] = field(default_factory=list)  # 匹配位置 (start, end)
    relevance_score: float = 0.0  # 相关度分数
    
    @property
    def highlighted_title(self) -> str:
        """获取高亮标题"""
        title = self.record.display_title
        if not self.match_positions:
            return title
        
        # 简单的高亮处理（实际在 UI 中实现）
        return title


@dataclass
class WindowState:
    """窗口状态数据类"""
    
    width: int = 1200
    height: int = 800
    x: int = 100
    y: int = 100
    is_maximized: bool = False
    splitter_position: int = 350
    last_filter_type: int = 0  # FilterType.ALL
    last_search_text: str = ""
    last_selected_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "is_maximized": self.is_maximized,
            "splitter_position": self.splitter_position,
            "last_filter_type": self.last_filter_type,
            "last_search_text": self.last_search_text,
            "last_selected_id": self.last_selected_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WindowState':
        """从字典创建实例"""
        return cls(
            width=data.get("width", 1200),
            height=data.get("height", 800),
            x=data.get("x", 100),
            y=data.get("y", 100),
            is_maximized=data.get("is_maximized", False),
            splitter_position=data.get("splitter_position", 350),
            last_filter_type=data.get("last_filter_type", 0),
            last_search_text=data.get("last_search_text", ""),
            last_selected_id=data.get("last_selected_id"),
        )
