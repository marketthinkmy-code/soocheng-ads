# -*- coding: utf-8 -*-
"""READ-ONLY: current configured daily budgets, MY + SG.

Sums ACTIVE spend paths only: CBO campaign daily_budget, plus ABO ad set
daily_budget where both the ad set and its campaign are ACTIVE. Prints a
per-campaign breakdown so the owner sees where the money sits. Wednesday
note: run before 15:00 MYT the MY numbers are the normal config; after the
weekly-off sweep everything MY reads paused."""
from __future__ import annotations

import collections
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path

        camps = {c["id"]: c for c in g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,effective_status,daily_budget", "limit": "500"})}
        time.sleep(1.2)
        asets = g._get_all(
            f"{acct}/adsets",
            {"fields": "id,name,daily_budget,effective_status,campaign_id",
             "limit": "500"})
        time.sleep(1.2)

        by_camp = collections.defaultdict(float)
        for c in camps.values():
            if c.get("effective_status") == "ACTIVE" and c.get("daily_budget"):
                by_camp[c["id"]] += float(c["daily_budget"]) / 100.0   # CBO
        for a in asets:
            camp = camps.get(a.get("campaign_id")) or {}
            if (a.get("effective_status") == "ACTIVE"
                    and camp.get("effective_status") == "ACTIVE"
                    and a.get("daily_budget")):
                by_camp[camp["id"]] += float(a["daily_budget"]) / 100.0  # ABO

        total = sum(by_camp.values())
        print(f"═══ [{label}] 目前每日预算（ACTIVE 才算）═══")
        for cid, amt in sorted(by_camp.items(), key=lambda kv: -kv[1]):
            nm = (camps.get(cid, {}).get("name") or "?")[:52]
            print(f"  RM{amt:>7.0f}/day  {nm}")
        print(f"  ── 合计 RM{total:,.0f}/day\n")

    print("BUDGET SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
