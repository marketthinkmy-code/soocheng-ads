# -*- coding: utf-8 -*-
"""READ-ONLY final check of the AUG NEW fleet: for each of the 10 campaigns print
status + budget, the ad set's start_time/status, and every ad (status + effective
status). Confirms 30/30 before the 2026-08-20 00:00 MYT scheduled start."""
from __future__ import annotations

import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

ACCTS = (("MY", "config.yaml", "STOCKBLOOM | AUG NEW"),
         ("SG", "config.sg.yaml", "[SG] STOCKBLOOM | AUG NEW"))


def main() -> None:
    total = 0
    for label, cfg, prefix in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"══ {label}  {acct} ══")
        camps = [c for c in g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,effective_status,daily_budget", "limit": "500"})
            if (c.get("name") or "").startswith(prefix)]
        time.sleep(1)
        for c in sorted(camps, key=lambda x: x.get("name") or ""):
            print(f"  [{c.get('effective_status')}] {c.get('name')}  "
                  f"RM{int(c.get('daily_budget') or 0)/100:.0f}/day")
            for a in g._get_all(f"{c['id']}/adsets",
                                {"fields": "id,name,status,start_time", "limit": "5"}):
                print(f"    adset {a.get('status')}  start={a.get('start_time')}")
            time.sleep(1)
            ads = g._get_all(f"{c['id']}/ads",
                             {"fields": "id,name,status,effective_status", "limit": "50"})
            time.sleep(1)
            total += len(ads)
            for a in ads:
                print(f"      · «{(a.get('name') or '')[:44]}»  {a.get('status')}"
                      f" / {a.get('effective_status')}")
        print()
    print(f"TOTAL ADS IN FLEET: {total} (expect 30)")


if __name__ == "__main__":
    main()
