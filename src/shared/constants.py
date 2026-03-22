"""
常量定义模块
包含应用级别的常量、枚举和配置
"""

from enum import Enum, IntEnum
from pathlib import Path


class ClipboardType(IntEnum):
    """剪贴板内容类型枚举"""
    TEXT = 1
    IMAGE = 2
    FILE = 3


class SortOrder(IntEnum):
    """排序方式枚举"""
    TIME_DESC = 1
    TIME_ASC = 2


class FilterType(IntEnum):
    """过滤类型枚举"""
    ALL = 0
    TEXT = 1
    IMAGE = 2
    FILE = 3
    FAVORITE = 4


# 应用信息
APP_NAME = "ClipboardManager"
APP_DISPLAY_NAME = "剪贴板历史管理器"
APP_VERSION = "1.0.0"

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "clipboard.db"

# 数据库配置
DB_TIMEOUT = 30
MAX_TEXT_LENGTH = 100000  # 最大文本长度
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 最大图片大小 10MB
MAX_HISTORY_ITEMS = 1000  # 最大历史记录数

# UI 配置
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
LIST_WIDTH = 350
PREVIEW_MIN_WIDTH = 400

# 剪贴板监听配置
CLIPBOARD_DEBOUNCE_MS = 500  # 防抖时间（毫秒）
CLIPBOARD_MAX_DUPLICATE_CHECK = 50  # 检查重复的最大记录数

# 导出配置
EXPORT_FORMATS = ["json", "csv"]
JSON_EXPORT_VERSION = "1.0"

# 托盘图标提示
TRAY_TOOLTIP = "剪贴板历史管理器 - 运行中"
TRAY_TOOLTIP_PAUSED = "剪贴板历史管理器 - 已暂停"

# 通知配置
NOTIFICATION_DURATION_MS = 3000
