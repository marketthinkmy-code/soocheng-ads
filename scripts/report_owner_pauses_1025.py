# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-25: owner「很多花了 100-300+ 没有 lead / 1 个 lead 还在开的广告，我全部自己关掉了」.
Per account: every ad / ad set / campaign a human paused since 10/25 06:00 UTC, with that ad's spend + registrations
since 10/17 and this Thu-week (10/22→), age, and the creative — so we can see why the monitor had left it running."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

SINCE = int(dt.datetime(2026, 10, 25, 6, 0, tzinfo=dt.timezone.utc).timestamp())
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
CC = {"config.my5.yaml": "1048291251556714", "config.sg.yaml": "1614065190214320"}


def ins(g, oid, tok, since):
    r = g._get_all(oid + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": since, "until": TODAY})})
    r = r[0] if r else {}
    return float(r.get("spend") or 0), extract_results(r.get("actions"), tok)


for cfg, cc in CC.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{cc}"
    acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data", "since": str(SINCE), "limit": "500"})
    seen = set()
    print(f"\n## {cfg}")
    for a in acts:
        if a.get("actor_name") in ("STOCKBLOOM-ADS", "Meta", None) or "run_status" not in (a.get("event_type") or ""):
            continue
        if '"Inactive"' not in (a.get("extra_data") or "") or a["object_id"] in seen:
            continue
        try:
            ed = json.loads(a.get("extra_data") or "{}")
            if ed.get("new_value") != "Inactive":
                continue
        except Exception:                                                # noqa: BLE001
            continue
        seen.add(a["object_id"])
        oid = a["object_id"]
        lvl = a["event_type"].replace("update_", "").replace("_run_status", "")
        s1, r1 = ins(g, oid, tok, "2026-10-17"); time.sleep(0.3)
        s2, r2 = ins(g, oid, tok, "2026-10-22"); time.sleep(0.3)
        print(f"  {a['event_time'][5:16]} {a['actor_name'][:14]:<14} {lvl:<8} «{(a.get('object_name') or '')[:40]}» {oid} · "
              f"10/17起 RM{s1:.0f}/{r1:.0f} · 本周 RM{s2:.0f}/{r2:.0f}")
print("\nOWNER PAUSES DONE (read-only)")
