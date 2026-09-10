# -*- coding: utf-8 -*-
"""READ-ONLY: are the ads behind the 9/8-9/9 sales currently running?

For each (campaign fragment, ad fragment) pair from the sales sheet UTMs,
find the live ad and print campaign / ad set / ad effective_status plus the
budget carrying it. Wednesday note: after 15:00 MYT the MY weekly-off sweep
shows MY entities paused until Thursday 00:00 — that is the cycle, not a
real stop."""
from __future__ import annotations

import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

N = cpa.norm

CHECKS = {
    "MY": [
        ("BROAD MY 25+ | 0905", "korea"),
        ("DAY TRADING | 1-1-3", "炒过那么多"),
    ],
    "SG": [
        ("BROAD SG 25+ | 0905", "用我的方法"),
        ("PURCHASE LAL 5% | 1-1-4", "盖电脑"),
        ("GOLF PICKBLEBALL | 1-1-3", "trading 早就"),
        ("BROAD | 1-1-3 B", "freestyle 1"),
    ],
}


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,effective_status,"
                       "adset{id,name,status,daily_budget},"
                       "campaign{id,name,status,daily_budget}",
             "limit": "500"})
        time.sleep(1.2)
        print(f"═══ [{label}] 成交链当前状态 ═══")
        for camp_frag, ad_frag in CHECKS[label]:
            hits = [a for a in ads
                    if camp_frag in ((a.get("campaign") or {}).get("name") or "")
                    and N(ad_frag) in N(a.get("name") or "")]
            if not hits:
                print(f"  ⛔ 找不到  «{ad_frag}» in «{camp_frag}»")
                continue
            for a in hits:
                aset = a.get("adset") or {}
                camp = a.get("campaign") or {}
                bud = aset.get("daily_budget") or camp.get("daily_budget") or 0
                lvl = "adset" if aset.get("daily_budget") else "camp"
                print(f"  «{(a.get('name') or '')[:34]}» @ «{(camp.get('name') or '')[:40]}»")
                print(f"     ad={a.get('effective_status')} · adset={aset.get('status')} · "
                      f"campaign={camp.get('status')} · budget RM{float(bud)/100:.0f}/day ({lvl})")
        print()
    print("SOLD-ADS CHECK DONE (read-only)")


if __name__ == "__main__":
    main()
