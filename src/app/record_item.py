"""
记录项控件模块
实现列表中每条记录的显示
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)

from ..shared.models import ClipboardRecord
from ..shared.constants import ClipboardType
from ..shared.utils import format_timestamp, truncate_text


class RecordItemWidget(QWidget):
    """记录项控件"""
    
    def __init__(self, record: ClipboardRecord, parent=None):
        super().__init__(parent)
        
        self._record = record
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        # 顶部行：类型图标 + 标题 + 标记
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)
        
        # 类型图标
        type_icon = self._get_type_icon()
        self._type_label = QLabel(type_icon)
        self._type_label.setStyleSheet("font-size: 14px;")
        top_layout.addWidget(self._type_label)
        
        # 标题
        title = self._record.display_title
        self._title_label = QLabel(truncate_text(title, 35))
        self._title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        top_layout.addWidget(self._title_label, 1)
        
        # 标记
        marks = []
        if self._record.is_pinned:
            marks.append("📌")
        if self._record.is_favorite:
            marks.append("★")
        
        if marks:
            self._mark_label = QLabel(" ".join(marks))
            self._mark_label.setStyleSheet("font-size: 12px;")
            top_layout.addWidget(self._mark_label)
        
        layout.addLayout(top_layout)
        
        # 底部行：时间
        time_str = format_timestamp(self._record.created_at)
        self._time_label = QLabel(time_str)
        self._time_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._time_label)
        
        # 设置样式
        self._update_style()
    
    def _get_type_icon(self) -> str:
        """获取类型图标"""
        icons = {
            ClipboardType.TEXT: "📝",
            ClipboardType.IMAGE: "🖼",
            ClipboardType.FILE: "📎"
        }
        return icons.get(self._record.content_type, "📋")
    
    def _update_style(self):
        """更新样式"""
        # 置顶项使用不同背景
        if self._record.is_pinned:
            self.setStyleSheet("""
                RecordItemWidget {
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                RecordItemWidget {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
                RecordItemWidget:hover {
                    background-color: #f5f5f5;
                    border-color: #bdbdbd;
                }
            """)
    
    def sizeHint(self):
        """返回建议大小"""
        from PyQt6.QtCore import QSize
        return QSize(300, 50)
