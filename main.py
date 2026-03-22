"""
剪贴板历史管理器
入口文件
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app.application import main

if __name__ == "__main__":
    main()
