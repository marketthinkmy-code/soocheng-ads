# -*- coding: utf-8 -*-
"""owner 2026-11-18 ~21:0x「等下 00:00 开完我今天 11:20am 左右关的广告」: at 11/19 00:00 MYT re-open, at CAMPAIGN level only,
the 7 campaigns the owner paused by hand on 11/18 11:21–11:22 (activity log, actor Thelyin Siew). Ad sets / ads are NOT touched —
ads paused by the monitor or by the owner stay paused (the 盖电脑 ad layer is a separate approved 00:01 script).
Safety gate per campaign: if any ACTIVE ad under it is banned / 🚫 / DISAPPROVED → that campaign is NOT opened (reported).
Refuses writes before 2026-11-19 00:00 MYT. CONFIRM=true writes + reads back; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CAMPS = {
    "config.my5.yaml": [("120251454713670329", "DAY TRADING | 1-1-5 | 1017"), ("120251840045110329", "NEW VIDEO · News | 1-5-1 | 1110"),
                        ("120251840367640329", "NEW VIDEO · Broad | 1-5-1 | 1110"), ("120251454700150329", "BUSINESS OWNER | 1-1-5 | 1017"),
                        ("120251454704570329", "BROAD MY | 1-1-5 | 1017")],
    "config.sg.yaml": [("120250144810670521", "BROAD SG | 1-1-5 | 1030"), ("120250544490730521", "NEW VIDEO · Broad | 1-5-1 | 1110")],
}
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 19, 0, 0), "owner said 00:00 — refusing before 2026-11-19 00:00 MYT"
tot = 0.0
for cfg, camps in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    print(f"\n######## {cfg}")
    for cid, must in camps:
        c = g.get_object(cid, "name,status,effective_status,daily_budget")
        assert must in c["name"], (cid, c["name"])
        ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{id,name,status,daily_budget}", "limit": "200"})
        armed = [a for a in ads if a["status"] == "ACTIVE" and (a.get("adset") or {}).get("status") == "ACTIVE"]
        bad = [a for a in armed if compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
               or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES")]
        cb = int(c.get("daily_budget") or 0) / 100
        print(f"  {c['name']} · campaign {cid} · {c['status']} · {'CBO RM%g' % cb if cb else 'ABO'}")
        for a in armed:
            ab = int((a["adset"].get("daily_budget") or 0)) / 100
            print(f"     会跑：{a['adset']['name']} · {a['name']} · ad {a['id']}" + (f" · ad set RM{ab:g}" if ab else ""))
            tot += ab
        if not armed:
            print("     （底下没有 ad 层开着的广告 → 开了也不会花钱）")
        if bad:
            print("     ⛔ 有禁跑 / 被拒的 ad 上膛，这个 campaign 不开：" + "；".join(f"{a['name']} · ad {a['id']}" for a in bad))
            continue
        if armed and cb:
            tot += cb
        if CONFIRM and c["status"] != "ACTIVE":
            g.update_status(cid, "ACTIVE"); time.sleep(2)
        if CONFIRM:
            b = g.get_object(cid, "status,effective_status")
            print(f"     ✅ 回读 campaign {b['status']}/{b['effective_status']}")
print(f"\n会花钱的日预算合计约 RM{tot:,.0f}（不含 00:01 才开 ad 层的 BUSINESS OWNER 盖电脑）")
print("REOPEN CAMPAIGNS 1119 DONE" + ("" if CONFIRM else " (dry-run)"))
