# -*- coding: utf-8 -*-
"""READ-ONLY: are last night's (webinar_aug26) selling ads still ON?

For each seller (campaign-fragment, ad-needle) from the owner's Paid-list
screenshot, print ad own-status + effective_status + campaign/adset state so
any accidentally-closed seller is obvious. Includes the older aug5/aug19
sellers seen in the same screenshot as secondary checks."""
from __future__ import annotations

import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

SELLERS = {
    "MY": [
        ("AUG NEW D", "年纪大", "aug26 ×2"),
        ("PURCHASE LAL 1-5%", "你敢吗", "aug26 ×2"),
        ("DAY TRADING", "炒过那么多", "aug12"),
    ],
    "SG": [
        ("RUNNING", "你敢吗", "aug26"),
        ("PURCHASE LAL 5%", "市场不考你的英文", "aug26"),
        ("PURCHASE LAL 5%", "盖电脑", "aug26"),
        ("LUXURY WATCHES", "不选 forex", "aug26"),
        ("LUXURY WATCHES", "赚美金，一定要接美国客户", "aug19"),
        ("BROAD NEW HOOK B", "indicator", "aug26"),
        ("AUG NEW D", "求人", "aug26"),
        ("BROAD | 1-1-3 B", "freestyle 1", "aug5"),
    ],
}


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,effective_status,"
                       "campaign{name,effective_status,daily_budget},"
                       "adset{name,effective_status,daily_budget}",
             "limit": "500"})
        time.sleep(1)
        for camp_frag, needle, note in SELLERS[label]:
            hits = [a for a in ads
                    if needle in (a.get("name") or "")
                    and camp_frag in ((a.get("campaign") or {}).get("name") or "")]
            if not hits:
                print(f"  ?? 找不到  «{needle}» in «{camp_frag}»  ({note})")
                continue
            for a in hits:
                c = a.get("campaign") or {}
                aset = a.get("adset") or {}
                est = a.get("effective_status")
                mark = "✅" if est == "ACTIVE" else "🔴"
                bud = int(c.get("daily_budget") or aset.get("daily_budget") or 0) / 100
                print(f"  {mark} [{est:>15}] ad-own={a.get('status'):>6}  "
                      f"camp={c.get('effective_status'):>6}/{aset.get('effective_status'):>6}"
                      f"  RM{bud:.0f}  «{(a.get('name') or '')[:30]}»"
                      f"  in «{(c.get('name') or '')[:36]}»  ({note})")
        print()
    print("SELLER SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
