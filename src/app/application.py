"""
应用程序入口模块
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ..shared.constants import APP_NAME
from .main_window import MainWindow


class ClipboardManagerApp:
    """剪贴板管理器应用"""
    
    def __init__(self):
        # 启用高 DPI 支持
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # 创建应用
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setApplicationDisplayName("剪贴板历史管理器")
        self._app.setApplicationVersion("1.0.0")
        
        # 创建主窗口
        self._main_window = MainWindow()
    
    def run(self) -> int:
        """运行应用"""
        # 显示主窗口
        self._main_window.show()
        
        # 显示托盘图标
        self._main_window._tray_manager.show()
        
        # 运行事件循环
        return self._app.exec()
    
    def get_main_window(self) -> MainWindow:
        """获取主窗口"""
        return self._main_window


def main():
    """主函数"""
    app = ClipboardManagerApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
