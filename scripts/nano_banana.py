# -*- coding: utf-8 -*-
"""nano-banana 系列客户端（OpenAI 兼容 + Gemini 兼容双接口）。"""
import json
try:
    from .base import BaseClient
except ImportError:
    from base import BaseClient
try:
    from .credential import ensure_valid_key
except ImportError:
    from credential import ensure_valid_key


class NanoBananaClient(BaseClient):
    _CONFIG_SECTION = "nano_banana"
    DEFAULT_MODEL = "nano-banana-2"
    DEFAULT_SIZE = "1:1"
    DEFAULT_ASPECT_RATIO = None
    DEFAULT_N = 1

    def __init__(self, api_key=None, user_agent=None, poll_interval=None, timeout=None):
        super().__init__(api_key=api_key, user_agent=user_agent,
                         poll_interval=poll_interval, timeout=timeout)
        self.default_model = self.config.get("default_model") or self.DEFAULT_MODEL
        self.default_size = self.config.get("default_size") or self.DEFAULT_SIZE
        vis = (self.config.get("default_image_size") or "").strip()
        self.default_image_size = vis or None
        ar = (self.config.get("default_aspect_ratio") or "").strip()
        self.default_aspect_ratio = ar or None
        try:
            raw = (self.config.get("n") or "").strip()
            self.default_n = int(raw) if raw else self.DEFAULT_N
        except ValueError:
            self.default_n = self.DEFAULT_N

    def generate(self, prompt, model=None, size=None, image_size=None, n=None,
                 image=None, return_urls=True):
        """OpenAI 兼容文生图 / 图生图（编辑）。返回图片 URL 列表或完整响应 dict。"""
        if not getattr(self, "_key_verified", False):
            ensure_valid_key(self)
        return self._generate_openai(
            prompt,
            model or self.default_model,
            size or self.default_size,
            image_size if image_size is not None else self.default_image_size,
            n if n is not None else self.default_n,
            image, return_urls)

    def generate_gemini(self, prompt, model=None, aspect_ratio=None,
                        image_size=None, reference_image=None, return_urls=True):
        """Gemini 兼容文生图 / 图生图（编辑），使用 aspectRatio 控制比例。返回图片 URL 列表或完整响应 dict。"""
        if not getattr(self, "_key_verified", False):
            ensure_valid_key(self)
        model = model or self.default_model
        aspect_ratio = aspect_ratio or self.default_aspect_ratio
        image_size = image_size if image_size is not None else self.default_image_size
        parts = [{"text": prompt}]
        if reference_image is not None:
            b64 = self._read_image(reference_image)
            parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
        contents = {"parts": parts}
        gencfg = {}
        if aspect_ratio:
            gencfg.setdefault("imageConfig", {})["aspectRatio"] = aspect_ratio
        if image_size:
            gencfg.setdefault("imageConfig", {})["imageSize"] = image_size
        payload = {"contents": [contents], "async": True}
        if gencfg:
            payload["generationConfig"] = gencfg
        path = "/draw/v1beta/models/%s:generateContent" % model
        st, resp = self._post(path, payload)
        if st != 200 or not resp.get("task_id"):
            raise RuntimeError("提交失败 HTTP %s: %s" % (st, resp))
        final = self._wait(resp["task_id"])
        urls = self._extract(final)
        if not urls:
            raise RuntimeError("未拿到图片，最终响应: %s" % json.dumps(final, ensure_ascii=False)[:300])
        return urls if return_urls else final
