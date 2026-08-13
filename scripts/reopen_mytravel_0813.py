# -*- coding: utf-8 -*-
"""Owner 2026-08-13 «误关，你开回去 确保他跑»: MY TRAVEL was accidentally paused at
campaign level. The account turns out to hold more than one TRAVEL campaign id under
that family, so this script DIAGNOSES first, then acts:

  1. list every MY campaign with TRAVEL in the name (TOP3 excluded): id, status,
     budget, 3d spend, ads
  2. target = the campaign that carries the 你没有本钱 runner AND had real 3d spend
     (the one that was delivering at CPL ~24 until it got paused today);
     if that is not exactly one campaign, print everything and abort
  3. re-ACTIVATE it, apply the skipped +30% budget, walk adset/ads, final check.

Verify-then-write; idempotent; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import json
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 3.0
FACTOR = 1.3
W_3D = {"since": "2026-08-10", "until": "2026-08-13"}
RUNNER = "你没有本钱"
MIN_3D_SPEND = 100.0


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Reopen + scale MY TRAVEL — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    cands = []
    for c in g._get_all(f"{acct}/campaigns",
                        {"fields": "id,name,effective_status,daily_budget,created_time",
                         "limit": "500"}):
        nm = (c.get("name") or "")
        if "travel" not in cpa.norm(nm) or "top3" in cpa.norm(nm):
            continue
        ads = g._get_all(f"{c['id']}/ads", {"fields": "id,name,status,effective_status",
                                            "limit": "50"})
        time.sleep(1)
        rows = g._request("GET", f"{c['id']}/insights",
                          params={"fields": "spend", "time_range": json.dumps(W_3D)}
                          ).get("data", [])
        spend3 = float(rows[0].get("spend")) if rows else 0.0
        has_runner = any(cpa.norm(RUNNER) in cpa.norm(a.get("name") or "") for a in ads)
        cands.append({"c": c, "ads": ads, "spend3": spend3, "runner": has_runner})
        print(f"· {c['id']}  '{nm}'  {c.get('effective_status')}  "
              f"budget=RM{int(c.get('daily_budget') or 0)/100:.0f}  3d_spend=RM{spend3:.0f}  "
              f"created={str(c.get('created_time'))[:10]}  runner={'Y' if has_runner else 'N'}")
        for a in ads:
            print(f"    - «{(a.get('name') or '')[:40]}»  status={a.get('status')}"
                  f"  effective={a.get('effective_status')}")
        time.sleep(1)

    targets = [x for x in cands if x["runner"] and x["spend3"] >= MIN_3D_SPEND]
    if len(targets) != 1:
        raise SystemExit(f"\n⛔ expected exactly 1 target, found {len(targets)} — not acting; "
                         "review the listing above")
    t = targets[0]
    camp = t["c"]
    st, cur = camp.get("effective_status"), int(camp.get("daily_budget") or 0)
    new = int(round(cur * FACTOR / 100.0) * 100)
    print(f"\nTARGET: {camp['id']} '{camp.get('name')}'  {st}  RM{cur/100:.0f} -> RM{new/100:.0f}/day")

    if not CONFIRM:
        print("▶ would ACTIVATE (if paused) + set the budget above. DRY-RUN DONE.")
        return

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

    for aset in g._get_all(f"{camp['id']}/adsets",
                           {"fields": "id,name,status,effective_status", "limit": "10"}):
        if aset.get("status") == "PAUSED":
            g.update_status(aset["id"], "ACTIVE")
            time.sleep(PACE)
            print(f"✅ adset «{aset.get('name')}» reactivated")
    time.sleep(PACE)
    for a in g._get_all(f"{camp['id']}/ads",
                        {"fields": "id,name,status,effective_status", "limit": "50"}):
        nm = a.get("name") or ""
        if a.get("status") == "PAUSED" and (cpa.norm(RUNNER) in cpa.norm(nm)
                                            or "盖电脑" in nm):
            g.update_status(a["id"], "ACTIVE")
            time.sleep(PACE)
            print(f"✅ ad «{nm[:40]}» reactivated -> "
                  f"{g.get_object(a['id'], 'effective_status').get('effective_status')}")
        else:
            print(f"· ad «{nm[:40]}»  status={a.get('status')}"
                  f"  effective={a.get('effective_status')}")

    time.sleep(6)
    final = g.get_object(camp["id"], "effective_status").get("effective_status")
    print(f"\nFINAL: campaign effective_status = {final}"
          + ("  ✅ 跑起来了" if final in ("ACTIVE", "IN_PROCESS") else "  ⚠️ check Ads Manager"))


if __name__ == "__main__":
    main()
