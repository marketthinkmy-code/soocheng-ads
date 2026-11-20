# -*- coding: utf-8 -*-
"""owner 2026-11-20 23:0x「如果 campaign 里 ad set 都关完了，请帮我把 campaign 也关掉」.

For MY 5.0 + SG: every campaign whose own status is ACTIVE but that has NO ad that could run
(ad.status ACTIVE and its ad set status ACTIVE) → campaign-level PAUSE. Ads / ad sets are not touched.
Also lists, per ACTIVE campaign, which ads are still set to run, so nothing with a live ad is closed.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
print("APPLY" if CONFIRM else "DRY-RUN")
for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.ad_account_id if str(s.meta.ad_account_id).startswith("act_") else f"act_{s.meta.ad_account_id}"
    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    active = [c for c in camps if c.get("status") == "ACTIVE"]
    print(f"\n######## {label} · ACTIVE campaigns {len(active)}")
    for c in active:
        ads = g._get_all(c["id"] + "/ads", {"fields": "id,name,status,effective_status,adset{name,status}", "limit": "200"})
        live = [a for a in ads if a.get("status") == "ACTIVE" and (a.get("adset") or {}).get("status") == "ACTIVE"]
        bud = f"CBO RM{int(c['daily_budget']) // 100}" if c.get("daily_budget") else "ABO"
        if live:
            names = "; ".join(f"{a['adset']['name']} · {a['name']} · ad {a['id']} [{a['effective_status']}]" for a in live)
            print(f"  KEEP  {c['name']} · campaign {c['id']} · {bud} · 在跑 {len(live)}：{names}")
            continue
        print(f"  EMPTY {c['name']} · campaign {c['id']} · {bud} · 0 支可跑 ad（共 {len(ads)} 支 ad）")
        if CONFIRM:
            g.update_status(c["id"], "PAUSED"); time.sleep(2)
            b = g.get_object(c["id"], "status,effective_status")
            print(f"        ✅ 回读 {b['status']}/{b['effective_status']}")
print("\nCLOSE EMPTY CAMPAIGNS DONE" + ("" if CONFIRM else " (dry-run)"))
