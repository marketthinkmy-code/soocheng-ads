# -*- coding: utf-8 -*-
"""owner 2026-10-25「做」— item 2 of the SG 3-day review: move budget to the 4 SG carriers under the line
(3-day CPL): DAY TRADING SG 60→90 (43) · WINNERS Investment · 我跟你讲 50→65 (48) · LAL 5% · 盖电脑 50→65 (61) ·
Investment · 用我的方法 65→80 (70). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = {"120250027169830521": 9000,   # DAY TRADING SG (CBO)
        "120250008788740521": 6500,   # Investment · 我跟你讲
        "120250008788120521": 6500,   # LAL 5% · 盖电脑
        "120249964897130521": 8000}   # Investment | SG 28+ (用我的方法)


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    for oid, cents in PLAN.items():
        o = g.get_object(oid, "name,status,daily_budget")
        print(f"  «{o['name']}» {o['status']} RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
        if CONFIRM and int(o.get("daily_budget") or 0) != cents:
            g.update_daily_budget(oid, cents); time.sleep(1)
            print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
    print("SG RAISE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
