# 剪贴板历史管理器 (Clipboard Manager)

一个使用 Python + PyQt6 构建的本地剪贴板历史管理器，支持文本、图片、文件路径的记录和管理。

## 功能特性

### 核心功能
- **实时监听剪贴板**：自动捕获文本、图片、文件路径
- **历史记录管理**：支持收藏、置顶、删除、批量清空
- **详情预览**：
  - 文本可编辑并重新复制
  - 图片支持缩放预览
  - 文件路径支持一键在系统文件管理器中定位
- **智能搜索**：全文搜索（文本内容 + 文件名），支持关键词高亮
- **类型过滤**：按文本/图片/文件/收藏过滤
- **导入导出**：支持 JSON/CSV 格式导出，支持从 JSON 导入备份
- **系统托盘**：最小化到系统托盘，支持托盘菜单

### 快捷键
- `Ctrl+F`：聚焦搜索框
- `Delete`：删除选中记录
- `Escape`：清除搜索
- `Ctrl+R`：刷新列表
- `Ctrl+Q`：退出应用

## 安装要求

- Python 3.8+
- PyQt6 6.4.0+

## 安装步骤

### 1. 克隆/下载项目

```bash
cd clipboard-manager
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
```

### 3. 激活虚拟环境

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

## 启动应用

```bash
python main.py
```

## 运行测试

```bash
python -m unittest discover tests
```

或运行单个测试文件：

```bash
python -m unittest tests.test_models
python -m unittest tests.test_storage
python -m unittest tests.test_utils
python -m unittest tests.test_search
python -m unittest tests.test_export_import
```

## 项目结构

```
clipboard-manager/
├── main.py                    # 应用入口
├── requirements.txt           # 依赖文件
├── README.md                  # 说明文档
├── data/                      # 数据目录（自动创建）
│   └── clipboard.db          # SQLite 数据库
├── src/
│   ├── app/                  # UI 入口与主窗口
│   │   ├── __init__.py
│   │   ├── application.py    # 应用类
│   │   ├── main_window.py    # 主窗口
│   │   ├── preview_widget.py # 预览控件
│   │   └── record_item.py    # 记录项控件
│   ├── core/                 # 业务逻辑
│   │   ├── __init__.py
│   │   ├── clipboard_listener.py  # 剪贴板监听
│   │   ├── search_engine.py       # 搜索引擎
│   │   └── export_import.py       # 导入导出
│   ├── storage/              # SQLite 仓储
│   │   ├── __init__.py
│   │   ├── database.py       # 数据库管理
│   │   └── repository.py     # 数据仓库
│   ├── system/               # 系统调用封装
│   │   ├── __init__.py
│   │   ├── tray_manager.py   # 托盘管理
│   │   ├── notification.py   # 通知管理
│   │   └── system_api.py     # 系统 API
│   └── shared/               # 共享模块
│       ├── __init__.py
│       ├── constants.py      # 常量定义
│       ├── models.py         # 数据模型
│       └── utils.py          # 工具函数
└── tests/                    # 测试目录
    ├── __init__.py
    ├── test_models.py
    ├── test_storage.py
    ├── test_utils.py
    ├── test_search.py
    └── test_export_import.py
```

## 使用说明

### 基本操作

1. **查看历史记录**：启动后自动监听剪贴板，所有复制的内容都会显示在左侧列表中
2. **搜索记录**：在顶部搜索框输入关键词，实时过滤记录
3. **筛选类型**：使用类型下拉框筛选文本/图片/文件/收藏
4. **查看详情**：点击列表中的记录，在右侧预览区查看详情
5. **复制内容**：在预览区点击"复制到剪贴板"按钮
6. **收藏/置顶**：点击预览区的 ☆/📌 按钮
7. **删除记录**：点击预览区的 🗑 按钮或按 Delete 键

### 导入导出

- **导出**：文件菜单 → 导出为 JSON/CSV
- **导入**：文件菜单 → 从文件导入

### 系统托盘

- 关闭窗口时应用会最小化到系统托盘
- 双击托盘图标显示主窗口
- 右键托盘图标可暂停监听或退出应用

## 技术要点

1. **剪贴板监听**：使用 `QClipboard.dataChanged` 信号，加入去重与防抖
2. **本地存储**：使用 SQLite，图片以二进制存储，文本建立 FTS 全文索引
3. **窗口状态**：使用 `QSettings` 持久化窗口大小、位置、筛选条件等
4. **系统 API**：支持剪贴板操作、系统托盘、桌面通知、打开文件位置

## 数据存储

- 数据库文件位于 `data/clipboard.db`
- 使用 SQLite 存储所有记录
- 图片以二进制 BLOB 存储
- 文本内容支持全文搜索（FTS5）

## 注意事项

1. 最大文本长度限制：100,000 字符
2. 最大图片大小限制：10 MB
3. 最大历史记录数：1,000 条（自动清理旧记录，保留收藏和置顶）

## 许可证

MIT License
