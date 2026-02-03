import os
import sys
import time
import requests
from dotenv import load_dotenv

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".flv", ".mov")

API_BASE = "https://open.feishu.cn/open-apis"
TOKEN_URL = f"{API_BASE}/auth/v3/tenant_access_token/internal"
LIST_URL = f"{API_BASE}/drive/v1/files"
PREPARE_URL = f"{API_BASE}/drive/v1/files/upload_prepare"
UPLOAD_PART_URL = f"{API_BASE}/drive/v1/files/upload_part"
FINISH_URL = f"{API_BASE}/drive/v1/files/upload_finish"

POLL_INTERVAL = 3
MAX_WAIT_SECONDS = 600
DRY_RUN = os.getenv("DRY_RUN", "").lower() in ("1", "true", "yes")


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _default_env_path():
    return os.path.join(_repo_root(), "yt-dlp-gui", ".env")


def load_config():
    env_path = os.getenv("ENV_PATH") or _default_env_path()
    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env not found: {env_path}")

    load_dotenv(env_path)

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    user_access_token = os.getenv("FEISHU_USER_ACCESS_TOKEN")
    folder_token = os.getenv("FEISHU_FOLDER_TOKEN")
    download_path = os.getenv("DOWNLOAD_PATH")

    if not all([folder_token, download_path]):
        raise ValueError(".env 缺少必要字段 (FEISHU_FOLDER_TOKEN/DOWNLOAD_PATH)")

    env_dir = os.path.dirname(env_path)
    if os.path.isabs(download_path):
        download_dir = download_path
    else:
        download_dir = os.path.abspath(os.path.join(env_dir, download_path))

    return app_id, app_secret, user_access_token, folder_token, download_dir


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _parse_json(res, context):
    try:
        return res.json()
    except Exception as e:
        text = res.text or ""
        snippet = text[:300].replace("\n", " ")
        raise RuntimeError(
            f"{context} 返回非 JSON 响应 (status={res.status_code}). 片段: {snippet}"
        ) from e


def get_tenant_access_token(app_id, app_secret):
    res = requests.post(TOKEN_URL, json={"app_id": app_id, "app_secret": app_secret}, timeout=30)
    data = _parse_json(res, "获取 token")
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data.get('msg')}")
    return data["tenant_access_token"]


def list_folder_files(token, folder_token):
    page_token = None
    files = []
    while True:
        params = {"folder_token": folder_token, "page_size": 200}
        if page_token:
            params["page_token"] = page_token
        res = requests.get(LIST_URL, headers=_headers(token), params=params, timeout=30)
        data = _parse_json(res, "列目录")
        if data.get("code") != 0:
            raise RuntimeError(f"列目录失败: {data.get('msg')}")
        files.extend(data.get("data", {}).get("files", []))
        page_token = data.get("data", {}).get("next_page_token")
        if not page_token:
            break
    return files


def build_remote_index(token, folder_token):
    index = {}
    for f in list_folder_files(token, folder_token):
        name = f.get("name")
        if not name:
            continue
        index.setdefault(name, []).append(f)
    return index


def find_remote_file(remote_index, filename):
    matches = remote_index.get(filename) or []
    return matches[0] if matches else None


def delete_remote_file(token, file_token):
    if DRY_RUN:
        print(f"🧪 [DRY_RUN] 将删除远端文件: {file_token}")
        return
    url = f"{API_BASE}/drive/v1/files/{file_token}"
    res = requests.delete(url, headers=_headers(token), timeout=30)
    data = _parse_json(res, "删除远端文件")
    if data.get("code") != 0:
        raise RuntimeError(f"删除远端文件失败: {data.get('msg')}")


def upload_prepare(token, folder_token, file_name, size):
    if DRY_RUN:
        print(f"🧪 [DRY_RUN] 将初始化上传: {file_name} ({size} bytes)")
        return "dry_run_upload_id"
    payload = {
        "file_name": file_name,
        "parent_type": "explorer",
        "parent_node": folder_token,
        "size": size,
    }
    res = requests.post(PREPARE_URL, headers=_headers(token), json=payload, timeout=30)
    data = _parse_json(res, "初始化上传")
    if data.get("code") != 0:
        raise RuntimeError(f"初始化上传失败: {data.get('msg')}")
    return data["data"]["upload_id"]


def upload_parts(token, upload_id, file_path):
    if DRY_RUN:
        print(f"🧪 [DRY_RUN] 将上传分片: {file_path}")
        return 1
    block_size = 4 * 1024 * 1024
    seq = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break
            data = {"upload_id": upload_id, "seq": seq, "size": len(chunk)}
            files = {"file": chunk}
            res = requests.post(UPLOAD_PART_URL, headers=_headers(token), data=data, files=files, timeout=120)
            resp = _parse_json(res, f"分片上传(seq={seq})")
            if resp.get("code") != 0:
                raise RuntimeError(f"分片上传失败(seq={seq}): {resp.get('msg')}")
            seq += 1
    return seq


def upload_finish(token, upload_id, block_num):
    if DRY_RUN:
        print(f"🧪 [DRY_RUN] 将完成上传: {upload_id} (blocks={block_num})")
        return
    res = requests.post(FINISH_URL, headers=_headers(token), json={"upload_id": upload_id, "block_num": block_num}, timeout=30)
    data = _parse_json(res, "完成上传")
    if data.get("code") != 0:
        raise RuntimeError(f"完成上传失败: {data.get('msg')}")


def wait_for_remote_file(token, folder_token, filename):
    if DRY_RUN:
        print(f"🧪 [DRY_RUN] 将等待远端可见: {filename}")
        return True
    start = time.time()
    while True:
        res = find_remote_file(build_remote_index(token, folder_token), filename)
        if res:
            return True
        elapsed = time.time() - start
        if elapsed >= MAX_WAIT_SECONDS:
            return False
        print(f"⏳ 等待远端可见: {filename} ({int(elapsed)}s)")
        time.sleep(POLL_INTERVAL)


def ask_overwrite(filename):
    while True:
        answer = input(f"飞书目录中已存在同名文件：{filename}。是否覆盖？(yes/no) ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("请输入 yes 或 no。")


def main():
    try:
        app_id, app_secret, user_access_token, folder_token, download_dir = load_config()
    except Exception as e:
        print(f"配置错误: {e}")
        sys.exit(1)

    if not os.path.isdir(download_dir):
        print(f"目录不存在: {download_dir}")
        sys.exit(1)

    if user_access_token:
        token = user_access_token
        print("🔐 使用 FEISHU_USER_ACCESS_TOKEN 访问个人空间")
    else:
        print("未检测到 FEISHU_USER_ACCESS_TOKEN。请先在 .env 填写该值并保存。")
        sys.exit(1)

    files = [f for f in os.listdir(download_dir) if f.lower().endswith(VIDEO_EXTS)]
    if not files:
        print("📭 没有发现待上传的视频文件。")
        return

    print(f"📂 发现 {len(files)} 个待上传文件。")
    if DRY_RUN:
        print("🧪 已启用 DRY_RUN，不会真正上传或删除文件。")
    remote_index = build_remote_index(token, folder_token)
    for name in files:
        file_path = os.path.join(download_dir, name)
        print(f"\n🚀 开始处理: {name}")
        try:
            existing = find_remote_file(remote_index, name)
            if existing:
                if not ask_overwrite(name):
                    print("⏭️ 已跳过")
                    continue

            size = os.path.getsize(file_path)
            upload_id = upload_prepare(token, folder_token, name, size)
            block_num = upload_parts(token, upload_id, file_path)
            upload_finish(token, upload_id, block_num)

            if not wait_for_remote_file(token, folder_token, name):
                print("⚠️ 上传完成但未在目录中检测到该文件，请稍后手动确认。")
                continue

            if existing:
                delete_remote_file(token, existing["token"])
                print("🧹 已删除远端同名文件")

            if DRY_RUN:
                print(f"🧪 [DRY_RUN] 将删除本地文件: {file_path}")
            else:
                os.remove(file_path)
                print("✅ 上传成功并已清理本地文件")
            remote_index = build_remote_index(token, folder_token)
        except Exception as e:
            print(f"❌ 处理失败: {e}")

    print("\n✨ 全部任务处理完成")


if __name__ == "__main__":
    main()
