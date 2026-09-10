# -*- coding: utf-8 -*-
"""Owner 2026-09-10:「开回盖电脑那个 campaign」— the SG PURCHASE LAL 5% chain
that sold on 9/9.

Scope: set campaign «PURCHASE LAL 5% | 1-1-4» (SG) ACTIVE, and the sold ad
«盖电脑» inside it ACTIVE. Other ads in the campaign are left untouched so
monitor decisions on them stand. Idempotent; CONFIRM gate."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
N = cpa.norm
CAMP_FRAG = "PURCHASE LAL 5% | 1-1-4"
AD_FRAG = "盖电脑"


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"Reopen SG PURCHASE LAL 5% (盖电脑 成交链) — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    camps = [c for c in g._get_all(
        f"{acct}/campaigns", {"fields": "id,name,status", "limit": "500"})
        if CAMP_FRAG in (c.get("name") or "")]
    time.sleep(1.2)
    if len(camps) != 1:
        print(f"⛔ campaign 匹配到 {len(camps)} 个，不动。{[c.get('name') for c in camps]}")
        return
    camp = camps[0]
    print(f"campaign «{camp['name']}» status={camp['status']}")

    ads = [a for a in g._get_all(
        f"{camp['id']}/ads",
        {"fields": "id,name,status,effective_status", "limit": "100"})
        if N(AD_FRAG) in N(a.get("name") or "")]
    time.sleep(1.2)
    if len(ads) != 1:
        print(f"⛔ ad 匹配到 {len(ads)} 支，不动。{[a.get('name') for a in ads]}")
        return
    ad = ads[0]
    print(f"ad «{ad['name']}» status={ad['status']} effective={ad['effective_status']}")

    if not CONFIRM:
        print("\n▶ would set: campaign ACTIVE + ad ACTIVE（其余 ad 不动）")
        return

    if camp["status"] != "ACTIVE":
        g.update_status(camp["id"], "ACTIVE")
        print("✓ campaign → ACTIVE")
        time.sleep(3)
    else:
        print("· campaign 已是 ACTIVE")
    if ad["status"] != "ACTIVE":
        g.update_status(ad["id"], "ACTIVE")
        print("✓ ad → ACTIVE")
        time.sleep(3)
    else:
        print("· ad 已是 ACTIVE")

    chk = [a for a in g._get_all(
        f"{camp['id']}/ads",
        {"fields": "id,name,status,effective_status", "limit": "100"})
        if a["id"] == ad["id"]][0]
    print(f"\n验证: «{chk.get('name')}» status={chk.get('status')} "
          f"effective={chk.get('effective_status')}")
    print("REOPEN DONE")


if __name__ == "__main__":
    main()
