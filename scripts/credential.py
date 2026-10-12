# -*- coding: utf-8 -*-
"""凭证层：检测凭证有效性，无效时调起本地前端采集并持久化。

设计：
- validate_key：纯网络鉴权探测（复用 base 的 /v1/tasks 探测），不触发真实生图。
- ensure_valid_key(client)：有效直接返回；无效启动本地 HTTPServer（127.0.0.1）
  托管 auth.html，用户在页面输入密钥，本地服务校验通过后写入 config.ini 并关闭。
- 密钥仅在本地服务与生图服务端之间流动，不经过任何第三方，规避 CORS。
"""
import os
import json
import socket
import time
import threading
import urllib.request
import webbrowser
import configparser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from .base import BaseClient
except ImportError:
    from base import BaseClient


def _bing_bg():
    """返回 Bing 每日壁纸地址（服务端代理，规避 CORS，国内可直连 bing.com）。"""
    try:
        api = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN"
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
        urlbase = data["images"][0]["url"]
        full = urlbase if urlbase.startswith("http") else "https://www.bing.com" + urlbase
        return {"ok": True, "url": full}
    except Exception:
        return {"ok": False, "url": ""}


def _ctype(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".svg": "image/svg+xml", ".ico": "image/x-icon",
        ".css": "text/css", ".js": "application/javascript", ".json": "application/json",
        ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
    }.get(ext, "application/octet-stream")


# 同一进程内已验证通过的 Key，避免重复网络探测
_VERIFIED_KEYS = set()


def ensure_valid_key(client):
    """确保 client.api_key 为有效凭证，返回有效 Key；无凭证或无效则调起前端采集。

    每个 Key 在一个进程内只做一次鉴权探测，不会反复校验。
    """
    key = client.api_key
    if key and key in _VERIFIED_KEYS:
        client._key_verified = True
        return key
    if key and client.validate_key(key):
        _VERIFIED_KEYS.add(key)
        client._key_verified = True
        return key
    new_key = _collect_via_html(client)
    _VERIFIED_KEYS.add(new_key)
    client.api_key = new_key
    client._key_verified = True
    return new_key


def _collect_via_html(client):
    port = _free_port()
    skill_root = BaseClient._skill_root()
    html_path = os.path.join(skill_root, "assets", "auth.html")
    assets_dir = os.path.join(skill_root, "assets")
    state = {"key": None}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.startswith("/api/bg"):
                self._send(200, _bing_bg())
                return
            if self.path.startswith("/api/"):
                self._send(405, {"ok": False, "msg": "method not allowed"})
                return
            name = self.path.split("?", 1)[0].lstrip("/")
            if name and name != "index.html":
                cand = os.path.normpath(os.path.join(assets_dir, name))
                if os.path.isfile(cand) and os.path.commonpath([cand, assets_dir]) == assets_dir:
                    self._send_file(cand)
                    return
            self._send_file(html_path)

        def _send_file(self, path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
            except Exception:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", _ctype(path))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != "/api/key":
                self._send(404, {"ok": False, "msg": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                data = {}
            key = (data.get("key") or "").strip()
            if not key:
                self._send(200, {"ok": False, "msg": "请输入密钥"})
                return
            if client.validate_key(key):
                _save_key(key)
                self._send(200, {"ok": True})
                state["key"] = key
            else:
                self._send(200, {"ok": False, "msg": "密钥无效，请重试"})

        def log_message(self, *args):
            pass

    try:
        timeout = int((client.config or {}).get("credential_timeout", "") or 900)
    except ValueError:
        timeout = 900
    url = "http://127.0.0.1:%d/" % port
    print("[图片生成] 凭证无效，已打开密钥录入页：%s" % url)
    try:
        webbrowser.open(url)
    except Exception:
        print("[图片生成] 无法自动打开浏览器，请手动访问：%s" % url)

    # 服务在后台线程常驻，主线程等待；避免 agent 在用户未录入时无限阻塞
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    deadline = time.time() + timeout
    while time.time() < deadline and not state["key"]:
        time.sleep(0.2)
    server.shutdown()
    server.server_close()
    if not state["key"]:
        raise RuntimeError("[图片生成] %d 秒内未获取到有效密钥，已放弃。" % timeout)
    return state["key"]


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _save_key(key):
    """将用户密钥持久化到 config.ini [common] api_key。"""
    path = BaseClient._find_config()
    if not path:
        return
    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(path, encoding="utf-8")
        if not cp.has_section("common"):
            cp.add_section("common")
        cp.set("common", "api_key", key)
        with open(path, "w", encoding="utf-8") as f:
            cp.write(f)
    except Exception:
        pass
