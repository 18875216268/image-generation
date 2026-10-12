# -*- coding: utf-8 -*-
"""极简离线测试骨架：仅标准库，不联网、不消耗额度。"""
import os, sys, json, re

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

TEXT_EXT = (".py", ".md", ".html", ".ini", ".json", ".txt")
KEY_RE = re.compile(r"sk-[A-Za-z0-9]{8,}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def walk_files(root):
    for dp, dn, fn in os.walk(root):
        if "__pycache__" in dp:
            continue
        for f in sorted(fn):
            yield os.path.join(dp, f)


class Recorder:
    """记录断言结果：check(名称, 条件, 附加信息)"""

    def __init__(self, prefix, failed, verbose=True):
        self.prefix = prefix
        self.failed = failed
        self.verbose = verbose

    def __call__(self, name, cond, extra=""):
        ok = bool(cond)
        if not ok:
            self.failed.append(("%s :: %s" % (self.prefix, name), str(extra)))
        if self.verbose:
            tail = (" :: " + str(extra)) if extra else ""
            print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, tail))
        return ok
