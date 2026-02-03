---
name: feishu-upload-clean
description: 上传下载目录的视频到飞书云空间，校验完成后清理本地文件，支持重复文件覆盖确认与慢响应监控。
---

# Feishu Upload & Clean

## 使用场景
- 上传 `gui_qt/downloads` 下的全部视频并在飞书目录可见后清理本地文件。
- 视频体积较大，需要监控上传完成状态。
- 飞书目录已存在同名文件时，先询问是否覆盖。

## 工作流 (Workflow)
1. 读取 `yt-dlp-gui/.env` 里的配置（App ID、Secret、Folder Token、下载目录）。
2. 扫描下载目录中的视频文件。
3. 逐个文件上传：
   - 检查飞书目录是否已有同名文件。
   - 如果存在，询问是否覆盖；若否，跳过该文件。
   - 若允许覆盖，删除远端同名文件后再上传。
4. 上传完成后轮询检查飞书目录是否出现该文件。
5. 文件确认存在后删除本地文件。
6. 输出汇总结果。

## 依赖说明
- Python 3.9+
- `requests`
- `python-dotenv`

## 运行方式
在仓库根目录执行：
```
python3 .cursor/skills/feishu-upload-clean/scripts/upload_and_clean.py
```
