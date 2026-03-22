"""
系统托盘管理模块
管理托盘图标、菜单和交互
"""

from typing import Optional, Callable

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter, QFont
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QWidget

from ..shared.constants import APP_NAME, APP_DISPLAY_NAME, TRAY_TOOLTIP, TRAY_TOOLTIP_PAUSED


class TrayManager(QObject):
    """托盘管理器"""
    
    # 信号定义
    show_window_requested = pyqtSignal()  # 请求显示主窗口
    pause_requested = pyqtSignal(bool)  # 请求暂停/恢复监听 (True = 暂停)
    quit_requested = pyqtSignal()  # 请求退出应用
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._parent = parent
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None
        self._is_paused = False
        
        # 菜单项
        self._show_action: Optional[QAction] = None
        self._pause_action: Optional[QAction] = None
        self._quit_action: Optional[QAction] = None
        
        self._init_tray()
    
    def _init_tray(self):
        """初始化托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # 创建托盘图标
        self._tray_icon = QSystemTrayIcon(self._parent)
        self._tray_icon.setIcon(self._create_tray_icon())
        self._tray_icon.setToolTip(TRAY_TOOLTIP)
        
        # 创建菜单
        self._create_menu()
        
        # 连接激活信号
        self._tray_icon.activated.connect(self._on_tray_activated)
    
    def _create_menu(self):
        """创建托盘菜单"""
        self._tray_menu = QMenu(self._parent)
        
        # 显示主窗口
        self._show_action = QAction("显示主窗口", self._parent)
        self._show_action.triggered.connect(self.show_window_requested.emit)
        self._tray_menu.addAction(self._show_action)
        
        self._tray_menu.addSeparator()
        
        # 暂停/恢复监听
        self._pause_action = QAction("暂停监听", self._parent)
        self._pause_action.setCheckable(True)
        self._pause_action.triggered.connect(self._on_pause_toggled)
        self._tray_menu.addAction(self._pause_action)
        
        self._tray_menu.addSeparator()
        
        # 退出
        self._quit_action = QAction("退出", self._parent)
        self._quit_action.triggered.connect(self.quit_requested.emit)
        self._tray_menu.addAction(self._quit_action)
        
        # 设置菜单
        self._tray_icon.setContextMenu(self._tray_menu)
    
    def _create_tray_icon(self) -> QIcon:
        """创建托盘图标"""
        # 创建一个简单的图标（使用程序绘制）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.setBrush(QColor("#2196F3"))
        painter.setPen(QColor("#1976D2"))
        painter.drawRoundedRect(2, 2, 28, 28, 4, 4)
        
        # 绘制文字 "C"
        painter.setPen(QColor("white"))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, "C")  # 居中对齐
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_paused_icon(self) -> QIcon:
        """创建暂停状态的图标"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制灰色背景
        painter.setBrush(QColor("#9E9E9E"))
        painter.setPen(QColor("#757575"))
        painter.drawRoundedRect(2, 2, 28, 28, 4, 4)
        
        # 绘制文字 "C"
        painter.setPen(QColor("white"))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, "C")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def show(self):
        """显示托盘图标"""
        if self._tray_icon:
            self._tray_icon.show()
    
    def hide(self):
        """隐藏托盘图标"""
        if self._tray_icon:
            self._tray_icon.hide()
    
    def set_paused(self, paused: bool):
        """设置暂停状态"""
        self._is_paused = paused
        
        if self._tray_icon:
            if paused:
                self._tray_icon.setIcon(self._create_paused_icon())
                self._tray_icon.setToolTip(TRAY_TOOLTIP_PAUSED)
            else:
                self._tray_icon.setIcon(self._create_tray_icon())
                self._tray_icon.setToolTip(TRAY_TOOLTIP)
        
        if self._pause_action:
            self._pause_action.setChecked(paused)
            self._pause_action.setText("恢复监听" if paused else "暂停监听")
    
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """显示托盘通知"""
        if self._tray_icon and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                duration
            )
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def _on_pause_toggled(self, checked: bool):
        """暂停菜单项被切换"""
        self.pause_requested.emit(checked)
    
    def is_visible(self) -> bool:
        """托盘图标是否可见"""
        return self._tray_icon.isVisible() if self._tray_icon else False
    
    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._is_paused
