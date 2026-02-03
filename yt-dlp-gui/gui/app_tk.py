import os
import sys
import tkinter as tk
from tkinter import filedialog

# Ensure core module is importable
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from core.config import Config
from core.queue_manager import QueueManager
from core.task import TaskStatus


def _agent_log(hypothesis_id, location, message, data, run_id="pre3"):
    # #region agent log
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
            import json as _json
            _f.write(_json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion agent log


class TaskCard(tk.Frame):
    """单个下载任务的卡片组件 (Tkinter 版本)"""

    def __init__(self, master, task, on_pause, on_resume, on_cancel, on_retry):
        super().__init__(master, bd=1, relief="solid")
        self.task = task
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_cancel = on_cancel
        self.on_retry = on_retry

        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)

        display_title = self.task.title if self.task.title else self.task.url
        if len(display_title) > 50:
            display_title = display_title[:47] + "..."

        self.lbl_title = tk.Label(self, text=display_title, font=("Arial", 13, "bold"), anchor="w")
        self.lbl_title.grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        self.progress_bar = tk.Canvas(self, height=14, bd=0, highlightthickness=0, bg="#e6e6e6")
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

        self.lbl_status = tk.Label(self, text=self._get_status_text(), anchor="w")
        self.lbl_status.grid(row=2, column=0, sticky="w", padx=8, pady=(0, 4))

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        self.btn_action = tk.Button(btn_frame, text=self._get_action_text(), command=self._on_action, width=6)
        self.btn_action.grid(row=0, column=0, padx=(0, 6))

        self.btn_cancel = tk.Button(btn_frame, text="取消", command=self.on_cancel, width=6)
        self.btn_cancel.grid(row=0, column=1, padx=6)

        self.btn_retry = tk.Button(btn_frame, text="重试", command=self.on_retry, width=6)
        self.btn_retry.grid(row=0, column=2, padx=6)

        self._update_button_states()

    def _get_status_text(self):
        s = self.task.status
        if s == TaskStatus.DOWNLOADING:
            return f"{self.task.progress:.1f}% | {self.task.speed} | ETA: {self.task.eta}"
        if s == TaskStatus.COMPLETED:
            return "已完成"
        if s == TaskStatus.FAILED:
            err = self.task.error[:30] + "..." if len(self.task.error) > 30 else self.task.error
            return f"失败: {err}"
        if s == TaskStatus.PAUSED:
            return "已暂停"
        if s == TaskStatus.CANCELLED:
            return "已取消"
        return "等待中"

    def _get_action_text(self):
        s = self.task.status
        if s == TaskStatus.DOWNLOADING:
            return "暂停"
        if s == TaskStatus.PAUSED:
            return "继续"
        return "-"

    def _on_action(self):
        s = self.task.status
        if s == TaskStatus.DOWNLOADING:
            self.on_pause()
        elif s == TaskStatus.PAUSED:
            self.on_resume()

    def _update_button_states(self):
        action_text = self._get_action_text()
        self.btn_action.config(text=action_text)
        self.btn_action.config(state="normal" if action_text != "-" else "disabled")

        can_retry = self.task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.COMPLETED)
        self.btn_retry.config(state="normal" if can_retry else "disabled")

    def update_display(self):
        title = self.task.title if self.task.title else self.task.url
        if len(title) > 50:
            title = title[:47] + "..."
        self.lbl_title.config(text=title)
        self._update_progress_bar()
        self.lbl_status.config(text=self._get_status_text())
        self._update_button_states()

    def _update_progress_bar(self):
        self.progress_bar.delete("bar")
        width = max(self.progress_bar.winfo_width(), 1)
        percent = max(0.0, min(100.0, self.task.progress)) / 100.0
        fill_width = int(width * percent)
        self.progress_bar.create_rectangle(0, 0, fill_width, 14, fill="#4caf50", width=0, tags="bar")
        self.progress_bar.create_rectangle(fill_width, 0, width, 14, fill="#e6e6e6", width=0, tags="bar")


class SettingsDialog(tk.Toplevel):
    """设置弹窗 (Tkinter 版本)"""

    def __init__(self, master, config):
        super().__init__(master)
        self.title("设置")
        self.geometry("520x280")
        self.resizable(False, False)
        self.cfg = config

        self.grab_set()

        # 路径设置
        tk.Label(self, text="下载保存路径:").pack(pady=(18, 8))
        path_frame = tk.Frame(self)
        path_frame.pack(fill="x", padx=16)
        # Make entry visually obvious on macOS Tk (high contrast)
        _path_wrap = tk.Frame(path_frame, bg="#ff3b30")  # red border
        _path_wrap.pack(side="left", fill="x", expand=True, padx=(0, 8))
        _path_wrap.columnconfigure(0, weight=1)
        self.entry_path = tk.Entry(
            _path_wrap,
            bg="white",
            fg="black",
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground="#ff3b30",
            highlightcolor="#ff3b30",
            font=("Arial", 13),
        )
        self.entry_path.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        current_path = config.get("download_path") or os.path.expanduser("~/Downloads")
        self.entry_path.insert(0, current_path)
        tk.Button(path_frame, text="浏览...", command=self._browse).pack(side="left")

        # Cookie 设置
        tk.Label(self, text="Cookie 设置 (用于绕过机器人检测):").pack(pady=(18, 8))
        cookie_frame = tk.Frame(self)
        cookie_frame.pack(fill="x", padx=16)
        
        self.lbl_cookie = tk.Label(cookie_frame, text=self._get_cookie_display(), fg="blue", wraplength=480)
        self.lbl_cookie.pack(pady=2)

        btn_cookie_frame = tk.Frame(self)
        btn_cookie_frame.pack(pady=10)
        tk.Button(btn_cookie_frame, text="导入 Cookie (.txt)", command=self._import_cookie).pack(side="left", padx=5)
        tk.Button(btn_cookie_frame, text="清理 Cookie", command=self._clear_cookie).pack(side="left", padx=5)

        # 保存按钮
        tk.Button(self, text="保存并关闭", command=self._save, width=15, bg="#4caf50").pack(pady=(10, 18))

        # #region agent log
        try:
            _data = {
                "sessionId": "debug-session",
                "runId": "pre",
                "hypothesisId": "H4",
                "location": "app_tk.py:SettingsDialog.__init__",
                "message": "settings_widgets_created",
                "data": {
                    "entry_path_winfo_width": self.entry_path.winfo_width(),
                    "entry_path_visible": bool(self.entry_path.winfo_ismapped())
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after_idle(self._debug_log_settings_layout)
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after_idle(lambda: _agent_log(
                "H4",
                "app_tk.py:SettingsDialog.after_idle",
                "path_frame_layout",
                {
                    "toplevel_w": self.winfo_width(),
                    "toplevel_h": self.winfo_height(),
                    "path_frame_w": path_frame.winfo_width(),
                    "path_frame_h": path_frame.winfo_height(),
                    "wrap_w": _path_wrap.winfo_width(),
                    "wrap_h": _path_wrap.winfo_height(),
                    "entry_mapped": bool(self.entry_path.winfo_ismapped()),
                    "entry_w": self.entry_path.winfo_width(),
                    "entry_h": self.entry_path.winfo_height(),
                    "entry_x": self.entry_path.winfo_x(),
                    "entry_y": self.entry_path.winfo_y(),
                    "manager": self.entry_path.winfo_manager()
                },
                run_id="pre4"
            ))
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.bind("<Map>", lambda e: _agent_log(
                "H4",
                "app_tk.py:SettingsDialog.<Map>",
                "settings_mapped",
                {"toplevel_mapped": bool(self.winfo_ismapped()), "w": self.winfo_width(), "h": self.winfo_height(), "x": self.winfo_x(), "y": self.winfo_y()},
                run_id="pre3"
            ))
            self.entry_path.bind("<Map>", lambda e: _agent_log(
                "H4",
                "app_tk.py:SettingsDialog.entry_path.<Map>",
                "settings_entry_mapped",
                {"mapped": bool(self.entry_path.winfo_ismapped()), "w": self.entry_path.winfo_width(), "h": self.entry_path.winfo_height(), "x": self.entry_path.winfo_x(), "y": self.entry_path.winfo_y(), "manager": self.entry_path.winfo_manager(), "bg": str(self.entry_path.cget("bg")), "bd": int(self.entry_path.cget("bd")), "relief": str(self.entry_path.cget("relief")), "hlt": int(self.entry_path.cget("highlightthickness"))},
                run_id="pre3"
            ))
        except Exception:
            pass
        # #endregion agent log

    def _debug_log_settings_layout(self):
        # #region agent log
        try:
            self.update_idletasks()
            _data = {
                "sessionId": "debug-session",
                "runId": "pre2",
                "hypothesisId": "H4",
                "location": "app_tk.py:SettingsDialog._debug_log_settings_layout",
                "message": "settings_layout_state",
                "data": {
                    "toplevel_mapped": bool(self.winfo_ismapped()),
                    "toplevel_w": self.winfo_width(),
                    "toplevel_h": self.winfo_height(),
                    "entry_path_manager": str(self.entry_path.winfo_manager()),
                    "entry_path_mapped": bool(self.entry_path.winfo_ismapped()),
                    "entry_path_w": self.entry_path.winfo_width(),
                    "entry_path_h": self.entry_path.winfo_height(),
                    "entry_path_reqw": self.entry_path.winfo_reqwidth(),
                    "path_frame_mapped": bool(self.entry_path.master.winfo_ismapped()),
                    "path_frame_manager": str(self.entry_path.master.winfo_manager()),
                    "path_frame_w": self.entry_path.master.winfo_width(),
                    "path_frame_reqw": self.entry_path.master.winfo_reqwidth(),
                    "path_frame_children": len(self.entry_path.master.winfo_children()),
                    "path_frame_pack_slaves": len(self.entry_path.master.pack_slaves())
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after(0, self._debug_log_settings_post_layout)
        except Exception:
            pass
        # #endregion agent log

    def _debug_log_settings_post_layout(self):
        # #region agent log
        try:
            _data = {
                "sessionId": "debug-session",
                "runId": "pre",
                "hypothesisId": "H4",
                "location": "app_tk.py:SettingsDialog._debug_log_settings_post_layout",
                "message": "settings_post_layout",
                "data": {
                    "entry_path_winfo_width": self.entry_path.winfo_width(),
                    "entry_path_winfo_height": self.entry_path.winfo_height(),
                    "entry_path_mapped": bool(self.entry_path.winfo_ismapped()),
                    "entry_path_x": self.entry_path.winfo_x(),
                    "entry_path_y": self.entry_path.winfo_y(),
                    "entry_path_reqwidth": self.entry_path.winfo_reqwidth()
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

    def _get_cookie_display(self):
        p = self.cfg.get("cookies_path")
        if not p: return "当前状态：未加载 Cookie"
        return f"当前路径: ...{p[-40:]}" if len(p) > 40 else f"当前路径: {p}"

    def _import_cookie(self):
        path = filedialog.askopenfilename(title="选择 Cookie 文件", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    head = f.read(100)
                    if "# Netscape HTTP Cookie File" not in head:
                        from tkinter import messagebox
                        messagebox.showerror("格式错误", "该文件似乎不是有效的 Netscape 格式 Cookie 文件")
                        return
                self.cfg.set("cookies_path", path)
                self.lbl_cookie.config(text=self._get_cookie_display())
            except Exception as e:
                print(f"Cookie 导入失败: {e}")

    def _clear_cookie(self):
        self.cfg.set("cookies_path", "")
        self.lbl_cookie.config(text=self._get_cookie_display())

    def _browse(self):
        path = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)

    def _save(self):
        self.cfg.set("download_path", self.entry_path.get())
        self.destroy()


class App(tk.Tk):
    """主应用窗口 (Tkinter 版本)"""

    def __init__(self, yt_dlp_path):
        super().__init__()

        self.title("YT-DLP 下载器")
        self.geometry("900x600")
        self.minsize(600, 400)

        self.yt_dlp_path = yt_dlp_path
        self.task_cards = {}

        self._create_widgets()
        self._init_backend()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        root_frame = tk.Frame(self, padx=12, pady=12, bg="#f7f7f7")
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        top_frame = tk.Frame(root_frame, bg="#f7f7f7")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)

        _lbl_url = tk.Label(top_frame, text="视频链接:", bg="#f7f7f7")
        _lbl_url.grid(row=0, column=0, padx=(0, 8), pady=4)
        # Make entry visually obvious on macOS Tk (high contrast)
        _url_wrap = tk.Frame(top_frame, bg="#ff3b30")  # red border
        _url_wrap.grid(row=0, column=1, sticky="ew", pady=4)
        _url_wrap.columnconfigure(0, weight=1)
        self.entry_url = tk.Entry(
            _url_wrap,
            bg="white",
            fg="black",
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground="#ff3b30",
            highlightcolor="#ff3b30",
            font=("Arial", 14),
        )
        self.entry_url.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        self.entry_url.insert(0, "在这里粘贴视频链接…")
        top_frame.columnconfigure(1, weight=1)

        self.btn_add = tk.Button(top_frame, text="添加下载", command=self._add_task)
        self.btn_add.grid(row=0, column=2, padx=(8, 0))

        self.btn_settings = tk.Button(top_frame, text="设置", command=self._open_settings)
        self.btn_settings.grid(row=0, column=3, padx=(8, 0))

        # Scrollable list area
        list_container = tk.Frame(root_frame)
        list_container.grid(row=1, column=0, sticky="nsew")
        list_container.rowconfigure(0, weight=1)
        list_container.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(list_container, highlightthickness=0, bg="#f7f7f7")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#f7f7f7")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.lbl_empty = tk.Label(self.scrollable_frame, text="队列为空，请添加下载链接", bg="#f7f7f7")
        self.lbl_empty.pack(pady=40)

        # Ensure progress bars render correctly once layout is ready
        self.after(0, self._refresh_list)

        # #region agent log
        try:
            _data = {
                "sessionId": "debug-session",
                "runId": "pre",
                "hypothesisId": "H2",
                "location": "app_tk.py:App._create_widgets",
                "message": "entry_widget_created",
                "data": {
                    "entry_width_opt": 60,
                    "entry_winfo_width": self.entry_url.winfo_width(),
                    "entry_mapped": bool(self.entry_url.winfo_ismapped()),
                    "top_frame_bg": str(top_frame.cget("bg")),
                    "root_bg": str(root_frame.cget("bg"))
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after_idle(self._debug_log_top_layout)
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after_idle(lambda: _agent_log(
                "H2",
                "app_tk.py:App._create_widgets.after_idle",
                "top_frame_bbox",
                {
                    "top_w": self.entry_url.master.master.winfo_width(),
                    "top_h": self.entry_url.master.master.winfo_height(),
                    "bbox_c0": list(self.entry_url.master.master.grid_bbox(0, 0)),
                    "bbox_c1": list(self.entry_url.master.master.grid_bbox(1, 0)),
                    "lbl_mapped": bool(_lbl_url.winfo_ismapped()),
                    "lbl_x": _lbl_url.winfo_x(),
                    "lbl_y": _lbl_url.winfo_y(),
                    "lbl_w": _lbl_url.winfo_width(),
                    "wrap_mapped": bool(_url_wrap.winfo_ismapped()),
                    "wrap_x": _url_wrap.winfo_x(),
                    "wrap_y": _url_wrap.winfo_y(),
                    "wrap_w": _url_wrap.winfo_width(),
                },
                run_id="pre4"
            ))
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.bind("<Map>", lambda e: _agent_log(
                "H2",
                "app_tk.py:App.<Map>",
                "root_mapped",
                {"root_mapped": bool(self.winfo_ismapped()), "w": self.winfo_width(), "h": self.winfo_height()},
                run_id="pre3"
            ))
            self.entry_url.bind("<Map>", lambda e: _agent_log(
                "H2",
                "app_tk.py:App.entry_url.<Map>",
                "entry_mapped",
                {"mapped": bool(self.entry_url.winfo_ismapped()), "w": self.entry_url.winfo_width(), "h": self.entry_url.winfo_height(), "x": self.entry_url.winfo_x(), "y": self.entry_url.winfo_y(), "manager": self.entry_url.winfo_manager(), "bg": str(self.entry_url.cget("bg")), "bd": int(self.entry_url.cget("bd")), "relief": str(self.entry_url.cget("relief")), "hlt": int(self.entry_url.cget("highlightthickness"))},
                run_id="pre3"
            ))
        except Exception:
            pass
        # #endregion agent log

    def _debug_log_top_layout(self):
        # #region agent log
        try:
            self.update_idletasks()
            _top = self.entry_url.master
            _data = {
                "sessionId": "debug-session",
                "runId": "pre2",
                "hypothesisId": "H2",
                "location": "app_tk.py:App._debug_log_top_layout",
                "message": "top_layout_state",
                "data": {
                    "root_mapped": bool(self.winfo_ismapped()),
                    "root_w": self.winfo_width(),
                    "root_h": self.winfo_height(),
                    "top_frame_manager": str(_top.winfo_manager()),
                    "top_frame_mapped": bool(_top.winfo_ismapped()),
                    "top_frame_w": _top.winfo_width(),
                    "top_frame_reqw": _top.winfo_reqwidth(),
                    "entry_manager": str(self.entry_url.winfo_manager()),
                    "entry_mapped": bool(self.entry_url.winfo_ismapped()),
                    "entry_w": self.entry_url.winfo_width(),
                    "entry_reqw": self.entry_url.winfo_reqwidth(),
                    "label0_manager": str(_top.grid_slaves(row=0, column=0)[0].winfo_manager()) if _top.grid_slaves(row=0, column=0) else "none",
                    "grid_slaves_count": len(_top.grid_slaves()),
                    "grid_info_entry": dict(self.entry_url.grid_info()) if self.entry_url.winfo_manager() == "grid" else {}
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

        # #region agent log
        try:
            self.after(0, self._debug_log_entry_post_layout)
        except Exception:
            pass
        # #endregion agent log

    def _debug_log_entry_post_layout(self):
        # #region agent log
        try:
            _data = {
                "sessionId": "debug-session",
                "runId": "pre",
                "hypothesisId": "H2",
                "location": "app_tk.py:App._debug_log_entry_post_layout",
                "message": "entry_post_layout",
                "data": {
                    "entry_winfo_width": self.entry_url.winfo_width(),
                    "entry_winfo_height": self.entry_url.winfo_height(),
                    "entry_mapped": bool(self.entry_url.winfo_ismapped()),
                    "entry_x": self.entry_url.winfo_x(),
                    "entry_y": self.entry_url.winfo_y(),
                    "entry_reqwidth": self.entry_url.winfo_reqwidth()
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/yelin/Desktop/codebase/yt-dlp/.cursor/debug.log", "a", encoding="utf-8") as _f:
                import json as _json
                _f.write(_json.dumps(_data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion agent log

    def _init_backend(self):
        config_path = os.path.join(_parent_dir, "config.json")
        self.config = Config(config_path)

        self.queue_manager = QueueManager(
            max_concurrent=5,
            config=self.config,
            yt_dlp_path=self.yt_dlp_path
        )
        self.queue_manager.on_update = self._on_task_update

    def _add_task(self):
        url = self.entry_url.get().strip()
        if not url:
            return

        self.lbl_empty.pack_forget()
        self.queue_manager.add_task(url)
        self.entry_url.delete(0, "end")
        self._refresh_list()

    def _refresh_list(self):
        current_ids = {t.id for t in self.queue_manager.get_all_tasks()}
        existing_ids = set(self.task_cards.keys())

        for tid in existing_ids - current_ids:
            self.task_cards[tid].destroy()
            del self.task_cards[tid]

        for task in self.queue_manager.get_all_tasks():
            if task.id not in self.task_cards:
                card = TaskCard(
                    self.scrollable_frame, task,
                    on_pause=lambda t=task: self._pause(t.id),
                    on_resume=lambda t=task: self._resume(t.id),
                    on_cancel=lambda t=task: self._cancel(t.id),
                    on_retry=lambda t=task: self._retry(t.id)
                )
                self.task_cards[task.id] = card
                card.pack(fill="x", pady=6)
            else:
                self.task_cards[task.id].task = task
                self.task_cards[task.id].update_display()

        if not self.task_cards:
            self.lbl_empty.pack(pady=40)

    def _on_task_update(self, task_id):
        self.after(0, self._safe_update, task_id)

    def _safe_update(self, task_id):
        if task_id in self.task_cards:
            task = self.queue_manager.get_task(task_id)
            if task:
                self.task_cards[task_id].task = task
                self.task_cards[task_id].update_display()
        else:
            self._refresh_list()

    def _pause(self, task_id):
        self.queue_manager.pause_task(task_id)

    def _resume(self, task_id):
        self.queue_manager.resume_task(task_id)

    def _cancel(self, task_id):
        self.queue_manager.cancel_task(task_id)
        self._refresh_list()

    def _retry(self, task_id):
        self.queue_manager.retry_task(task_id)

    def _open_settings(self):
        SettingsDialog(self, self.config)

    def _on_close(self):
        self.destroy()
