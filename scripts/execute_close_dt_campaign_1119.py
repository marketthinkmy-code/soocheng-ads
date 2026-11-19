# -*- coding: utf-8 -*-
"""owner 2026-11-19 14:4x「day trading（webinarkit）里有什么需要值得开的吗？没有的话，campaign 就关掉。」
report_dt_worth_1119: all 5 ads inside are paused, 0 original-position sales since launch (~RM3,900), one is banned → nothing worth reopening.
Campaign-layer PAUSE of exactly (Webinarkit) STOCKBLOOM | DAY TRADING | 1-1-5 | 1017 · campaign 120251454713670329; asserts no ad inside is
delivering; reads back. Owner-closed = final. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CID, NAME = "120251454713670329", "(Webinarkit) STOCKBLOOM | DAY TRADING | 1-1-5 | 1017"
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
c = g.get_object(CID, "name,status,effective_status,daily_budget")
assert c["name"] == NAME, c
live = [a for a in g._get_all(CID + "/ads", {"fields": "name,effective_status", "limit": "100"}) if a["effective_status"] == "ACTIVE"]
print(f"  «{c['name']}» · campaign {CID} · 现在 {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100} · 在投放的 ad {len(live)}")
assert not live, ("an ad is delivering — refusing", live)
if CONFIRM and c["status"] != "PAUSED":
    g.update_status(CID, "PAUSED")
    time.sleep(3)
if CONFIRM:
    b = g.get_object(CID, "status,effective_status")
    print(f"  ✅ 回读 campaign {b['status']}/{b['effective_status']}")
print("CLOSE DT CAMPAIGN DONE" + ("" if CONFIRM else " (dry-run)"))
