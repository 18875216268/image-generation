# -*- coding: utf-8 -*-
"""ROUTES.md 与 routes.json 同源性（离线）"""
import os
from _harness import SKILL_ROOT, load_json, read

ROUTES_JSON = os.path.join(SKILL_ROOT, "routes", "routes.json")
ROUTES_MD = os.path.join(SKILL_ROOT, "routes", "ROUTES.md")


def run(check):
    check("routes.json 存在", os.path.isfile(ROUTES_JSON))
    check("ROUTES.md 存在", os.path.isfile(ROUTES_MD))
    data = load_json(ROUTES_JSON)
    md = read(ROUTES_MD)

    d = data.get("defaults", {})
    check("默认模型已渲染", d.get("model") in md, d.get("model"))
    check("默认方法已渲染", d.get("method") in md, d.get("method"))

    for r in data.get("routes", []):
        check("路由 %s 已渲染" % r["id"], r["id"] in md)
        check("路由 %s 的调用目标已渲染" % r["id"], r["client"] in md, r["client"])
        check("路由 %s 的方法已渲染" % r["id"], r["method"] in md, r["method"])

    for line in data.get("redlines", []):
        check("红线已渲染：%s…" % line[:14], line in md)
