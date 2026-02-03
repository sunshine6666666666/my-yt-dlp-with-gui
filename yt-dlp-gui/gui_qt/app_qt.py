import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListView, QStyledItemDelegate,
                             QStyle, QProgressBar, QLabel, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor

from core.config import Config
from core.queue_manager import QueueManager
from core.task import TaskStatus
from .models import TaskListModel
from .settings_qt import SettingsDialog
from core.logger import setup_logger

logger = setup_logger("GUI")

class TaskDelegate(QStyledItemDelegate):
    """自定义任务渲染委派"""
    def __init__(self, parent=None, on_pause=None, on_resume=None, on_cancel=None, on_retry=None):
        super().__init__(parent)
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_cancel = on_cancel
        self.on_retry = on_retry

    def paint(self, painter, option, index):
        task = index.data(Qt.UserRole)
        if not task: return

        painter.save()
        
        # 背景
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#e3f2fd"))
        
        # 标题 (上部)
        rect = option.rect
        title = task.title if task.title else task.url
        title_rect = rect.adjusted(10, 5, -10, -55)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine, title)
        
        # 进度条背景 (中部)
        bar_rect = rect.adjusted(10, 30, -10, -35)
        painter.fillRect(bar_rect, QColor("#eeeeee"))
        # 进度填充
        progress_width = int(bar_rect.width() * (task.progress / 100.0))
        painter.fillRect(bar_rect.adjusted(0, 0, progress_width - bar_rect.width(), 0), QColor("#4caf50"))

        # 状态文字 (下部)
        status_text = f"状态: {task.status.value}"
        if task.status == TaskStatus.DOWNLOADING:
            status_text = f"{task.progress:.1f}% | {task.speed} | ETA: {task.eta}"
        elif task.status == TaskStatus.FAILED:
            status_text = f"❌ 失败: {task.error[:60]}"
        elif task.status == TaskStatus.COMPLETED:
            status_text = "✅ 下载完成"
        
        status_rect = rect.adjusted(10, 55, -10, -5)
        painter.drawText(status_rect, Qt.AlignLeft | Qt.AlignVCenter, status_text)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 80)

class AppWindow(QMainWindow):
    def __init__(self, yt_dlp_path):
        super().__init__()
        self.yt_dlp_path = yt_dlp_path
        self.setWindowTitle("YT-DLP 下载器 (Qt 版)")
        self.setMinimumSize(800, 600)
        
        # 初始化核心
        _gui_dir = os.path.dirname(os.path.abspath(__file__))
        _root_dir = os.path.dirname(_gui_dir)
        config_path = os.path.join(_root_dir, "config.json")
        self.config = Config(config_path)
        self.queue_manager = QueueManager(max_concurrent=5, config=self.config, yt_dlp_path=yt_dlp_path)
        self._cookie_error_prompted = False
        self._last_clicked_task_id = None
        
        self._init_ui()
        
        # 定时刷新 UI（兜底）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_ui)
        self.timer.start(1000)

        # 主动回调刷新（更及时）
        self.queue_manager.on_update = lambda _tid: self._refresh_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 顶部输入区
        top_layout = QHBoxLayout()
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("在这里粘贴视频链接...")
        self.edit_url.setFixedHeight(35)
        top_layout.addWidget(self.edit_url)
        
        btn_add = QPushButton("添加下载")
        btn_add.setFixedHeight(35)
        btn_add.clicked.connect(self._add_task)
        top_layout.addWidget(btn_add)
        
        btn_settings = QPushButton("⚙️ 设置")
        btn_settings.setFixedHeight(35)
        btn_settings.clicked.connect(self._open_settings)
        top_layout.addWidget(btn_settings)
        
        layout.addLayout(top_layout)

        # 错误提示条（非弹窗，避免线程问题）
        self.error_banner = QLabel("")
        self.error_banner.setStyleSheet("color: #b00020; background: #ffe9e9; padding: 6px; border: 1px solid #f1bcbc;")
        self.error_banner.setVisible(False)
        layout.addWidget(self.error_banner)

        # 列表区
        self.list_view = QListView()
        self.model = TaskListModel()
        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(TaskDelegate(self))
        self.list_view.setSelectionMode(QListView.SingleSelection)
        self.list_view.setSelectionBehavior(QListView.SelectRows)
        self.list_view.setFocusPolicy(Qt.StrongFocus)
        self.list_view.setEditTriggers(QListView.NoEditTriggers)
        # 强化选中高亮可见性（防止样式覆盖）
        self.list_view.setStyleSheet("QListView::item:selected { background: #e3f2fd; }")
        
        def _on_clicked(index):
            task = self.model.data(index, Qt.UserRole)
            self._last_clicked_task_id = task.id if task else None
        self.list_view.clicked.connect(_on_clicked)
        
        def _on_current_changed(current, _previous):
            task = self.model.data(current, Qt.UserRole)
            self._last_clicked_task_id = task.id if task else None
        self.list_view.selectionModel().currentChanged.connect(_on_current_changed)
        
        layout.addWidget(self.list_view)

        # 底部控制区（针对选中项）
        btn_layout = QHBoxLayout()
        self.btn_pause = QPushButton("暂停")
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_resume = QPushButton("继续")
        self.btn_resume.clicked.connect(self._on_resume)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_retry = QPushButton("重试")
        self.btn_retry.clicked.connect(self._on_retry)
        
        for b in [self.btn_pause, self.btn_resume, self.btn_cancel, self.btn_retry]:
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

    def _add_task(self):
        url = self.edit_url.text().strip()
        logger.info(f"Add button clicked, URL: {url}")
        if url:
            try:
                task_id = self.queue_manager.add_task(url)
                logger.info(f"Task enqueued with id: {task_id}")
            except Exception as e:
                logger.error(f"Add task failed: {e}")
            self.edit_url.clear()
            self._refresh_ui()

    def _open_settings(self):
        logger.info("Settings opened")
        diag = SettingsDialog(self, self.config)
        if diag.exec():
            # If settings were saved (accepted), clear cookie error state
            self._cookie_error_prompted = False
            self.error_banner.setVisible(False)
            logger.info("Settings saved, cleared cookie error state")

    def _refresh_ui(self):
        # 保存当前选中任务的 ID
        selected_id = self._get_selected_id()
        if not selected_id and self._last_clicked_task_id:
            selected_id = self._last_clicked_task_id
        
        self.model.refresh(self.queue_manager.get_all_tasks())
        
        # 恢复选中状态
        if selected_id:
            for row in range(self.model.rowCount()):
                index = self.model.index(row, 0)
                task = self.model.data(index, Qt.UserRole)
                if task and task.id == selected_id:
                    # 使用 QItemSelectionModel 兼容 PySide6
                    from PySide6.QtCore import QItemSelectionModel
                    self.list_view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
                    self.list_view.setCurrentIndex(index)
                    break
        
        # Detect cookie invalid errors and prompt user once
        for task in self.queue_manager.get_all_tasks():
            if getattr(task, "error", "") and "Cookie 已失效" in task.error:
                if not self._cookie_error_prompted:
                    self._cookie_error_prompted = True
                    def _prompt():
                        self._show_cookie_prompt(task.id)
                    QTimer.singleShot(0, _prompt)
                    # 非弹窗提示条
                    self.error_banner.setText("Cookie 已失效，请重新导入 Cookie（点击设置导入）")
                    self.error_banner.setVisible(True)
                break

    def _show_cookie_prompt(self, task_id):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Cookie 已失效")
        msg.setText("YouTube Cookie 已失效，请重新导入 Cookie。")
        msg.setInformativeText("是否现在打开设置导入新的 Cookie？")
        msg.setWindowModality(Qt.ApplicationModal)
        open_btn = msg.addButton("打开设置", QMessageBox.AcceptRole)
        msg.addButton("稍后处理", QMessageBox.RejectRole)
        # Keep reference to avoid GC before showing
        self._cookie_msg = msg
        msg.open()
        msg.raise_()
        msg.activateWindow()
        def _on_finished(_result):
            if msg.clickedButton() == open_btn:
                self._open_settings()
        msg.finished.connect(_on_finished)

    def _get_selected_id(self):
        indexes = self.list_view.selectedIndexes()
        if indexes:
            task = self.model.data(indexes[0], Qt.UserRole)
            return task.id
        if self._last_clicked_task_id:
            return self._last_clicked_task_id
        return None

    def _on_pause(self):
        tid = self._get_selected_id()
        logger.info(f"Pause action for task: {tid}")
        if tid: self.queue_manager.pause_task(tid)

    def _on_resume(self):
        tid = self._get_selected_id()
        logger.info(f"Resume action for task: {tid}")
        if tid: self.queue_manager.resume_task(tid)

    def _on_cancel(self):
        tid = self._get_selected_id()
        logger.info(f"Cancel action for task: {tid}")
        if tid: self.queue_manager.cancel_task(tid)

    def _on_retry(self):
        tid = self._get_selected_id()
        logger.info(f"Retry action for task: {tid}")
        if tid: self.queue_manager.retry_task(tid)

    def closeEvent(self, event):
        super().closeEvent(event)
