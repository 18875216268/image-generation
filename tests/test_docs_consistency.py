# -*- coding: utf-8 -*-
"""文档与结构一致性（离线）"""
import os, re, json
from _harness import SKILL_ROOT, read, load_json

SKILL = os.path.join(SKILL_ROOT, "SKILL.md")
README = os.path.join(SKILL_ROOT, "README.md")
MANIFEST = os.path.join(SKILL_ROOT, "manifest.json")

SECTIONS = ["## 1. 作用", "## 2. 最高原则", "## 3. 架构", "## 9. 已知边界", "## 10. 许可"]


def run(check):
    sk, rd = read(SKILL), read(README)

    for sec in SECTIONS:
        check("SKILL.md 含章节 %s" % sec, sec in sk)
        check("README.md 含章节 %s" % sec, sec in rd)

    check("SKILL.md frontmatter name 为 image-generation",
          re.search(r"^name:\s*image-generation\s*$", sk, re.M) is not None)
    check("SKILL.md 标识名符合 kebab-case",
          re.search(r"^name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", sk, re.M) is not None)
    check("SKILL.md display_name 保留中文",
          re.search(r"^display_name:\s*\"?图片生成\"?", sk, re.M) is not None)
    check("README.md 指向 SKILL.md", "SKILL.md" in rd)
    check("SKILL.md 无平台字眼", not re.search(r"Right\s*Code|rightapi\.ai", sk))
    check("README.md 无平台字眼", not re.search(r"Right\s*Code|rightapi\.ai", rd))

    for p in ("models/gpt-image.md", "models/nano-banana.md"):
        check("模型文档存在：%s" % p, os.path.isfile(os.path.join(SKILL_ROOT, p)))

    mf = load_json(MANIFEST)
    check("manifest 标识名为 image-generation", mf.get("name") == "image-generation", mf.get("name"))
    check("manifest 标识名符合 kebab-case",
          re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", str(mf.get("name") or "")) is not None)
    check("manifest 展示名保留中文", mf.get("display_name") == "图片生成", mf.get("display_name"))
    for layer in mf.get("layers", []):
        check("manifest 层路径存在：%s" % layer["path"],
              os.path.exists(os.path.join(SKILL_ROOT, layer["path"])))
    check("manifest 声明无 shell 命令", mf.get("shell", {}).get("used") is False)
    check("manifest 声明包内仅写 api_key",
          "api_key" in json.dumps(mf.get("writes", {}), ensure_ascii=False))

    for p in ("scripts/base.py", "scripts/gpt_image.py", "scripts/nano_banana.py",
              "scripts/credential.py", "scripts/__init__.py", "config.ini",
              "assets/auth.html", "assets/qrcode.png", "assets/favicon.png"):
        check("功能文件在位：%s" % p, os.path.isfile(os.path.join(SKILL_ROOT, p)))
