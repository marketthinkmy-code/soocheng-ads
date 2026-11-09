# -*- coding: utf-8 -*-
"""owner 2026-11-09 23:5x「A」— pause SG TRAVEL SG › Travel | SG 28+ · Video：年纪大的人做不了交易？ · ad 120250144816380521
(11/6→11/9 ≈ RM390 / 2 报名 ≈ CPL 195; Thu-week RM468/6 = 78 only because of 11/5). No budget moved. Position asserted first.
CONFIRM=true writes, then reads back."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD = "120250144816380521"
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
a = g.get_object(AD, "name,status,effective_status,campaign{name},adset{name}")
assert "TRAVEL SG | 1-1-2 | 1030" in a["campaign"]["name"] and a["adset"]["name"] == "Travel | SG 28+" and "年纪大" in a["name"], a
print(f"  «{a['campaign']['name']}» › {a['adset']['name']} · {a['name']} · ad {AD} · {a['status']}/{a['effective_status']} → PAUSED")
if CONFIRM and a["status"] != "PAUSED":
    g.update_status(AD, "PAUSED"); time.sleep(2)
    b = g.get_object(AD, "status,effective_status")
    print(f"    ✅ {b['status']}/{b['effective_status']}")
print("PAUSE TRAVEL SG 1109 DONE" + ("" if CONFIRM else " (dry-run)"))
