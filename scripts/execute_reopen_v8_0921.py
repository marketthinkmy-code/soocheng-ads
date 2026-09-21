# -*- coding: utf-8 -*-
"""Owner 2026-09-21「开回 V8」— reopen old «video 8：做么你 trading 不用看盘的？»
@ STOCKBLOOM | DAY TRADING | 0905 (MY) for a 1-week observation at a reduced
carrier budget of RM50/day. The monitor-side cpa.hold exemption merged first
(PR #65) so the hourly CPA hard-stop won't re-pause it. Review 9/28.
CONFIRM gate; idempotent; verified after."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD_RAW = "video 8：做么你 trading 不用看盘的？"
CAMP_SUB = "DAY TRADING | 0905"
BUDGET_CENTS = 5000


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{s.meta.account_path}/ads",
        {"fields": "id,name,status,effective_status,"
                   "campaign{id,name,status,daily_budget},"
                   "adset{id,name,status,daily_budget}", "limit": "500"})
    time.sleep(1.2)
    hits = [a for a in ads
            if (a.get("name") or "").strip() == AD_RAW
            and CAMP_SUB in ((a.get("campaign") or {}).get("name") or "")]
    if len(hits) != 1:
        print(f"⚠️ SKIP: {len(hits)} 个匹配，不猜。")
        return
    a = hits[0]
    aset, camp = a.get("adset") or {}, a.get("campaign") or {}
    carrier = aset if aset.get("daily_budget") else camp
    kind = "adset" if aset.get("daily_budget") else "campaign"
    cur = int(carrier.get("daily_budget") or 0)
    print(f"目标 «{AD_RAW}» @ «{camp.get('name')}» (ad {a.get('status')}, "
          f"adset {aset.get('status')}, campaign {camp.get('status')}, "
          f"{kind} RM{cur / 100:.0f}/day)")
    if not CONFIRM:
        print(f"[dry] OPEN ad + 层(若关) + {kind} 预算 → RM{BUDGET_CENTS / 100:.0f}")
        return
    if cur != BUDGET_CENTS:
        g.update_daily_budget(carrier["id"], BUDGET_CENTS)   # budget first: reopen at RM50
        time.sleep(2.5)
        print(f"✔ {kind} 预算 RM{cur / 100:.0f} → RM{BUDGET_CENTS / 100:.0f}")
    for eid, st_own, lbl in ((a["id"], a.get("status"), "ad"),
                             (aset.get("id"), aset.get("status"), "adset"),
                             (camp.get("id"), camp.get("status"), "campaign")):
        if eid and st_own == "PAUSED":
            g.update_status(eid, "ACTIVE")
            time.sleep(2.5)
            print(f"✔ OPEN {lbl}")
    o = g.get_object(a["id"], fields="effective_status")
    print(f"复核 → {o.get('effective_status')}")
    print("V8 REOPEN DONE")


if __name__ == "__main__":
    main()
