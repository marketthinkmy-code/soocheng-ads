# -*- coding: utf-8 -*-
"""owner 2026-10-25「原本因为 rejected 而关掉的，都可以开，但开之前先评估」— of the MY 5.0 赚美金 copies the 10/24 ban
paused, only LUXURY MY's (120251454699130329) passes: CPL 22 since 10/17 (RM198 · 9), 3 days RM42 · 2, campaign live.
Not reopened: PURCHASE LAL MY copy (campaign paused, 0 reg) and the 4 pre-Webinarkit 10/08–10/12 campaign copies
(old link, campaigns off). MY 5.0 only (owner test exception, PR #81). CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD = "120251454699130329"

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
a = g.get_object(AD, "name,status,effective_status")
assert not compliance.is_banned(a["name"], s.compliance.banned_creatives), f"still banned: {a['name']}"
print(f"«{a['name']}» {a['status']}/{a['effective_status']} → ACTIVE")
if CONFIRM and a["status"] != "ACTIVE":
    g.update_status(AD, "ACTIVE")
    print(f"  ✅ {g.get_object(AD, 'status')['status']}")
print("LUX REOPEN DONE" + ("" if CONFIRM else " (dry-run)"))
