# 🚀 YT-DLP 下载器启动指南 (小白专用)

如果你是第一次使用或者换了新电脑，请按照以下步骤启动程序。

## 1. 快速启动 (推荐)

如果你已经按照 AI 的提示安装好了环境，直接在终端执行这一行命令即可：

```bash
.venv/bin/python yt-dlp-gui/main.py
```

> **注意 (macOS)**：程序现在默认使用 **PySide6 (Qt)** 界面，解决了之前 Tkinter 界面渲染问题。

---

## 2. Cookie 使用 (绕过机器人检测)

如果你在下载时遇到 "Sign in to confirm you’re not a bot" 错误：

1.  **准备 Cookie**：在浏览器中安装插件（如 "Get cookies.txt LOCALLY"），导出 YouTube 的 cookie 为 `.txt` 文件。
2.  **导入程序**：点击下载器右上角的 **“设置”** 按钮。
3.  **加载文件**：点击 **“导入 Cookie (.txt)”**，选择你导出的文件。
4.  **安全下载**：程序已默认开启 **“安全模式”**（限速 5M/s 且增加随机请求间隔），极大降低被封 IP 的风险。
5.  **清理**：如果想移除 Cookie，在设置中点击 **“清理 Cookie”** 即可。

---

## 3. 详细启动步骤 (如果上面失败了)

### 第一步：打开终端
在 Cursor 编辑器下方找到 **终端 (Terminal)** 窗口。如果没有看到，可以按快捷键 ``Ctrl + ` `` (数字 1 左边的键)。

### 第二步：确保你在正确的文件夹
在终端输入 `ls`，如果你能看到 `yt-dlp-gui` 这个文件夹，说明位置是对的。

### 第三步：安装环境 (仅第一次需要)
如果你还没安装过环境，请依次运行以下两条命令：
1. **创建虚拟环境**：
   ```bash
   python3 -m venv .venv
   ```
2. **安装必要的工具**：
   ```bash
   .venv/bin/pip install -r yt-dlp-gui/requirements.txt
   ```

### 第四步：启动程序
输入以下命令并回车：
```bash
.venv/bin/python yt-dlp-gui/main.py
```

---

## 4. 常见问题排查

*   **看到 "DEPRECATION WARNING" 怎么办？**
    *   **忽略它**。那是 Mac 系统的友情提示，不影响你下载视频。
*   **窗口没弹出来？**
    *   检查电脑底部的程序栏（Dock），看有没有一个 Python 的图标在闪烁。
*   **提示 "command not found: python3"？**
    *   说明你电脑还没装 Python，请前往 [python.org](https://www.python.org/) 下载并安装最新版本。

---
*祝你下载愉快！*
