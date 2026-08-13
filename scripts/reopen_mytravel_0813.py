# -*- coding: utf-8 -*-
"""Owner 2026-08-13 «误关，你开回去 确保他跑»: MY TRAVEL was accidentally paused at
campaign level minutes before the 8/13 scale run. This script:

  1. re-ACTIVATEs campaign STOCKBLOOM | TRAVEL | 1-1-3 (id-verified)
  2. applies the +30% budget the scale run had to skip
  3. walks adset + ads and reports/repairs delivery (its two runners 你没有本钱 +
     盖电脑 get ad-level ACTIVE if the pause cascaded), then prints a final
     three-layer delivery check.

Verify-then-write; idempotent; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 3.0
FACTOR = 1.3

CAMP_NAME = "STOCKBLOOM | TRAVEL | 1-1-3"
CAMP_ID = "120247524817830575"          # known MY TRAVEL id — must match the name lookup
RUNNERS = ("你没有本钱", "盖电脑")       # the two delivering creatives


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Reopen + scale MY TRAVEL — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    camp = None
    for c in g._get_all(f"{acct}/campaigns",
                        {"fields": "id,name,effective_status,daily_budget", "limit": "500"}):
        if (c.get("name") or "").strip() == CAMP_NAME:
            camp = c
            break
    if not camp:
        raise SystemExit(f"⛔ '{CAMP_NAME}' not found")
    if camp["id"] != CAMP_ID:
        raise SystemExit(f"⛔ name matched campaign {camp['id']} but expected {CAMP_ID} — aborting")
    st, cur = camp.get("effective_status"), int(camp.get("daily_budget") or 0)
    print(f"campaign {camp['id']} '{CAMP_NAME}'  status={st}  budget=RM{cur/100:.0f}/day")

    new = int(round(cur * FACTOR / 100.0) * 100)
    if not CONFIRM:
        if st != "ACTIVE":
            print(f"▶ would ACTIVATE campaign")
        print(f"▶ would set budget RM{cur/100:.0f} -> RM{new/100:.0f}/day")
    else:
        if st != "ACTIVE":
            g.update_status(camp["id"], "ACTIVE")
            time.sleep(PACE)
            print(f"✅ campaign {st} -> "
                  f"{g.get_object(camp['id'], 'effective_status').get('effective_status')}")
        else:
            print("✓ campaign already ACTIVE")
        g._request("POST", camp["id"], data={"daily_budget": str(new)})
        time.sleep(PACE)
        after = int((g.get_object(camp["id"], "daily_budget") or {}).get("daily_budget") or 0)
        print(f"✅ budget RM{cur/100:.0f} -> RM{after/100:.0f}/day"
              + ("" if after == new else "  ⚠️ verify mismatch"))

    print("\n── delivery check (adset + ads) ──")
    for aset in g._get_all(f"{camp['id']}/adsets",
                           {"fields": "id,name,status,effective_status", "limit": "10"}):
        print(f"  adset «{aset.get('name')}»  status={aset.get('status')}"
              f"  effective={aset.get('effective_status')}")
        if CONFIRM and aset.get("status") == "PAUSED":
            g.update_status(aset["id"], "ACTIVE")
            time.sleep(PACE)
            print(f"    ✅ adset reactivated -> "
                  f"{g.get_object(aset['id'], 'effective_status').get('effective_status')}")
    time.sleep(PACE)
    for ad in g._get_all(f"{camp['id']}/ads",
                         {"fields": "id,name,status,effective_status", "limit": "50"}):
        nm = ad.get("name") or ""
        line = (f"  ad «{nm[:40]}»  status={ad.get('status')}"
                f"  effective={ad.get('effective_status')}")
        is_runner = any(cpa.norm(r) in cpa.norm(nm) for r in RUNNERS)
        if ad.get("status") == "PAUSED" and is_runner:
            if CONFIRM:
                g.update_status(ad["id"], "ACTIVE")
                time.sleep(PACE)
                line += (" -> ✅ reactivated, effective="
                         f"{g.get_object(ad['id'], 'effective_status').get('effective_status')}")
            else:
                line += "  ▶ would reactivate (runner)"
        print(line)

    if CONFIRM:
        time.sleep(6)
        final = g.get_object(camp["id"], "effective_status").get("effective_status")
        print(f"\nFINAL: campaign effective_status = {final}"
              + ("  ✅ 跑起来了" if final in ("ACTIVE", "IN_PROCESS") else "  ⚠️ check Ads Manager"))
    else:
        print("\nDRY-RUN DONE — set confirm=true to apply.")


if __name__ == "__main__":
    main()
