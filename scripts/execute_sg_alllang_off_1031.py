# -*- coding: utf-8 -*-
"""owner 2026-10-31「關」— PAUSE «(Webinarkit) [SG] STOCKBLOOM | PURCHASE LAL 5% · ALL LANG | 1-1-4 | 1026» campaign
120250072526350521 (RM50; 10/29→10/31 RM122.89 / 0 报名). Name asserted first (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
OID = "120250072526350521"
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
o = g.get_object(OID, "name,status")
assert "PURCHASE LAL 5% · ALL LANG" in o["name"] and "(Webinarkit) [SG]" in o["name"], f"{OID} is «{o['name']}»"
print(f"  PAUSE «{o['name']}» · campaign {OID} · now {o['status']}")
if CONFIRM and o["status"] != "PAUSED":
    g.update_status(OID, "PAUSED"); time.sleep(1)
    print(f"    ✅ {g.get_object(OID, 'status')['status']}")
print("SG ALL LANG OFF DONE" + ("" if CONFIRM else " (dry-run)"))
