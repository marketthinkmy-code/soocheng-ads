# -*- coding: utf-8 -*-
"""owner 2026-10-23「开」— reopen SG PURCHASE LAL 5% · 不选 forex ad (monitor paused it on 10/22-outage spend;
kpi.hold_ad_until keeps it through 10/25). SG only — 不选 forex must never run on MY. Ban gate. CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD = "120249918200750521"

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
assert s.meta.account_path.endswith("893025326577600")
g = graph_client(s)
a = g.get_object(AD, "name,status,effective_status,adset{name}")
assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and AD in s.kpi.hold_ad_until
print(f"«{a['name']}» in «{a['adset']['name']}» {a['status']} → ACTIVE · hold to {s.kpi.hold_ad_until[AD]}")
if CONFIRM and a["status"] != "ACTIVE":
    g.update_status(AD, "ACTIVE")
    print(f"  ✅ {g.get_object(AD, 'status')['status']}")
print("FOREX REOPEN DONE" + ("" if CONFIRM else " (dry-run)"))
