# 归档记录 - 浏览器 Cookie 集成与 UI 稳定性修复

**任务名称**：集成浏览器动态 Cookie 读取功能并修复 Qt 跨线程刷新崩溃
**归档时间**：2026-02-03 16:25:00
**当前分支**：main

## 📝 变更摘要
1. **浏览器 Cookie 动态集成**：
   - 在 `Downloader` 中实现了优先尝试 `--cookies-from-browser chrome` 的逻辑。
   - **自动回退机制**：当检测到浏览器 Cookie 读取失败（解密失败、数据库锁等）时，自动切换到传统的静态 Cookie 文件并继续下载。
2. **UI 逻辑增强**：
   - **设置页优化**：新增“优先使用浏览器 Cookie (Chrome)”勾选项，并实现配置持久化。
   - **状态反馈**：在任务卡片中新增 `notice` 提示条，当触发 Cookie 回退时，用户能实时看到“⚠️ 浏览器 Cookie 读取失败，已回退静态 Cookie”的提示。
3. **架构稳定性修复**：
   - **跨线程安全**：修复了因下载线程直接操作 UI 导致项目崩溃（segfault）的严重缺陷。引入了 `UiBridge` 信号量机制，确保所有 UI 刷新均在主线程执行。
4. **环境清理与规约**：
   - 将 `yt-dlp-gui/logs/` 目录正式加入 `.gitignore`，确保本地业务日志不会污染云端。
   - 清理了 `downloader.py` 中遗留的调试插桩逻辑。

## 📁 关键文件
- `yt-dlp-gui/core/downloader.py` (核心回退逻辑)
- `yt-dlp-gui/gui_qt/app_qt.py` (主窗口逻辑与跨线程修复)
- `yt-dlp-gui/gui_qt/settings_qt.py` (设置界面)
- `yt-dlp-gui/core/config.py` (配置定义)
- `yt-dlp-gui/core/task.py` (任务模型扩展)
- `.gitignore` (忽略规则)

## ✅ 验证结果
- [x] **功能验证**：成功通过 Chrome 动态 Cookie 下载视频，无报错。
- [x] **稳定性验证**：连续添加多任务，不再触发 `QBasicTimer` 警告及 Segfault。
- [x] **回退验证**：模拟浏览器 Cookie 失效后，程序能自动拉起静态 Cookie 进程并完成任务。

---
*此归档记录标志着 PySide6 GUI 版本在 Cookie 处理和并发稳定性上达到了生产级可用状态。*
