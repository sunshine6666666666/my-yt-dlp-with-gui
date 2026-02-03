import base64
import hashlib
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

import requests


APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
REDIRECT_URI = "http://localhost:3456/callback"
SCOPE = "offline_access drive:drive drive:file:upload"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def generate_pkce():
    code_verifier = _b64url(os.urandom(64))
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = _b64url(digest)
    return code_verifier, code_challenge


class CallbackHandler(BaseHTTPRequestHandler):
    server_version = "FeishuOAuth/1.0"
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        self.server.auth_code = (params.get("code") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"success, you can close this page now")

    def log_message(self, format, *args):
        return


def get_user_token():
    if not APP_ID or not APP_SECRET:
        raise RuntimeError("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")

    code_verifier, code_challenge = generate_pkce()
    auth_params = {
        "client_id": APP_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": "reauthorize",
        "scope": SCOPE,
    }
    auth_url = "https://open.feishu.cn/open-apis/authen/v1/authorize?" + urlencode(auth_params)

    server = HTTPServer(("localhost", 3456), CallbackHandler)
    server.auth_code = None

    def _serve():
        server.handle_request()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()

    print("请在浏览器打开以下链接完成授权：")
    print(auth_url)
    print("等待回调中...")
    thread.join(timeout=180)

    if not server.auth_code:
        raise RuntimeError("未收到授权码，请确认浏览器已授权并返回到 callback 页面。")

    token_url = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "code": server.auth_code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    resp = requests.post(token_url, json=payload, timeout=30)
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"换取 token 失败: {data}")

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    print("\n✅ 获取成功：")
    print(f"user_access_token: {access_token}")
    if refresh_token:
        print(f"refresh_token: {refresh_token}")


if __name__ == "__main__":
    get_user_token()
