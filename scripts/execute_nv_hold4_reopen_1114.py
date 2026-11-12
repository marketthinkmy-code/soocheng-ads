# -*- coding: utf-8 -*-
"""owner 2026-11-12「做」— Sat 11/14 00:00 MYT: reopen the 4 NEW VIDEO ads parked by execute_nv_hold4_pause_1112.py.
Refuses before 2026-11-14 00:00 MYT. Skips any ad that is banned / 🚫 / DISAPPROVED, or whose ad set / campaign is no
longer ACTIVE (owner may have changed things — report, don't touch). Reads back. CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
HOLD = {"120251840352430329": "Luxury Goods | MY 28+ · V2", "120251840350550329": "Luxury Goods | MY 28+ · V1",
        "120251840364150329": "Luxury Goods | MY 28+ · V4", "120251840063080329": "News | MY 28+ · V5"}
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 14, 0, 0), "owner: 2 天后 — refusing before 2026-11-14 00:00 MYT"
n = 0
for aid, aset in HOLD.items():
    a = g.get_object(aid, "name,status,effective_status,adset{name,status},campaign{name,status}")
    assert "NEW VIDEO" in a["campaign"]["name"] and a["adset"]["name"] == aset, (aid, a)
    ban = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
    ok = (a["status"] == "PAUSED" and not ban and a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES")
          and a["adset"]["status"] == "ACTIVE" and a["campaign"]["status"] == "ACTIVE")
    why = "" if ok else (" ⛔ 禁跑/被拒" if ban or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES") else
                         f" ⚠️ 不动（ad {a['status']} · ad set {a['adset']['status']} · campaign {a['campaign']['status']}）")
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']}"
          + (" → 开回" if ok else why))
    if CONFIRM and ok:
        g.update_status(aid, "ACTIVE"); time.sleep(2); n += 1
if CONFIRM:
    time.sleep(3)
    for aid in HOLD:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 ad {aid} · {b['status']}/{b['effective_status']}")
print(f"开回 {n} 支\nNV HOLD4 REOPEN DONE" + ("" if CONFIRM else " (dry-run)"))
