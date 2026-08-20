# -*- coding: utf-8 -*-
"""READ-ONLY: current status + today's spend for the revived sellers, the trimmed
TRAVEL, the owner-reopened SG BROAD A, and the AUG NEW fleet."""
from __future__ import annotations

import datetime as dt
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 20).isoformat()
WATCH = {
    "MY": ["STOCKBLOOM | DAY TRADING | 1-1-3", "STOCKBLOOM | INVESTMENT | 1-1-3",
           "STOCKBLOOM | 用我的方法 | 1-1-1", "STOCKBLOOM | TRAVEL | 1-1-3"],
    "SG": ["[SG] STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3", "[SG] STOCKBLOOM | RUNNING | 1-1-3",
           "[SG] STOCKBLOOM | BROAD | 1-1-3 A"],
}


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══ [{label}] {acct} ═══")
        camps = {c.get("name"): c for c in g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,effective_status,daily_budget", "limit": "500"})}
        time.sleep(1)
        today = {}
        for r in g.account_insights(acct, level="campaign",
                                    fields="campaign_name,spend,actions",
                                    time_range={"since": TODAY, "until": TODAY}):
            today[r.get("campaign_name")] = (
                float(r.get("spend") or 0),
                extract_results(r.get("actions"), token))
        time.sleep(1)

        for name in WATCH[label]:
            c = camps.get(name)
            if not c:
                print(f"  ?? «{name}» 不存在")
                continue
            sp, ld = today.get(name, (0.0, 0.0))
            print(f"  [{c.get('effective_status'):>8}] RM{int(c.get('daily_budget') or 0)/100:4.0f}/day"
                  f"  今天 RM{sp:5.0f} · {ld:3.0f} 名单   «{name}»")
        aug_sp = aug_ld = 0.0
        aug_n = 0
        for name, c in camps.items():
            if "AUG NEW" in name:
                aug_n += 1
                sp, ld = today.get(name, (0.0, 0.0))
                aug_sp += sp
                aug_ld += ld
        print(f"  AUG NEW ×{aug_n}: 今天合计 RM{aug_sp:.0f} · {aug_ld:.0f} 名单")
        print()
    print("STATE VERIFIED (read-only)")


if __name__ == "__main__":
    main()
