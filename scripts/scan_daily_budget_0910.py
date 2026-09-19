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
        live_ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,effective_status,adset{id},campaign{id}",
             "limit": "500"})
        time.sleep(1.2)
        live_asets = {(a.get("adset") or {}).get("id") for a in live_ads
                      if a.get("effective_status") == "ACTIVE"}
        live_camps = {(a.get("campaign") or {}).get("id") for a in live_ads
                      if a.get("effective_status") == "ACTIVE"}

        by_camp = collections.defaultdict(float)
        phantom = collections.defaultdict(float)   # ACTIVE chain, zero live ads -> can't spend
        for c in camps.values():
            if c.get("effective_status") == "ACTIVE" and c.get("daily_budget"):
                amt = float(c["daily_budget"]) / 100.0                  # CBO
                (by_camp if c["id"] in live_camps else phantom)[c["id"]] += amt
        for a in asets:
            camp = camps.get(a.get("campaign_id")) or {}
            if (a.get("effective_status") == "ACTIVE"
                    and camp.get("effective_status") == "ACTIVE"
                    and a.get("daily_budget")):
                amt = float(a["daily_budget"]) / 100.0                  # ABO
                (by_camp if a["id"] in live_asets else phantom)[camp["id"]] += amt

        total = sum(by_camp.values())
        print(f"═══ [{label}] 目前每日预算（有活广告在跑的才算）═══")
        for cid, amt in sorted(by_camp.items(), key=lambda kv: -kv[1]):
            nm = (camps.get(cid, {}).get("name") or "?")[:52]
            print(f"  RM{amt:>7.0f}/day  {nm}")
        print(f"  ── 合计 RM{total:,.0f}/day")
        if phantom:
            pt = sum(phantom.values())
            print(f"  （另有 RM{pt:,.0f}/day 挂在没活广告的链上，实际烧不了钱：）")
            for cid, amt in sorted(phantom.items(), key=lambda kv: -kv[1]):
                nm = (camps.get(cid, {}).get("name") or "?")[:48]
                print(f"    · RM{amt:>6.0f}  {nm}")
        print()

    print("BUDGET SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
