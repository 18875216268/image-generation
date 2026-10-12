# -*- coding: utf-8 -*-
"""凭证门禁与"不过多验证"（离线，不联网）"""
from _harness import SCRIPTS
import sys
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from base import BaseClient
import credential as cred


def run(check):
    # 无密钥时必须走凭证页采集，而不是直接放行
    calls = []
    real_collect = cred._collect_via_html
    cred._collect_via_html = lambda client: (calls.append(1), "dummy")[1]
    try:
        cred.ensure_valid_key(BaseClient())
    finally:
        cred._collect_via_html = real_collect
    check("无密钥时调起凭证页", len(calls) == 1, calls)

    # 同一个 Key 在一个进程内只做一次鉴权探测
    hits = [0]
    real_validate = BaseClient.validate_key
    BaseClient.validate_key = lambda self, key=None: (hits.__setitem__(0, hits[0] + 1), True)[1]
    try:
        cred.ensure_valid_key(BaseClient(api_key="dummy-key-A"))
        cred.ensure_valid_key(BaseClient(api_key="dummy-key-A"))
        cred.ensure_valid_key(BaseClient(api_key="dummy-key-A"))
    finally:
        BaseClient.validate_key = real_validate
    check("同一 Key 仅探测一次（不过多验证）", hits[0] == 1, "探测次数=%d" % hits[0])
