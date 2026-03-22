"""
桌面通知模块
提供系统通知功能
"""

from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon


class NotificationManager(QObject):
    """通知管理器"""
    
    notification_clicked = pyqtSignal(str)  # 通知被点击，参数为通知 ID
    
    def __init__(self, tray_icon: QSystemTrayIcon, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._tray_icon = tray_icon
        self._notifications: dict = {}  # 存储通知信息
        self._notification_id = 0
    
    def show(self, title: str, message: str, 
             notification_id: Optional[str] = None,
             duration_ms: int = 3000) -> str:
        """
        显示通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_id: 通知唯一标识，None 则自动生成
            duration_ms: 显示时长（毫秒）
            
        Returns:
            通知 ID
        """
        if notification_id is None:
            self._notification_id += 1
            notification_id = f"notification_{self._notification_id}"
        
        if self._tray_icon and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                duration_ms
            )
            
            # 存储通知信息
            self._notifications[notification_id] = {
                'title': title,
                'message': message,
                'timestamp': __import__('time').time()
            }
        
        return notification_id
    
    def show_clipboard_captured(self, content_type: str, preview: str):
        """
        显示剪贴板捕获通知
        
        Args:
            content_type: 内容类型（文本/图片/文件）
            preview: 内容预览
        """
        title = f"已捕获 {content_type}"
        # 限制预览长度
        if len(preview) > 50:
            preview = preview[:50] + "..."
        
        self.show(title, preview, duration_ms=2000)
    
    def show_error(self, message: str, duration_ms: int = 5000):
        """显示错误通知"""
        if self._tray_icon and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(
                "错误",
                message,
                QSystemTrayIcon.MessageIcon.Warning,
                duration_ms
            )
    
    def show_info(self, title: str, message: str, duration_ms: int = 3000):
        """显示信息通知"""
        self.show(title, message, duration_ms=duration_ms)
    
    def clear_notifications(self):
        """清除通知记录"""
        self._notifications.clear()
    
    def is_supported(self) -> bool:
        """检查是否支持通知"""
        return self._tray_icon is not None and self._tray_icon.supportsMessages()
