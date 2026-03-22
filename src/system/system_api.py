"""
系统 API 封装模块
封装系统调用，如打开文件、执行命令等
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote


class SystemAPI:
    """系统 API 封装"""
    
    @staticmethod
    def open_file_location(file_path: str) -> bool:
        """
        在文件管理器中打开文件所在位置
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            system = platform.system()
            
            if system == "Windows":
                # Windows: 使用 explorer 并选中文件
                subprocess.run(
                    ["explorer", "/select,", os.path.normpath(file_path)],
                    check=True
                )
            elif system == "Darwin":
                # macOS: 使用 open
                subprocess.run(["open", "-R", file_path], check=True)
            else:
                # Linux: 使用 xdg-open 打开目录
                dir_path = os.path.dirname(file_path)
                subprocess.run(["xdg-open", dir_path], check=True)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def open_directory(dir_path: str) -> bool:
        """
        打开目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        try:
            if not os.path.isdir(dir_path):
                return False
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(dir_path)
            elif system == "Darwin":
                subprocess.run(["open", dir_path], check=True)
            else:
                subprocess.run(["xdg-open", dir_path], check=True)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def open_file_with_default_app(file_path: str) -> bool:
        """
        使用默认应用打开文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        复制文本到剪贴板
        
        Args:
            text: 要复制的文本
            
        Returns:
            是否成功
        """
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                'exists': path.exists(),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'extension': path.suffix.lower(),
                'filename': path.name,
                'dirname': str(path.parent),
            }
        except Exception:
            return {
                'exists': False,
                'is_file': False,
                'is_dir': False,
                'size': 0,
                'modified_time': 0,
                'created_time': 0,
                'extension': '',
                'filename': '',
                'dirname': '',
            }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化后的字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def get_desktop_path() -> str:
        """获取桌面路径"""
        return str(Path.home() / "Desktop")
    
    @staticmethod
    def get_documents_path() -> str:
        """获取文档路径"""
        return str(Path.home() / "Documents")
    
    @staticmethod
    def get_downloads_path() -> str:
        """获取下载路径"""
        return str(Path.home() / "Downloads")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows 非法字符: < > : " / \ | ? *
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    @staticmethod
    def reveal_in_explorer(file_paths: List[str]) -> bool:
        """
        在资源管理器中显示多个文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            是否成功
        """
        if not file_paths:
            return False
        
        # 只显示第一个文件所在目录
        return SystemAPI.open_file_location(file_paths[0])
