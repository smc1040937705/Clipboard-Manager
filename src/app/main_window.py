"""
主窗口模块
实现剪贴板管理器的主界面
"""

from typing import Optional, List

from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLineEdit, QPushButton, QComboBox,
    QListWidget, QListWidgetItem, QLabel, QTextEdit,
    QMenu, QMessageBox, QFileDialog, QToolBar,
    QStatusBar, QFrame, QSizePolicy, QApplication
)

from ..shared.models import ClipboardRecord, WindowState
from ..shared.constants import (
    APP_NAME, APP_DISPLAY_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    LIST_WIDTH, PREVIEW_MIN_WIDTH, FilterType, ClipboardType
)
from ..shared.utils import format_timestamp
from ..storage.repository import ClipboardRepository
from ..core.clipboard_listener import ClipboardListener
from ..core.search_engine import SearchEngine, SearchOptions
from ..core.export_import import ExportImportManager
from ..system.tray_manager import TrayManager
from ..system.notification import NotificationManager
from ..system.system_api import SystemAPI
from .preview_widget import PreviewWidget
from .record_item import RecordItemWidget


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号
    record_selected = pyqtSignal(ClipboardRecord)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # 初始化组件
        self._repository = ClipboardRepository()
        self._search_engine = SearchEngine(self._repository)
        self._export_manager = ExportImportManager(self._repository)
        self._clipboard_listener = ClipboardListener(self)
        
        # 托盘管理器
        self._tray_manager = TrayManager(self)
        self._tray_manager.show_window_requested.connect(self.show_and_raise)
        self._tray_manager.pause_requested.connect(self._on_pause_requested)
        self._tray_manager.quit_requested.connect(self._on_quit_requested)
        
        # 通知管理器
        self._notification_manager = NotificationManager(
            self._tray_manager._tray_icon, self
        )
        
        # 当前选中的记录
        self._current_record: Optional[ClipboardRecord] = None
        self._records: List[ClipboardRecord] = []
        
        # 初始化 UI
        self._init_ui()
        self._init_menu()
        self._init_shortcuts()
        
        # 加载窗口状态
        self._load_window_state()
        
        # 连接剪贴板监听器
        self._clipboard_listener.set_content_handler(self._on_content_captured)
        self._clipboard_listener.start_listening()
        
        # 加载初始数据
        self._refresh_records()
    
    def _init_ui(self):
        """初始化 UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 工具栏区域
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("搜索剪贴板内容...")
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._search_edit.setClearButtonEnabled(True)
        toolbar_layout.addWidget(self._search_edit, 1)
        
        # 类型过滤
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("全部", FilterType.ALL)
        self._filter_combo.addItem("文本", FilterType.TEXT)
        self._filter_combo.addItem("图片", FilterType.IMAGE)
        self._filter_combo.addItem("文件", FilterType.FILE)
        self._filter_combo.addItem("收藏", FilterType.FAVORITE)
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._filter_combo)
        
        # 清空按钮
        self._clear_btn = QPushButton("清空")
        self._clear_btn.setToolTip("清空所有记录（保留收藏）")
        self._clear_btn.clicked.connect(self._on_clear_all)
        toolbar_layout.addWidget(self._clear_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # 分割器（列表/详情）
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：记录列表
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # 记录列表
        self._record_list = QListWidget()
        self._record_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._record_list.itemClicked.connect(self._on_record_selected)
        self._record_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._record_list.customContextMenuRequested.connect(self._on_list_context_menu)
        self._record_list.setSpacing(2)
        list_layout.addWidget(self._record_list)
        
        # 统计标签
        self._stats_label = QLabel("共 0 条记录")
        self._stats_label.setStyleSheet("color: gray; font-size: 12px;")
        list_layout.addWidget(self._stats_label)
        
        self._splitter.addWidget(list_widget)
        
        # 右侧：详情预览
        self._preview_widget = PreviewWidget()
        self._preview_widget.copy_requested.connect(self._on_copy_requested)
        self._preview_widget.delete_requested.connect(self._on_delete_requested)
        self._preview_widget.favorite_requested.connect(self._on_favorite_requested)
        self._preview_widget.pin_requested.connect(self._on_pin_requested)
        self._preview_widget.open_location_requested.connect(self._on_open_location)
        
        self._splitter.addWidget(self._preview_widget)
        
        # 设置分割器比例
        self._splitter.setSizes([LIST_WIDTH, PREVIEW_MIN_WIDTH])
        
        main_layout.addWidget(self._splitter, 1)
        
        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")
    
    def _init_menu(self):
        """初始化菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        export_json_action = QAction("导出为 JSON...", self)
        export_json_action.triggered.connect(self._on_export_json)
        file_menu.addAction(export_json_action)
        
        export_csv_action = QAction("导出为 CSV...", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        file_menu.addAction(export_csv_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("从文件导入...", self)
        import_action.triggered.connect(self._on_import)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        pause_action = QAction("暂停监听", self)
        pause_action.setCheckable(True)
        pause_action.triggered.connect(self._on_pause_toggled)
        edit_menu.addAction(pause_action)
        self._pause_action = pause_action
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _init_shortcuts(self):
        """初始化快捷键"""
        # Ctrl+F 聚焦搜索框
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._search_edit.setFocus)
        
        # Delete 删除选中项
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._on_delete_shortcut)
        
        # Escape 清除搜索
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self._on_escape_pressed)
        
        # Ctrl+R 刷新
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._refresh_records)
    
    def _load_window_state(self):
        """加载窗口状态"""
        settings = QSettings(APP_NAME, "MainWindow")
        
        # 窗口几何
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        else:
            self.resize(1200, 800)
            self.move(100, 100)
        
        # 窗口状态（最大化等）
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
        
        # 分割器位置
        if settings.contains("splitter"):
            self._splitter.restoreState(settings.value("splitter"))
        
        # 最后筛选条件
        if settings.contains("filterType"):
            self._filter_combo.setCurrentIndex(settings.value("filterType", 0))
        
        # 最后搜索文本
        if settings.contains("searchText"):
            self._search_edit.setText(settings.value("searchText", ""))
    
    def _save_window_state(self):
        """保存窗口状态"""
        settings = QSettings(APP_NAME, "MainWindow")
        
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("splitter", self._splitter.saveState())
        settings.setValue("filterType", self._filter_combo.currentIndex())
        settings.setValue("searchText", self._search_edit.text())
        
        if self._current_record:
            settings.setValue("lastSelectedId", self._current_record.id)
    
    def _refresh_records(self):
        """刷新记录列表"""
        keyword = self._search_edit.text().strip()
        filter_type = self._filter_combo.currentData()
        
        # 搜索
        options = SearchOptions(
            keyword=keyword,
            filter_type=filter_type,
            limit=100
        )
        results = self._search_engine.search(options)
        self._records = [r.record for r in results]
        
        # 更新列表
        self._record_list.clear()
        for record in self._records:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, record.id)
            
            # 创建自定义部件
            widget = RecordItemWidget(record)
            
            item.setSizeHint(widget.sizeHint())
            self._record_list.addItem(item)
            self._record_list.setItemWidget(item, widget)
        
        # 更新统计
        stats = self._repository.get_statistics()
        self._stats_label.setText(
            f"共 {stats['total']} 条 | 文本: {stats['text']} | "
            f"图片: {stats['image']} | 文件: {stats['file']} | 收藏: {stats['favorites']}"
        )
    
    def _on_content_captured(self, record: ClipboardRecord):
        """内容被捕获"""
        # 保存到数据库
        record_id = self._repository.create(record)
        record.id = record_id
        
        # 显示通知
        type_names = {ClipboardType.TEXT: "文本", ClipboardType.IMAGE: "图片", ClipboardType.FILE: "文件"}
        self._notification_manager.show_clipboard_captured(
            type_names.get(record.content_type, "内容"),
            record.display_title
        )
        
        # 刷新列表
        self._refresh_records()
    
    def _on_record_selected(self, item: QListWidgetItem):
        """记录被选中"""
        record_id = item.data(Qt.ItemDataRole.UserRole)
        record = self._repository.get_by_id(record_id)
        
        if record:
            self._current_record = record
            self._preview_widget.set_record(record)
            self.record_selected.emit(record)
    
    def _on_search_changed(self):
        """搜索文本改变"""
        self._refresh_records()
    
    def _on_filter_changed(self, index):
        """过滤器改变"""
        self._refresh_records()
    
    def _on_list_context_menu(self, position):
        """列表右键菜单"""
        item = self._record_list.itemAt(position)
        if not item:
            return
        
        record_id = item.data(Qt.ItemDataRole.UserRole)
        record = self._repository.get_by_id(record_id)
        if not record:
            return
        
        menu = QMenu(self)
        
        # 复制
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(lambda: self._copy_record(record))
        menu.addAction(copy_action)
        
        # 收藏
        fav_action = QAction(
            "取消收藏" if record.is_favorite else "收藏",
            self
        )
        fav_action.triggered.connect(lambda: self._toggle_favorite(record_id))
        menu.addAction(fav_action)
        
        # 置顶
        pin_action = QAction(
            "取消置顶" if record.is_pinned else "置顶",
            self
        )
        pin_action.triggered.connect(lambda: self._toggle_pin(record_id))
        menu.addAction(pin_action)
        
        menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_record(record_id))
        menu.addAction(delete_action)
        
        menu.exec(self._record_list.mapToGlobal(position))
    
    def _copy_record(self, record: ClipboardRecord):
        """复制记录到剪贴板"""
        if record.content_type == ClipboardType.TEXT:
            self._clipboard_listener.set_clipboard_text(record.text_content or "")
        elif record.content_type == ClipboardType.IMAGE and record.image_data:
            self._clipboard_listener.set_clipboard_image(record.image_data)
        
        self._status_bar.showMessage("已复制到剪贴板", 2000)
    
    def _delete_record(self, record_id: int):
        """删除记录"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._repository.delete(record_id)
            self._refresh_records()
            self._preview_widget.clear()
            self._status_bar.showMessage("记录已删除", 2000)
    
    def _toggle_favorite(self, record_id: int):
        """切换收藏状态"""
        self._repository.toggle_favorite(record_id)
        self._refresh_records()
    
    def _toggle_pin(self, record_id: int):
        """切换置顶状态"""
        self._repository.toggle_pin(record_id)
        self._refresh_records()
    
    def _on_clear_all(self):
        """清空所有记录"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有记录吗？\n（收藏的记录将被保留）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            count = self._repository.clear_all(keep_favorites=True)
            self._refresh_records()
            self._preview_widget.clear()
            self._status_bar.showMessage(f"已清空 {count} 条记录", 2000)
    
    def _on_copy_requested(self, record: ClipboardRecord):
        """预览区请求复制"""
        self._copy_record(record)
    
    def _on_delete_requested(self, record: ClipboardRecord):
        """预览区请求删除"""
        if record.id:
            self._delete_record(record.id)
    
    def _on_favorite_requested(self, record: ClipboardRecord):
        """预览区请求收藏"""
        if record.id:
            self._toggle_favorite(record.id)
    
    def _on_pin_requested(self, record: ClipboardRecord):
        """预览区请求置顶"""
        if record.id:
            self._toggle_pin(record.id)
    
    def _on_open_location(self, file_path: str):
        """打开文件位置"""
        if SystemAPI.open_file_location(file_path):
            self._status_bar.showMessage(f"已打开: {file_path}", 2000)
        else:
            QMessageBox.warning(self, "错误", f"无法打开文件位置: {file_path}")
    
    def _on_export_json(self):
        """导出为 JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出为 JSON", "clipboard_export.json", "JSON Files (*.json)"
        )
        
        if file_path:
            self._export_manager.export_to_json(file_path=file_path)
            self._status_bar.showMessage(f"已导出到: {file_path}", 3000)
    
    def _on_export_csv(self):
        """导出为 CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出为 CSV", "clipboard_export.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            self._export_manager.export_to_csv(file_path=file_path)
            self._status_bar.showMessage(f"已导出到: {file_path}", 3000)
    
    def _on_import(self):
        """导入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入文件", "", "JSON/CSV Files (*.json *.csv)"
        )
        
        if not file_path:
            return
        
        # 验证文件
        validation = self._export_manager.validate_import_file(file_path)
        if not validation['valid']:
            QMessageBox.warning(self, "导入失败", validation['error'])
            return
        
        # 确认导入
        reply = QMessageBox.question(
            self, "确认导入",
            f"文件包含 {validation['record_count']} 条记录，确定要导入吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 执行导入
        if validation['format'] == 'json':
            result = self._export_manager.import_from_json(file_path)
        else:
            result = self._export_manager.import_from_csv(file_path)
        
        if result['success']:
            self._refresh_records()
            msg = f"导入完成: {result['imported']} 条成功, {result['skipped']} 条跳过"
            if result['errors']:
                msg += f"\n{len(result['errors'])} 个错误"
            QMessageBox.information(self, "导入完成", msg)
        else:
            QMessageBox.warning(self, "导入失败", "\n".join(result['errors']))
    
    def _on_pause_requested(self, pause: bool):
        """托盘请求暂停/恢复"""
        self._on_pause_toggled(pause)
        self._pause_action.setChecked(pause)
    
    def _on_pause_toggled(self, checked: bool):
        """暂停/恢复监听"""
        if checked:
            self._clipboard_listener.pause()
            self._tray_manager.set_paused(True)
            self._status_bar.showMessage("监听已暂停", 2000)
        else:
            self._clipboard_listener.resume()
            self._tray_manager.set_paused(False)
            self._status_bar.showMessage("监听已恢复", 2000)
    
    def _on_quit_requested(self):
        """托盘请求退出"""
        self._save_window_state()
        self._clipboard_listener.stop_listening()
        QApplication.quit()
    
    def _on_delete_shortcut(self):
        """Delete 快捷键"""
        if self._current_record and self._current_record.id:
            self._delete_record(self._current_record.id)
    
    def _on_escape_pressed(self):
        """Escape 快捷键"""
        self._search_edit.clear()
        self._search_edit.clearFocus()
    
    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self, f"关于 {APP_DISPLAY_NAME}",
            f"<h2>{APP_DISPLAY_NAME}</h2>"
            f"<p>版本: 1.0.0</p>"
            f"<p>一个功能强大的剪贴板历史管理器</p>"
            f"<p>支持文本、图片、文件路径的记录和管理</p>"
        )
    
    def show_and_raise(self):
        """显示并提升窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存状态
        self._save_window_state()
        
        # 最小化到托盘而不是关闭
        if self._tray_manager.is_visible():
            self.hide()
            self._tray_manager.show_notification(
                APP_DISPLAY_NAME,
                "程序已最小化到系统托盘",
                2000
            )
            event.ignore()
        else:
            self._clipboard_listener.stop_listening()
            event.accept()
