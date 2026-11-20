# -*- coding: utf-8 -*-
"""owner 2026-11-20 22:5x「现在关」(AskUserQuestion after the 22:47 hourly report: 老将 RM150 宽限下 0 报名过 RM60).
Ad-level PAUSE of exactly this one MY 5.0 ad; position asserted first:

  · WINNERS MY | 1-6-6 | 1022 › Broad · 盖电脑 | MY 28+ · Video：盖电脑，喂！ · ad 120251533792260329
    （周四起 RM67.54 / 0 报名，60 天 0 单，monitor reason veteran_wait）

Campaign / ad set not touched. Owner-closed = final. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AID, CM, SM, AM = "120251533792260329", "WINNERS MY | 1-6-6 | 1022", "Broad · 盖电脑 | MY 28+", "盖电脑"
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
a = g.get_object(AID, "name,status,effective_status,adset{id,name,status,daily_budget},campaign{name,status}")
assert CM in a["campaign"]["name"] and a["adset"]["name"] == SM and AM in a["name"], a
print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {AID} · {a['status']}/{a['effective_status']}")
if CONFIRM and a["status"] != "PAUSED":
    g.update_status(AID, "PAUSED"); time.sleep(2)
if CONFIRM:
    b = g.get_object(AID, "status,effective_status")
    print(f"    ✅ 回读 {b['status']}/{b['effective_status']}")
s = a["adset"]
rows = g._get_all(s["id"] + "/ads", {"fields": "name,effective_status", "limit": "100"})
live = [f"{r['name']} · ad {r['id']}" for r in rows if r["effective_status"] == "ACTIVE"]
print(f"  ad set «{s['name']}» {s['status']} · RM{int(s.get('daily_budget') or 0) // 100} · 在跑 ad {len(live)} {live}")
print("CLOSE WINNERS 盖电脑 DONE" + ("" if CONFIRM else " (dry-run)"))
