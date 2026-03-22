"""
工具函数模块
提供通用的辅助函数
"""

import os
import re
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path


def format_timestamp(dt: datetime) -> str:
    """格式化时间戳为显示字符串"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "刚刚"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60} 分钟前"
        else:
            return f"{diff.seconds // 3600} 小时前"
    elif diff.days == 1:
        return "昨天 " + dt.strftime("%H:%M")
    elif diff.days < 7:
        return f"{diff.days} 天前"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def highlight_text(text: str, keyword: str, case_sensitive: bool = False) -> Tuple[str, List[Tuple[int, int]]]:
    """
    高亮文本中的关键词
    
    返回: (高亮后的HTML文本, 匹配位置列表)
    """
    if not keyword:
        return text, []
    
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.escape(keyword)
    
    matches = []
    for match in re.finditer(pattern, text, flags):
        matches.append((match.start(), match.end()))
    
    if not matches:
        return text, []
    
    # 构建高亮 HTML
    result = []
    last_end = 0
    for start, end in matches:
        result.append(text[last_end:start])
        result.append(f'<span style="background-color: #FFD700; color: black;">')
        result.append(text[start:end])
        result.append('</span>')
        last_end = end
    result.append(text[last_end:])
    
    return ''.join(result), matches


def get_file_icon_path(file_path: str) -> str:
    """获取文件图标路径（返回系统图标或默认图标）"""
    # 在实际实现中，可以返回不同文件类型的图标
    ext = Path(file_path).suffix.lower()
    
    icon_map = {
        '.txt': 'text',
        '.doc': 'document',
        '.docx': 'document',
        '.pdf': 'pdf',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.mp3': 'audio',
        '.mp4': 'video',
        '.zip': 'archive',
        '.rar': 'archive',
        '.exe': 'executable',
    }
    
    return icon_map.get(ext, 'file')


def open_file_location(file_path: str) -> bool:
    """在文件管理器中打开文件所在位置"""
    try:
        import subprocess
        import platform
        
        if not os.path.exists(file_path):
            return False
        
        system = platform.system()
        
        if system == "Windows":
            # Windows: 使用 explorer 并选中文件
            subprocess.run(["explorer", "/select,", os.path.normpath(file_path)], check=True)
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


def get_image_format_from_data(data: bytes) -> Optional[str]:
    """从图片二进制数据识别格式"""
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'PNG'
    elif data.startswith(b'\xff\xd8'):
        return 'JPEG'
    elif data.startswith(b'GIF89a') or data.startswith(b'GIF87a'):
        return 'GIF'
    elif data.startswith(b'BM'):
        return 'BMP'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'WEBP'
    return None


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # Windows 非法字符: < > : " / \ | ? *
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def generate_unique_id() -> str:
    """生成唯一 ID"""
    import uuid
    return str(uuid.uuid4())
