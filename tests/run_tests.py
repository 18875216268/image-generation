# -*- coding: utf-8 -*-
"""离线测试总入口：python tests/run_tests.py（不联网、不消耗额度）"""
import os, sys, importlib, traceback

here = os.path.dirname(os.path.abspath(__file__))
if here not in sys.path:
    sys.path.insert(0, here)

import _harness


def main():
    failed = []
    mods = sorted(f[:-3] for f in os.listdir(here)
                  if f.startswith("test_") and f.endswith(".py"))
    for name in mods:
        print("\n== %s ==" % name)
        rec = _harness.Recorder(name, failed)
        try:
            mod = importlib.import_module(name)
            mod.run(rec)
        except Exception:
            failed.append((name + "（执行异常）", traceback.format_exc(limit=3)))
            print("  [FAIL] 模块执行异常")

    for d, _, _ in os.walk(_harness.SKILL_ROOT):
        if "__pycache__" in d:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    print("\n" + "=" * 46)
    if failed:
        print("未通过 %d 项：" % len(failed))
        for label, extra in failed:
            print("  - %s%s" % (label, (" :: " + extra) if extra else ""))
        return 1
    print("全部通过（%d 个测试模块）" % len(mods))
    return 0


if __name__ == "__main__":
    sys.exit(main())
