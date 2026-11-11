# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/11 15:2x「我现在手动关完了全部跑着的广告，因为今晚就是直播了」).
Per account: anything still delivering (effective_status ACTIVE at ad level) with campaign › ad set · ad id,
today's spend, and every run-status change since 11/11 12:00 MYT grouped by actor / level (who closed what)."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter, defaultdict

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

SINCE_MYT = dt.datetime(2026, 11, 11, 12, 0)
SINCE_UTC = int(SINCE_MYT.replace(tzinfo=dt.timezone.utc).timestamp()) - 8 * 3600
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()


def T(fn, *a, **k):
    for i in range(5):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if i == 4:
                raise
            print(f"  (retry {i + 1}: {str(e)[:120]})"); time.sleep(20 * (i + 1))


print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT")
for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g, acct = graph_client(s), s.meta.account_path
    camps = {c["id"]: c for c in T(g._get_all, acct + "/campaigns", {"fields": "name,status,effective_status", "limit": "300"})}
    sets = {a["id"]: a for a in T(g._get_all, acct + "/adsets", {"fields": "name,status,effective_status,campaign_id", "limit": "500"})}
    ads = T(g._get_all, acct + "/ads", {"fields": "name,status,effective_status,campaign_id,adset_id", "limit": "2000"})
    spend = T(g._get_all, acct + "/insights", {"fields": "spend", "time_range": json.dumps({"since": TODAY.isoformat(), "until": TODAY.isoformat()})})
    print(f"\n################ {label} · 今天已花 RM{sum(float(r.get('spend') or 0) for r in spend):,.2f}")
    live = [a for a in ads if a["effective_status"] == "ACTIVE"]
    print(f"  还在投放的 ad（effective ACTIVE）: {len(live)}")
    for a in live:
        print(f"   🟢 {camps[a['campaign_id']]['name']} › {sets[a['adset_id']]['name']} · {a['name']} · ad {a['id']}")
    print(f"  campaign 自身状态 ACTIVE: {sum(c['status'] == 'ACTIVE' for c in camps.values())} · "
          f"ad set 自身 ACTIVE: {sum(x['status'] == 'ACTIVE' for x in sets.values())} · ad 自身 ACTIVE: {sum(a['status'] == 'ACTIVE' for a in ads)}")
    for c in camps.values():
        if c["status"] == "ACTIVE":
            print(f"   · campaign 仍是 ACTIVE（自身）: «{c['name']}» · {c['id']} · effective {c['effective_status']}")
    acts = T(g._get_all, acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data",
                                                 "since": str(SINCE_UTC), "limit": "1000"})
    by = Counter(); first = {}; last = {}; detail = defaultdict(list)
    for x in sorted(acts, key=lambda x: x["event_time"]):
        et = x.get("event_type") or ""
        if "run_status" not in et:
            continue
        try:
            ed = json.loads(x.get("extra_data") or "{}")
        except Exception:                                                # noqa: BLE001
            ed = {}
        new = ed.get("new_value"); new = new.get("new_value", new) if isinstance(new, dict) else new
        t = (dt.datetime.fromisoformat(x["event_time"].replace("+0000", "+00:00")) + dt.timedelta(hours=8)).strftime("%H:%M")
        lvl = et.replace("update_", "").replace("_run_status", "")
        k = (x.get("actor_name") or "?", lvl, str(new))
        by[k] += 1; first.setdefault(k, t); last[k] = t
        if lvl in ("campaign", "ad_set"):
            detail[k].append(f"{t} «{x.get('object_name')}» · {x['object_id']}")
    print(f"  12:00 MYT 起的开/关记录:")
    for k, n in sorted(by.items(), key=lambda kv: first[kv[0]]):
        print(f"   [{k[0]}] {k[1]} → {k[2]} ×{n}（{first[k]}–{last[k]}）")
        for d in detail[k]:
            print(f"        {d}")
print("\nALL-OFF CHECK DONE (read-only)")
