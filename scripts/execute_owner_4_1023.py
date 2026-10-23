# -*- coding: utf-8 -*-
"""owner 2026-10-23「全部照建议」— (1) pause SG Webinarkit TRAVEL 1-1-5 again (was switched back on by hand);
(2) MY BUSINESS OWNER RM84 → RM120 (undo the monitor's single-ad cut); (4) reopen SG WINNERS Investment ·
用我的方法 ad (monitor paused it on 10/22-outage spend; config hold_ad_until 10/25 keeps it from re-pausing).
(3) = the monitor change, merged separately (PR #78). Ban gate on the reopened ad. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")


def main() -> None:
    sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(sg)
    c = g.get_object("120249918201630521", "name,status")
    print(f"(1) «{c['name']}» {c['status']} → PAUSED")
    if CONFIRM and c["status"] != "PAUSED":
        g.update_status("120249918201630521", "PAUSED"); time.sleep(1)
        print(f"    ✅ {g.get_object('120249918201630521', 'status')['status']}")
    ad = g.get_object("120249964899250521", "name,status,adset{name}")
    assert not compliance.is_banned(ad["name"], sg.compliance.banned_creatives)
    print(f"(4) «{ad['name']}» in «{ad['adset']['name']}» {ad['status']} → ACTIVE · hold_ad_until {sg.kpi.hold_ad_until}")
    if CONFIRM and ad["status"] != "ACTIVE":
        g.update_status("120249964899250521", "ACTIVE"); time.sleep(1)
        print(f"    ✅ {g.get_object('120249964899250521', 'status')['status']}")
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    b = g.get_object("120251454700150329", "name,daily_budget")
    print(f"(2) «{b['name']}» RM{int(b['daily_budget']) // 100} → RM120")
    if CONFIRM and int(b["daily_budget"]) != 12000:
        g.update_daily_budget("120251454700150329", 12000); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object('120251454700150329', 'daily_budget')['daily_budget']) // 100}")
    print("OWNER 4 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
