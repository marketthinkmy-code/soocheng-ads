# -*- coding: utf-8 -*-
"""owner 2026-10-26「关 DAY TRADING 里的赚美金」— pause exactly
(Webinarkit) STOCKBLOOM | DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · Video：赚美金，一定要接美国客户？ · ad 120251454718680329
(Thu-week RM151 · 2 reg, CPL 75; never sold at this position). Position is read back and asserted first. CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD = "120251454718680329"

g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
a = g.get_object(AD, "name,status,campaign{name},adset{name}")
assert "DAY TRADING" in a["campaign"]["name"] and "赚美金" in a["name"], a
print(f"{a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {AD} · {a['status']} → PAUSED")
if CONFIRM and a["status"] != "PAUSED":
    g.update_status(AD, "PAUSED")
    print(f"  ✅ {g.get_object(AD, 'status')['status']}")
print("DT ZMJ DONE" + ("" if CONFIRM else " (dry-run)"))
