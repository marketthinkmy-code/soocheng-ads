# -*- coding: utf-8 -*-
"""owner 2026-10-12 19:20「MY 的广告 全部加到去 200 perday」: every MY 5.0 campaign CBO -> RM200/day
(DAY TRADING, BUSINESS OWNER, BROAD MY 30+, and the new LUXURY MY once it exists). Prints before/after;
skips a campaign already at RM200; does not touch statuses (LUXURY MY stays on its PAUSED ad-set gate).
CONFIRM=true writes; otherwise dry-run. No PII."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
TARGET = 20000
KNOWN = {"120251329144280329": "DAY TRADING", "120251329164100329": "BUSINESS OWNER", "120251329174460329": "BROAD MY 30+"}
NEW_NAME = "STOCKBLOOM | LUXURY MY | 1-1-4 | 1012"


def rm(c) -> str:
    return f"RM{int(c or 0) / 100:.0f}"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "100"})
    time.sleep(0.8)
    targets = [c for c in camps if c["id"] in KNOWN or (c.get("name") or "") == NEW_NAME]
    missing = [n for cid, n in KNOWN.items() if cid not in {c["id"] for c in targets}]
    if NEW_NAME not in {c.get("name") for c in targets}:
        missing.append("LUXURY MY (not built yet)")
    done = []
    for c in targets:
        cur = int(c.get("daily_budget") or 0)
        tag = f"«{(c.get('name') or '')[:42]}» {c.get('status')} {rm(cur)}"
        if cur == TARGET:
            print(f"  = {tag} (already RM200)"); continue
        print(f"  → {tag} → RM200")
        if CONFIRM:
            g.update_daily_budget(c["id"], TARGET); done.append(c["id"]); time.sleep(1.0)
    if missing:
        print(f"  ! not found: {missing}")
    if not CONFIRM:
        print("DRY RUN — CONFIRM=true 才会写。"); print("MY 200 DONE (dry-run)"); return
    time.sleep(4.0)
    print("\n── 验证 ──")
    for c in g._get_all(acct + "/campaigns", {"fields": "id,name,status,daily_budget", "limit": "100"}):
        if c["id"] in KNOWN or (c.get("name") or "") == NEW_NAME:
            print(f"  «{(c.get('name') or '')[:42]}» {c.get('status')} {rm(c.get('daily_budget'))}")
    print(f"MY 200 DONE ({len(done)} changed)")


if __name__ == "__main__":
    main()
