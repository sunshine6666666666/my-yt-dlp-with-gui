# 归档记录 - 全量功能交付与同步 (锁定根目录)

**任务名称**：PySide6 GUI 重构、系统清理、Cursor 自动化指令与 Skill 部署
**归档时间**：2026-02-03 13:02:23
**当前分支**：main

## 📝 变更摘要
1. **PySide6 GUI 重构**：完成了从 Tkinter 到 PySide6 的架构迁移，实现了任务选中状态持久化、自定义 Delegate 渲染及多线程下载保护。
2. **选中逻辑修复**：修复了刷新导致选中丢失的 bug，实现了基于 ID 的选中状态回填及兼容 PySide6 的枚举值。
3. **系统清理**：删除了 `yt-dlp-gui/gui/` 旧版代码及临时文件，精简了入口逻辑。
4. **路径规约锁定**：强制所有 `.claude/` 归档与计划文件必须存储在项目根目录下，不再允许在子目录存储。
5. **Cursor 自动化增强**：
   - 指令集：`/sync-upstream`, `/fetch-docs`, `/log-cleanup`, `/hello`。
   - 规约：`debug-joint-analysis.mdc`。
   - 技能：`hello-world`。

## 📁 关键文件
- `yt-dlp-gui/gui_qt/app_qt.py`
- `yt-dlp-gui/main.py`
- `.cursor/commands/*`
- `.cursor/skills/*`
- `.claude/archive/*` (位于项目根目录)

## ✅ 验证结果
- [x] PySide6 界面稳定，选中状态在下载刷新时不会丢失。
- [x] “重试”按钮功能正常。
- [x] 所有自动化指令路径均已对齐项目根目录。

---
*此归档记录由 Version Auditor 自动生成并锁定根目录路径。*
