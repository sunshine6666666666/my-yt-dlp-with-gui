import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QCheckBox, QMessageBox)

class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.config = config
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 下载路径
        layout.addWidget(QLabel("下载保存路径:"))
        path_layout = QHBoxLayout()
        self.edit_path = QLineEdit()
        self.edit_path.setText(self.config.get("download_path") or os.path.expanduser("~/Downloads"))
        path_layout.addWidget(self.edit_path)
        btn_browse = QPushButton("浏览...")
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        layout.addSpacing(10)

        # Cookie 设置
        layout.addWidget(QLabel("Cookie 设置 (绕过机器人检测):"))
        self.lbl_cookie_status = QLabel(self._get_cookie_text())
        self.lbl_cookie_status.setStyleSheet("color: blue;")
        layout.addWidget(self.lbl_cookie_status)

        cookie_btn_layout = QHBoxLayout()
        btn_import = QPushButton("导入 Cookie (.txt)")
        btn_import.clicked.connect(self._import_cookie)
        btn_clear = QPushButton("清理 Cookie")
        btn_clear.clicked.connect(self._clear_cookie)
        cookie_btn_layout.addWidget(btn_import)
        cookie_btn_layout.addWidget(btn_clear)
        layout.addLayout(cookie_btn_layout)

        layout.addSpacing(10)

        # 安全模式
        self.cb_safe = QCheckBox("启用安全模式 (限制速度 + 随机间隔)")
        self.cb_safe.setChecked(self.config.get("safe_mode") is not False) # 默认开启
        layout.addWidget(self.cb_safe)

        layout.addStretch()

        # 保存按钮
        btn_save = QPushButton("保存并关闭")
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_settings)
        layout.addWidget(btn_save)

    def _get_cookie_text(self):
        path = self.config.get("cookies_path")
        if not path: return "当前状态：未加载 Cookie"
        return f"当前路径: ...{path[-40:]}" if len(path) > 40 else f"当前路径: {path}"

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载目录", self.edit_path.text())
        if path:
            self.edit_path.setText(path)

    def _import_cookie(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Cookie 文件", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    if "# Netscape HTTP Cookie File" not in f.read(100):
                        QMessageBox.critical(self, "错误", "该文件不是有效的 Netscape 格式 Cookie 文件")
                        return
                self.config.set("cookies_path", path)
                self.lbl_cookie_status.setText(self._get_cookie_text())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取失败: {e}")

    def _clear_cookie(self):
        self.config.set("cookies_path", "")
        self.lbl_cookie_status.setText(self._get_cookie_text())

    def _save_settings(self):
        path = self.edit_path.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.critical(self, "错误", "下载目录无效，请重新选择")
            return
        self.config.set("download_path", path)
        self.config.set("safe_mode", self.cb_safe.isChecked())
        self.accept()
