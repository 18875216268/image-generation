# -*- coding: utf-8 -*-
"""默认值与客户端接口（离线）"""
from _harness import SCRIPTS
import sys
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from base import BaseClient
from gpt_image import GPTImageClient
from nano_banana import NanoBananaClient


def run(check):
    g, n = GPTImageClient(), NanoBananaClient()
    check("默认模型为 gpt-image-2", g.default_model == "gpt-image-2", g.default_model)
    check("nano 默认模型为 nano-banana-2", n.default_model == "nano-banana-2", n.default_model)
    check("默认比例为 1:1", g.default_size == "1:1", g.default_size)
    check("清晰度无默认值", g.default_image_size is None, g.default_image_size)
    check("Gemini 比例无默认值", n.default_aspect_ratio is None, n.default_aspect_ratio)
    check("默认数量为 1", g.default_n == 1 and n.default_n == 1)
    check("无参构造拿不到密钥", g.api_key is None and n.api_key is None,
          "gpt=%r nano=%r" % (g.api_key, n.api_key))
    check("客户端方法齐备",
          hasattr(g, "generate")
          and hasattr(n, "generate")
          and hasattr(n, "generate_gemini")
          and hasattr(BaseClient, "_generate_openai"))
    check("图生图入参存在", "image" in GPTImageClient.generate.__code__.co_varnames)
