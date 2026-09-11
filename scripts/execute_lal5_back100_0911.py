# -*- coding: utf-8 -*-
"""Owner 2026-09-11:「我自己改的」— his manual RM100 on SG PURCHASE LAL 5% was
deliberate (deeper than my approved -30%); my cuts script overwrote it to RM220.
Restore the owner's RM100. CONFIRM gate; idempotent."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
FRAG, NEW = "PURCHASE LAL 5% | 1-1-4", 10000   # RM100


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    camps = g._get_all(f"{s.meta.account_path}/campaigns",
                       {"fields": "id,name,daily_budget", "limit": "500"})
    hits = [c for c in camps if FRAG in (c.get("name") or "")]
    if len(hits) != 1:
        print(f"⛔ «{FRAG}» 匹配 {len(hits)} 个 — 停")
        return
    c = hits[0]
    cur = float(c.get("daily_budget") or 0) / 100
    if abs(cur - NEW / 100) < 1:
        print(f"· «{c['name'][:44]}» 已是 RM{NEW/100:.0f} — skip")
        return
    print(f"«{c['name'][:44]}»: RM{cur:.0f} → RM{NEW/100:.0f}/day"
          + ("" if CONFIRM else "  (would)"))
    if CONFIRM:
        g.update_daily_budget(c["id"], NEW)
        time.sleep(3)
        chk = g.get_object(c["id"], "daily_budget")
        print(f"验证 daily_budget=RM{float(chk.get('daily_budget') or 0)/100:.0f}")
    print("DONE" if CONFIRM else "DRY-RUN")


if __name__ == "__main__":
    main()
