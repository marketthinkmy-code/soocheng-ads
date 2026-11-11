# -*- coding: utf-8 -*-
"""owner 2026-11-11「新的视频，我觉得星期四可以全部开回去，再测试看看」— on Thursday 11/12 (new Thu-week window, NEW VIDEO now
judged at RM80, PR #89) switch every PAUSED ad in the 6 NEW VIDEO campaigns back to ACTIVE. Only these 6 campaign ids; refuses
to write before 2026-11-12 00:00 MYT; ban gate (🚫 / banned_creatives) and DISAPPROVED ads are skipped. Ad sets / campaigns
are not touched except an ad set found PAUSED is reopened too (monitor pauses only ads). Reads back. CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMPS = {"config.my5.yaml": ["120251840045110329", "120251840064210329", "120251840367640329"],
         "config.sg.yaml": ["120250544490730521", "120250544550400521", "120250544649500521"]}
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)


def T(fn, *a, **k):
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "request limit" not in str(e).lower():
                raise
            print(f"      … 限流，等 60s（{i + 1}/10）"); time.sleep(60)
    raise RuntimeError("throttled")


print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 12, 0, 0), "owner said 星期四 — refusing before 2026-11-12 00:00 MYT"
n_open = 0
for cfg, ids in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for cid in ids:
        c = T(g.get_object, cid, "name,status,effective_status")
        assert "NEW VIDEO" in c["name"] and "1-5-1 | 1110" in c["name"], c
        ads = T(g._get_all, cid + "/ads", {"fields": "name,status,effective_status,adset{id,name,status}", "limit": "20"})
        print(f"  «{c['name']}» {cid} · {c['status']}/{c['effective_status']}")
        for a in sorted(ads, key=lambda x: x["adset"]["name"]):
            ban = compliance.is_banned(a["name"], s.compliance.banned_creatives)
            todo = a["status"] == "PAUSED" and not ban and a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES")
            print(f"      › «{a['adset']['name']}» · ad {a['id']} «{a['name']}» {a['status']}/{a['effective_status']}"
                  + (" → 开回" if todo else (" ⛔ 禁跑/被拒，不开" if (ban or a['effective_status'] in ('DISAPPROVED', 'WITH_ISSUES')) else "")))
            if CONFIRM and todo:
                if a["adset"]["status"] != "ACTIVE":
                    T(g.update_status, a["adset"]["id"], "ACTIVE"); time.sleep(2)
                T(g.update_status, a["id"], "ACTIVE"); time.sleep(2); n_open += 1
        if CONFIRM:
            st = {}
            for a in T(g._get_all, cid + "/ads", {"fields": "effective_status", "limit": "20"}):
                st[a["effective_status"]] = st.get(a["effective_status"], 0) + 1
            b = T(g.get_object, cid, "status,effective_status")
            print(f"    ✅ 回读 campaign {b['status']}/{b['effective_status']} · 广告 {st}")
print(f"开回 {n_open} 支\nREOPEN NEWVIDEO DONE" + ("" if CONFIRM else " (dry-run)"))
