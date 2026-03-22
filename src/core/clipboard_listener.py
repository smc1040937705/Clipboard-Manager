"""
剪贴板监听模块
实时监听剪贴板变化，支持去重和防抖
"""

from typing import Optional, Callable, List
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication

from ..shared.models import ClipboardRecord
from ..shared.constants import (
    ClipboardType, 
    CLIPBOARD_DEBOUNCE_MS, 
    CLIPBOARD_MAX_DUPLICATE_CHECK,
    MAX_TEXT_LENGTH,
    MAX_IMAGE_SIZE
)
from ..shared.utils import get_image_format_from_data


class ClipboardListener(QObject):
    """剪贴板监听器"""
    
    # 信号定义
    text_captured = pyqtSignal(ClipboardRecord)  # 捕获到文本
    image_captured = pyqtSignal(ClipboardRecord)  # 捕获到图片
    files_captured = pyqtSignal(ClipboardRecord)  # 捕获到文件
    content_captured = pyqtSignal(ClipboardRecord)  # 捕获到任意内容
    error_occurred = pyqtSignal(str)  # 发生错误
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._clipboard = QApplication.clipboard()
        self._is_listening = False
        self._is_paused = False
        
        # 防抖定时器
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_clipboard)
        
        # 去重缓存（保存最近的内容哈希）
        self._recent_hashes: deque = deque(maxlen=CLIPBOARD_MAX_DUPLICATE_CHECK)
        
        # 上次处理的内容哈希
        self._last_hash: Optional[str] = None
        
        # 内容处理器（用于自定义处理）
        self._content_handler: Optional[Callable[[ClipboardRecord], None]] = None
    
    def start_listening(self):
        """开始监听剪贴板"""
        if not self._is_listening:
            self._clipboard.dataChanged.connect(self._on_clipboard_changed)
            self._is_listening = True
            self._is_paused = False
    
    def stop_listening(self):
        """停止监听剪贴板"""
        if self._is_listening:
            self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            self._is_listening = False
            self._debounce_timer.stop()
    
    def pause(self):
        """暂停监听"""
        self._is_paused = True
    
    def resume(self):
        """恢复监听"""
        self._is_paused = False
    
    @property
    def is_listening(self) -> bool:
        """是否正在监听"""
        return self._is_listening
    
    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._is_paused
    
    def set_content_handler(self, handler: Callable[[ClipboardRecord], None]):
        """设置内容处理器"""
        self._content_handler = handler
    
    def _on_clipboard_changed(self):
        """剪贴板变化回调"""
        if self._is_paused:
            return
        
        # 重置防抖定时器
        self._debounce_timer.stop()
        self._debounce_timer.start(CLIPBOARD_DEBOUNCE_MS)
    
    def _process_clipboard(self):
        """处理剪贴板内容"""
        try:
            mime_data = self._clipboard.mimeData()
            if not mime_data:
                return
            
            record: Optional[ClipboardRecord] = None
            
            # 检查文件路径
            if mime_data.hasUrls():
                file_paths = []
                for url in mime_data.urls():
                    if url.isLocalFile():
                        file_paths.append(url.toLocalFile())
                
                if file_paths:
                    record = ClipboardRecord(
                        content_type=ClipboardType.FILE,
                        file_paths=file_paths
                    )
            
            # 检查图片
            elif mime_data.hasImage():
                image = self._clipboard.image()
                if not image.isNull():
                    image_data = self._image_to_bytes(image)
                    if image_data and len(image_data) <= MAX_IMAGE_SIZE:
                        record = ClipboardRecord(
                            content_type=ClipboardType.IMAGE,
                            image_data=image_data
                        )
            
            # 检查文本
            elif mime_data.hasText():
                text = mime_data.text()
                if text and len(text) <= MAX_TEXT_LENGTH:
                    record = ClipboardRecord(
                        content_type=ClipboardType.TEXT,
                        text_content=text
                    )
            
            # 处理记录
            if record:
                self._handle_record(record)
        
        except Exception as e:
            self.error_occurred.emit(f"处理剪贴板内容失败: {str(e)}")
    
    def _image_to_bytes(self, image: QImage) -> Optional[bytes]:
        """将 QImage 转换为字节数据"""
        try:
            from PyQt6.QtCore import QBuffer, QIODevice
            
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            
            # 保存为 PNG 格式
            if image.save(buffer, "PNG"):
                return buffer.data().data()
            
            return None
        except Exception:
            return None
    
    def _handle_record(self, record: ClipboardRecord):
        """处理捕获的记录"""
        # 检查重复
        content_hash = record.content_hash
        
        if content_hash == self._last_hash:
            # 与上次内容相同，跳过
            return
        
        if content_hash in self._recent_hashes:
            # 在最近的缓存中，跳过
            return
        
        # 更新缓存
        self._recent_hashes.append(content_hash)
        self._last_hash = content_hash
        
        # 调用内容处理器
        if self._content_handler:
            self._content_handler(record)
        
        # 发射信号
        self.content_captured.emit(record)
        
        if record.content_type == ClipboardType.TEXT:
            self.text_captured.emit(record)
        elif record.content_type == ClipboardType.IMAGE:
            self.image_captured.emit(record)
        elif record.content_type == ClipboardType.FILE:
            self.files_captured.emit(record)
    
    def set_clipboard_text(self, text: str):
        """设置剪贴板文本"""
        self._clipboard.setText(text)
    
    def set_clipboard_image(self, image_data: bytes):
        """设置剪贴板图片"""
        try:
            from PyQt6.QtGui import QImage
            from PyQt6.QtCore import QByteArray
            
            image = QImage()
            image.loadFromData(QByteArray(image_data))
            
            if not image.isNull():
                self._clipboard.setImage(image)
        except Exception as e:
            self.error_occurred.emit(f"设置剪贴板图片失败: {str(e)}")
    
    def clear_recent_hashes(self):
        """清空最近哈希缓存"""
        self._recent_hashes.clear()
        self._last_hash = None
