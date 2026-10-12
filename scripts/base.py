# -*- coding: utf-8 -*-
"""生图公共客户端底座。"""
import urllib.request
import urllib.error
import json
import time
import base64
import os
import configparser


class BaseClient:
    BASE = "https://www.rightapi.ai"
    # 技能不内置任何密钥：无可用凭证时必须由用户在凭证页录入
    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    _CONFIG_SECTION = None

    def __init__(self, api_key=None, user_agent=None, poll_interval=None,
                 timeout=None):
        # 加载 config.ini（技能根目录），缺失则回退内置默认值
        cfg = self._load_config(getattr(self, "_CONFIG_SECTION", None))
        self.config = cfg

        self.api_key = api_key or cfg.get("api_key") or None
        self.ua = user_agent or cfg.get("user_agent") or self.DEFAULT_UA
        self.base_url = cfg.get("base_url") or self.BASE

        try:
            pi = int(cfg.get("poll_interval", ""))
        except (ValueError, TypeError):
            pi = None
        self.poll_interval = poll_interval or pi or 5

        try:
            to = int(cfg.get("timeout", ""))
        except (ValueError, TypeError):
            to = None
        self.timeout = timeout or to or 360

    @staticmethod
    def _find_config():
        p = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "config.ini")
        return p if os.path.isfile(p) else None

    def _load_config(self, section):
        path = self._find_config()
        if not path:
            return {}
        try:
            cp = configparser.ConfigParser(interpolation=None)
            cp.read(path, encoding="utf-8")
            cfg = {}
            if cp.has_section("common"):
                cfg.update(dict(cp.items("common")))
            if section and cp.has_section(section):
                cfg.update(dict(cp.items(section)))
            return cfg
        except Exception:
            return {}

    def _post(self, path, payload, retries=3):
        url = self.base_url + path
        data = json.dumps(payload).encode("utf-8")
        last = None
        for _ in range(retries):
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", "Bearer " + self.api_key)
            req.add_header("User-Agent", self.ua)
            req.add_header("Connection", "close")
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    return r.status, json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8", "replace")
            except Exception as e:
                last = str(e)
                time.sleep(2)
        return None, last

    def _get_task(self, task_id, retries=4):
        url = self.base_url + "/v1/tasks/" + task_id
        last = None
        for _ in range(retries):
            req = urllib.request.Request(url, method="GET")
            req.add_header("Authorization", "Bearer " + self.api_key)
            req.add_header("User-Agent", self.ua)
            req.add_header("Connection", "close")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return r.status, json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8", "replace")
            except Exception as e:
                last = str(e)
                time.sleep(2 + _ * 2)
        return None, last

    def _wait(self, task_id):
        """轮询任务直至完成（响应出现 data/candidates）或失败/超时。返回最终响应 dict。"""
        start = time.time()
        last = None
        while time.time() - start < self.timeout:
            st, resp = self._get_task(task_id)
            if st is None:
                time.sleep(self.poll_interval)
                continue
            if st != 200:
                raise RuntimeError("任务查询失败 HTTP %s: %s" % (st, resp))
            last = resp
            if not isinstance(resp, dict):
                time.sleep(self.poll_interval)
                continue
            if resp.get("status") == "failed":
                err = resp.get("error", {})
                raise RuntimeError("生图失败: %s" % err.get("message", resp))
            if resp.get("data") or resp.get("candidates"):
                return resp
            time.sleep(self.poll_interval)
        return last or {"status": "timeout"}

    def _generate_openai(self, prompt, model, size, image_size, n, image, return_urls):
        """OpenAI 兼容流程（gpt-image 与 nano-banana 共用）：提交 → 轮询 → 提取 URL。"""
        payload = {
            "model": model,
            "prompt": prompt,
            "async": True,
            "n": n,
            "size": size,
        }
        if image_size:
            payload["imageSize"] = image_size
        if image is not None:
            payload["image"] = ["data:image/png;base64," + self._read_image(image)]
        st, resp = self._post("/draw/v1/images/generations", payload)
        if st != 200 or not resp.get("task_id"):
            raise RuntimeError("提交失败 HTTP %s: %s" % (st, resp))
        final = self._wait(resp["task_id"])
        urls = self._extract(final)
        if not urls:
            raise RuntimeError("未拿到图片，最终响应: %s" % json.dumps(final, ensure_ascii=False)[:300])
        return urls if return_urls else final

    @staticmethod
    def _extract(resp):
        urls = []
        if isinstance(resp, dict):
            for it in resp.get("data", []) or []:
                if isinstance(it, dict) and it.get("url"):
                    urls.append(it["url"])
            for c in resp.get("candidates", []) or []:
                content = c.get("content", {}) if isinstance(c, dict) else {}
                for p in content.get("parts", []) or []:
                    if isinstance(p, dict) and p.get("text"):
                        urls.append(p["text"])
        return urls

    @staticmethod
    def _read_image(value):
        """接受路径 / bytes / 纯 base64 字符串，返回 base64 字符串。"""
        if value is None:
            return None
        if isinstance(value, bytes):
            return base64.b64encode(value).decode("ascii")
        if isinstance(value, str):
            if os.path.isfile(value):
                with open(value, "rb") as f:
                    return base64.b64encode(f.read()).decode("ascii")
            if value.startswith("data:"):
                return value.split(",", 1)[1]
            return value
        raise ValueError("不支持的参考图类型: %r" % type(value))

    @staticmethod
    def _skill_root():
        p = BaseClient._find_config()
        return os.path.dirname(p) if p else os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

    def _get_tasks(self, retries=2):
        """GET /v1/tasks：用于凭证鉴权探测，零成本。返回 (status, resp)。"""
        url = self.base_url + "/v1/tasks"
        for _ in range(retries):
            req = urllib.request.Request(url, method="GET")
            req.add_header("Authorization", "Bearer " + self.api_key)
            req.add_header("User-Agent", self.ua)
            req.add_header("Connection", "close")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status, json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8", "replace")
            except Exception:
                time.sleep(1)
        return None, None

    def validate_key(self, api_key=None):
        """探测 Key 是否被服务端接受（零成本：仅一次 GET，不触发真实生图）。返回 bool。

        服务端先鉴权后路由：Key 被接受时对不存在的路由返回 404，Key 无效时返回 401/403。
        故仅 401/403 判定无效；网络不可达返回 True，交由实际生成暴露错误，避免误拦截。
        """
        probe = self if api_key is None else BaseClient(api_key=api_key)
        st, _ = probe._get_tasks()
        if st is None:
            return True
        return st not in (401, 403)
