# -*- coding: utf-8 -*-
"""READ-ONLY: MY 5.0 right now, light on API calls (3): live ads grouped campaign › ad set › ad (id), with today and
Thursday-to-today spend · registrations; per-campaign today totals. Positions straight from the API (死忌 #1)."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
TOK = "offsite_conversion.custom.1048291251556714"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
acct = s.meta.account_path


def ins(since):
    return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)) for r in g._get_all(
        acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500",
                             "time_range": json.dumps({"since": since.isoformat(), "until": TODAY.isoformat()})})}


td = ins(TODAY); time.sleep(2)
wk = ins(THU); time.sleep(2)
ads = g._get_all(acct + "/ads", {"fields": "name,effective_status,campaign{name},adset{name}", "limit": "500"})
tree = defaultdict(lambda: defaultdict(list))
camp_today = defaultdict(lambda: [0.0, 0.0])
for a in ads:
    c = a["campaign"]["name"]
    if a["id"] in td:
        camp_today[c][0] += td[a["id"]][0]; camp_today[c][1] += td[a["id"]][1]
    if a.get("effective_status") == "ACTIVE":
        tree[c][a["adset"]["name"]].append(a)
for c in sorted(tree, key=lambda c: -camp_today[c][0]):
    sp, rg = camp_today[c]
    print(f"\n«{c}» 今天 RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else ""))
    for st, lst in tree[c].items():
        print(f"  › {st}")
        for a in sorted(lst, key=lambda a: -td.get(a["id"], (0, 0))[0]):
            ts, tr = td.get(a["id"], (0.0, 0.0)); ws, wr = wk.get(a["id"], (0.0, 0.0))
            print(f"      · {a['name']} · ad {a['id']} · 今天 RM{ts:.0f}/{tr:.0f} · 周四起 RM{ws:.0f}/{wr:.0f}" + (f"={ws / wr:.0f}" if wr else ""))
tsp, trg = sum(v[0] for v in td.values()), sum(v[1] for v in td.values())
print(f"\nMY 今天合计 RM{tsp:.0f} · 报名 {trg:.0f} · CPL {tsp / trg if trg else 0:.0f}")
print("MY STATE DONE (read-only)")
