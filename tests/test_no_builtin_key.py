# -*- coding: utf-8 -*-
"""零内置密钥（离线）"""
import os, re
from _harness import SKILL_ROOT, SCRIPTS, KEY_RE, read, walk_files
import sys
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from base import BaseClient


def run(check):
    check("代码中无 DEFAULT_KEY 常量", not hasattr(BaseClient, "DEFAULT_KEY"))

    hits = []
    for p in walk_files(SKILL_ROOT):
        if os.path.splitext(p)[1].lower() not in (".md", ".py", ".html", ".ini", ".json", ".txt"):
            continue
        s = read(p)
        for m in KEY_RE.finditer(s):
            hits.append(os.path.relpath(p, SKILL_ROOT))
    check("技能内零密钥素材", not hits, set(hits))

    cfg = read(os.path.join(SKILL_ROOT, "config.ini"))
    check("config.ini 无 api_key 项", not re.search(r"^api_key\s*=", cfg, re.M))
    check("config.ini 无环境变量侧信道",
          "RIGHTAPI_KEY" not in cfg and "api_key_env" not in cfg)
