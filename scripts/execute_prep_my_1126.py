# -*- coding: utf-8 -*-
"""owner 11/25「不建新的」— next cycle MY = only the existing CBO · LUX BEER OMAKASE | 1-3-3 | 1120 (RM100) and
BROAD MY | 1-1-5 | 1017 (RM100) running 用我的方法 only; korea in BROAD MY ad-level PAUSED; campaigns are opened by the OWNER.
This script: lists both campaigns (budget, every ad with all 3 layers, banned / rejected check, Webinarkit prefix), and with
CONFIRM=true PAUSES ONLY ad 120251456191090329 (BROAD MY › Broad | MY 28+ · freestyle: korea) and reads it back.
Campaign / ad set layers are never touched."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
CAMPS = {"120251454704570329": "BROAD MY", "120251995650640329": "CBO · LUX BEER OMAKASE"}
KOREA = "120251456191090329"
for cid in CAMPS:
    c = g.get_object(cid, "name,status,effective_status,daily_budget")
    print(f"\n{c['name']} · campaign {cid} · {c['status']} → {c['effective_status']} · CBO RM{float(c.get('daily_budget') or 0) / 100:.0f}"
          f"{'' if c['name'].startswith('(Webinarkit)') else ' ⚠️ 不是 (Webinarkit)'}")
    for a in g._get_all(f"{cid}/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "100"}):
        flag = " ⛔禁跑" if (compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]) else ""
        flag += " ⚠️被拒" if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES") else ""
        will = " ← 会跑" if a["status"] == "ACTIVE" and a["adset"]["status"] == "ACTIVE" and a["id"] != KOREA else ""
        print(f"  {c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}{flag}{will}")
a = g.get_object(KOREA, "name,status,campaign{id},adset{name}")
assert a["campaign"]["id"] == "120251454704570329" and "korea" in a["name"].lower(), a
print(f"\nPAUSE（只动 ad 层）BROAD MY › {a['adset']['name']} · {a['name']} · ad {KOREA} · 现在 ad {a['status']}")
if CONFIRM and a["status"] != "PAUSED":
    g._request("POST", KOREA, data={"status": "PAUSED"}); time.sleep(1)
    print(f"  ✅ 回读 {g.get_object(KOREA, 'status')['status']}")
print("PREP MY 1126 DONE" + ("" if CONFIRM else " (dry-run)"))
