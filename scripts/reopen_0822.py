# -*- coding: utf-8 -*-
"""Owner 2026-08-22 «执行» — reopen the misjudged CPA-winners (third time for two
of them):

  · MY DAY TRADING (120247921988670575) chain + driver 炒过那么多  (CPA60 203)
  · MY 用我的方法 (120247525704130575) chain + driver              (CPA60 172)
  · MY LAL ladder (120248446935660575): flip the paused freestyle 1 band ads
    back ACTIVE (6 siblings run with sales; CPA60 1,013)

Solo principle: only named drivers wake; all other sibling ads keep their
stored status. Status flips only, idempotent."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
N = cpa.norm

CHAINS = [
    {"cid": "120247921988670575", "label": "DAY TRADING (炒过那么多)",
     "driver": "video 12：炒过那么多，累而且不稳定"},
    {"cid": "120247525704130575", "label": "用我的方法 (1-1-1)",
     "driver": "video 1: 用我的方法，你也可以有将多"},
]
LADDER_CAMP = "120248446935660575"
LADDER_AD = "freestyle 1"


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Reopen 8/22 — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    print(f"═══ [MY] {s.meta.account_path} ═══")

    for r in CHAINS:
        try:
            c = g._request("GET", r["cid"], params={"fields": "name,status,daily_budget"})
            print(f"  ● {r['label']}  «{c.get('name')}» [{c.get('status')}] "
                  f"RM{int(c.get('daily_budget') or 0)/100:.0f}/day")
            if not CONFIRM:
                continue
            if c.get("status") != "ACTIVE":
                g.update_status(r["cid"], "ACTIVE")
                print("     ▶ campaign → ACTIVE")
                time.sleep(PACE)
            for aset in g._get_all(f"{r['cid']}/adsets",
                                   {"fields": "id,status", "limit": "10"}):
                if aset.get("status") != "ACTIVE":
                    g.update_status(aset["id"], "ACTIVE")
                    print("     ▶ adset → ACTIVE")
                    time.sleep(PACE)
            for a in g._get_all(f"{r['cid']}/ads",
                                {"fields": "id,name,status", "limit": "20"}):
                if N(a.get("name") or "") == N(r["driver"]):
                    if a.get("status") != "ACTIVE":
                        g.update_status(a["id"], "ACTIVE")
                        print(f"     ▶ driver «{a.get('name')}» → ACTIVE")
                        time.sleep(PACE)
                    else:
                        print("     · driver already ACTIVE")
                elif a.get("status") == "ACTIVE":
                    print(f"     (队友 «{(a.get('name') or '')[:24]}» ACTIVE — 不动)")
            print("     ✅ live")
        except Exception as e:
            print(f"     ❌ {r['label']}: {str(e)[:130]} — continuing")

    try:
        print(f"  ● LAL ladder freestyle 1 归队")
        for a in g._get_all(f"{LADDER_CAMP}/ads",
                            {"fields": "id,name,status,adset{name}", "limit": "40"}):
            if N(a.get("name") or "") != N(LADDER_AD):
                continue
            band = ((a.get("adset") or {}).get("name") or "")[:34]
            if a.get("status") == "ACTIVE":
                print(f"     · ACTIVE 已在跑  ({band})")
            elif CONFIRM:
                g.update_status(a["id"], "ACTIVE")
                print(f"     ▶ {a['id']} → ACTIVE  ({band})")
                time.sleep(PACE)
            else:
                print(f"     ▶ would ACTIVE {a['id']}  ({band})")
    except Exception as e:
        print(f"     ❌ ladder: {str(e)[:130]} — continuing")

    print("\nREOPEN DONE." if CONFIRM else "\nDRY-RUN.")


if __name__ == "__main__":
    main()
