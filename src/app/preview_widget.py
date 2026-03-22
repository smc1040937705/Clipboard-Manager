"""
预览控件模块
实现详情区的预览功能
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QMessageBox
)

from ..shared.models import ClipboardRecord
from ..shared.constants import ClipboardType
from ..shared.utils import format_timestamp, format_file_size
from ..system.system_api import SystemAPI


class PreviewWidget(QWidget):
    """预览控件"""
    
    # 信号
    copy_requested = pyqtSignal(ClipboardRecord)
    delete_requested = pyqtSignal(ClipboardRecord)
    favorite_requested = pyqtSignal(ClipboardRecord)
    pin_requested = pyqtSignal(ClipboardRecord)
    open_location_requested = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._record: Optional[ClipboardRecord] = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        self._type_label = QLabel("请选择一条记录")
        self._type_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(self._type_label)
        
        title_layout.addStretch()
        
        # 收藏按钮
        self._fav_btn = QPushButton("☆")
        self._fav_btn.setToolTip("收藏")
        self._fav_btn.setFixedSize(30, 30)
        self._fav_btn.clicked.connect(self._on_favorite_clicked)
        title_layout.addWidget(self._fav_btn)
        
        # 置顶按钮
        self._pin_btn = QPushButton("📌")
        self._pin_btn.setToolTip("置顶")
        self._pin_btn.setFixedSize(30, 30)
        self._pin_btn.clicked.connect(self._on_pin_clicked)
        title_layout.addWidget(self._pin_btn)
        
        # 删除按钮
        self._delete_btn = QPushButton("✕")
        self._delete_btn.setToolTip("删除")
        self._delete_btn.setFixedSize(30, 30)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        title_layout.addWidget(self._delete_btn)
        
        layout.addLayout(title_layout)
        
        # 信息标签
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self._info_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #ddd;")
        layout.addWidget(line)
        
        # 内容区域（滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 文本编辑器
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("文本内容将显示在这里...")
        self._text_edit.setVisible(False)
        self._content_layout.addWidget(self._text_edit)
        
        # 图片标签
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setVisible(False)
        self._content_layout.addWidget(self._image_label)
        
        # 文件列表
        self._file_widget = QWidget()
        self._file_layout = QVBoxLayout(self._file_widget)
        self._file_layout.setContentsMargins(0, 0, 0, 0)
        self._file_layout.setSpacing(5)
        self._file_widget.setVisible(False)
        self._content_layout.addWidget(self._file_widget)
        
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll, 1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        
        self._copy_btn = QPushButton("复制到剪贴板")
        self._copy_btn.setToolTip("将内容复制到剪贴板")
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        btn_layout.addWidget(self._copy_btn)
        
        btn_layout.addStretch()
        
        self._open_btn = QPushButton("打开文件位置")
        self._open_btn.setToolTip("在文件管理器中显示")
        self._open_btn.clicked.connect(self._on_open_clicked)
        self._open_btn.setVisible(False)
        btn_layout.addWidget(self._open_btn)
        
        layout.addLayout(btn_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # 设置操作按钮的特殊样式（确保图标显示）
        self._fav_btn.setStyleSheet("font-size: 16px;")
        self._pin_btn.setStyleSheet("font-size: 14px;")
        self._delete_btn.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
    
    def set_record(self, record: ClipboardRecord):
        """设置要显示的记录"""
        self._record = record
        self._update_ui()
    
    def clear(self):
        """清空显示"""
        self._record = None
        self._type_label.setText("请选择一条记录")
        self._info_label.setText("")
        self._text_edit.clear()
        self._text_edit.setVisible(False)
        self._image_label.clear()
        self._image_label.setVisible(False)
        self._file_widget.setVisible(False)
        self._clear_file_list()
        self._copy_btn.setEnabled(False)
        self._open_btn.setVisible(False)
        self._update_favorite_button()
        self._update_pin_button()
    
    def _update_ui(self):
        """更新 UI"""
        if not self._record:
            return
        
        # 类型标签
        type_names = {
            ClipboardType.TEXT: "文本",
            ClipboardType.IMAGE: "图片",
            ClipboardType.FILE: "文件"
        }
        type_name = type_names.get(self._record.content_type, "未知")
        self._type_label.setText(f"{type_name} #{self._record.id}")
        
        # 信息标签
        time_str = format_timestamp(self._record.created_at)
        self._info_label.setText(f"创建时间: {time_str}")
        
        # 更新按钮状态
        self._update_favorite_button()
        self._update_pin_button()
        self._copy_btn.setEnabled(True)
        
        # 根据类型显示内容
        if self._record.content_type == ClipboardType.TEXT:
            self._show_text()
        elif self._record.content_type == ClipboardType.IMAGE:
            self._show_image()
        elif self._record.content_type == ClipboardType.FILE:
            self._show_files()
    
    def _show_text(self):
        """显示文本内容"""
        self._text_edit.setVisible(True)
        self._image_label.setVisible(False)
        self._file_widget.setVisible(False)
        self._open_btn.setVisible(False)
        
        self._text_edit.setPlainText(self._record.text_content or "")
    
    def _show_image(self):
        """显示图片"""
        self._text_edit.setVisible(False)
        self._image_label.setVisible(True)
        self._file_widget.setVisible(False)
        self._open_btn.setVisible(False)
        
        if self._record.image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(self._record.image_data)
            
            if not pixmap.isNull():
                # 缩放图片以适应显示区域
                scaled_pixmap = pixmap.scaled(
                    600, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._image_label.setPixmap(scaled_pixmap)
                
                # 显示图片信息
                size_kb = len(self._record.image_data) / 1024
                self._info_label.setText(
                    f"{self._info_label.text()} | 大小: {size_kb:.1f} KB | "
                    f"尺寸: {pixmap.width()}x{pixmap.height()}"
                )
    
    def _show_files(self):
        """显示文件列表"""
        self._text_edit.setVisible(False)
        self._image_label.setVisible(False)
        self._file_widget.setVisible(True)
        self._open_btn.setVisible(True)
        
        self._clear_file_list()
        
        if self._record.file_paths:
            for file_path in self._record.file_paths:
                self._add_file_item(file_path)
    
    def _clear_file_list(self):
        """清空文件列表"""
        while self._file_layout.count():
            item = self._file_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_file_item(self, file_path: str):
        """添加文件项"""
        file_info = SystemAPI.get_file_info(file_path)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 文件名
        name_label = QLabel(file_info['filename'])
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # 文件大小
        if file_info['exists']:
            size_label = QLabel(format_file_size(file_info['size']))
            size_label.setStyleSheet("color: gray; font-size: 12px;")
            layout.addWidget(size_label)
        
        # 打开按钮
        open_btn = QPushButton("打开")
        open_btn.setFixedWidth(60)
        open_btn.clicked.connect(lambda: self.open_location_requested.emit(file_path))
        layout.addWidget(open_btn)
        
        # 设置样式
        widget.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        self._file_layout.addWidget(widget)
    
    def _update_favorite_button(self):
        """更新收藏按钮状态"""
        if self._record and self._record.is_favorite:
            self._fav_btn.setText("★")
            self._fav_btn.setStyleSheet("color: gold;")
        else:
            self._fav_btn.setText("☆")
            self._fav_btn.setStyleSheet("")
    
    def _update_pin_button(self):
        """更新置顶按钮状态"""
        if self._record and self._record.is_pinned:
            self._pin_btn.setStyleSheet("color: #2196F3;")
        else:
            self._pin_btn.setStyleSheet("")
    
    def _on_copy_clicked(self):
        """复制按钮点击"""
        if self._record:
            self.copy_requested.emit(self._record)
    
    def _on_delete_clicked(self):
        """删除按钮点击"""
        if self._record:
            self.delete_requested.emit(self._record)
    
    def _on_favorite_clicked(self):
        """收藏按钮点击"""
        if self._record:
            self.favorite_requested.emit(self._record)
    
    def _on_pin_clicked(self):
        """置顶按钮点击"""
        if self._record:
            self.pin_requested.emit(self._record)
    
    def _on_open_clicked(self):
        """打开位置按钮点击"""
        if self._record and self._record.file_paths:
            self.open_location_requested.emit(self._record.file_paths[0])
