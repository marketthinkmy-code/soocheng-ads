# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-11「SG 的最近 cpl 很高」— quantify it.

  1. SG account-level daily spend/reg/CPL for the last 14 days (when did it jump).
  2. Per-campaign split: last 7 days vs the 7 before (who drives the jump)."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

TOKEN = "offsite_conversion.fb_pixel_complete_registration"


def regs(row) -> float:
    return sum(float(a.get("value") or 0) for a in (row.get("actions") or [])
               if a.get("action_type") == TOKEN)


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # SGT/MYT
    d14 = today - dt.timedelta(days=13)

    rows = g._get_all(f"{acct}/insights", {
        "fields": "spend,actions", "time_increment": "1", "limit": "100",
        "time_range": json.dumps({"since": d14.isoformat(), "until": today.isoformat()})})
    print("═══ SG 逐日（14 天）═══")
    for r in rows:
        sp = float(r.get("spend") or 0)
        n = regs(r)
        cpl = f"RM{sp / n:6.1f}" if n else ("   —  " if sp < 1 else "   ∞  ")
        print(f"  {r.get('date_start')}  spend RM{sp:8.2f}  reg {n:4.0f}  CPL {cpl}")
    time.sleep(1.5)

    wins = {"prev7": (today - dt.timedelta(days=13), today - dt.timedelta(days=7)),
            "last7": (today - dt.timedelta(days=6), today)}
    per: dict = {}
    for label, (a, b) in wins.items():
        for r in g.account_insights(acct, level="campaign",
                                    fields="campaign_name,spend,actions",
                                    time_range={"since": a.isoformat(), "until": b.isoformat()}):
            nm = (r.get("campaign_name") or "?")[:46]
            per.setdefault(nm, {})[label] = (float(r.get("spend") or 0), regs(r))
        time.sleep(1.5)

    def cplf(sp, n):
        return f"{sp / n:6.1f}" if n else ("   —  " if sp < 1 else "   ∞  ")

    print("\n═══ SG 各 campaign：近 7 天 vs 前 7 天（spend / reg / CPL）═══")
    for nm, w in sorted(per.items(), key=lambda kv: -(kv[1].get("last7", (0.0, 0.0))[0])):
        s2, n2 = w.get("last7", (0.0, 0.0))
        s1, n1 = w.get("prev7", (0.0, 0.0))
        if s1 < 1 and s2 < 1:
            continue
        print(f"  {nm:<46} 近7: {s2:7.0f}/{n2:3.0f}/{cplf(s2, n2)}   "
              f"前7: {s1:7.0f}/{n1:3.0f}/{cplf(s1, n1)}")
    print("\nSG CPL TREND DONE (read-only)")


if __name__ == "__main__":
    main()
