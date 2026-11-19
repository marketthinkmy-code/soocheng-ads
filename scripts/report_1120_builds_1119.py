# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「我们刚刚建了什么啊？cbo & 1-1-3 而已，对吗」): every «| 1120» campaign built today, MY 5.0 + SG, live status,
budget, ad sets and ad counts."""
from collections import Counter

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for c in g._get_all(s.meta.account_path + "/campaigns", {"fields": "name,status,effective_status,daily_budget,created_time", "limit": "500"}):
        if "| 1120" not in c["name"]:
            continue
        ads = g._get_all(c["id"] + "/ads", {"fields": "effective_status,adset{name}", "limit": "50"})
        sets = Counter(a["adset"]["name"] for a in ads)
        st = Counter(a["effective_status"] for a in ads)
        print(f"{label} «{c['name']}» · campaign {c['id']} · {c['status']} · RM{int(c.get('daily_budget') or 0) // 100}/天 · 建于 {c['created_time'][11:16]} UTC")
        print(f"     ad sets: " + " · ".join(f"{k}（{v} 支）" for k, v in sets.items()) + f" · ad 状态 {dict(st)}")
print("1120 BUILDS DONE (read-only)")
