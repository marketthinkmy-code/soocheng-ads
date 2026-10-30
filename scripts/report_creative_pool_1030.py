# -*- coding: utf-8 -*-
"""READ-ONLY: which creatives to put into a new SG test. Last 14 days (10/16→today), per creative name (prefixes like 🌟 /
HOOK： stripped), MY 5.0 vs SG: spend · reg · CPL · number of ads · live count; and whether SG's ban gate blocks it.
Also SG last-14-day reach / frequency / CPM per campaign (audience saturation)."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
WIN = json.dumps({"since": "2026-10-16", "until": TODAY.isoformat()})
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
norm = lambda n: n.replace("🚫", "").replace("🌟", "").replace("HOOK：", "").strip()
agg = defaultdict(lambda: {"MY": [0.0, 0.0, 0, 0], "SG": [0.0, 0.0, 0, 0]})
sg_settings = None
for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    if label == "SG":
        sg_settings = s
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{cc}"
    live = {a["id"]: a for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status", "limit": "1000"})}
    perf = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"fields": "ad_id,ad_name,spend,actions", "level": "ad", "time_range": WIN, "limit": "1000"})}
    for aid, r in perf.items():
        k = norm(r.get("ad_name") or "")
        v = agg[k][label]
        v[0] += float(r.get("spend") or 0); v[1] += extract_results(r.get("actions"), tok); v[2] += 1
        v[3] += live.get(aid, {}).get("effective_status") == "ACTIVE"
    if label == "SG":
        print("SG 各 campaign 14 天 reach / frequency / CPM:")
        for r in g._get_all(s.meta.account_path + "/insights", {"fields": "campaign_name,spend,reach,frequency,cpm", "level": "campaign", "time_range": WIN, "limit": "200"}):
            if float(r.get("spend") or 0) >= 50:
                print(f"   «{r['campaign_name'][:60]}» RM{float(r['spend']):.0f} · reach {r.get('reach')} · freq {float(r.get('frequency') or 0):.1f} · CPM {float(r.get('cpm') or 0):.0f}")
print("\n素材 · 10/16 起（MY | SG）：花费/报名=CPL · ad 数(在跑) · SG 禁跑闸")
for k, v in sorted(agg.items(), key=lambda kv: -(kv[1]["MY"][1] + kv[1]["SG"][1])):
    if v["MY"][0] + v["SG"][0] < 20:
        continue
    f = lambda x: f"RM{x[0]:.0f}/{x[1]:.0f}" + (f"={x[0] / x[1]:.0f}" if x[1] else "") + f" · {x[2]}({x[3]})"
    print(f"   {k[:40]:<40} MY {f(v['MY']):<26} SG {f(v['SG']):<26} {'🚫 BANNED' if compliance.is_banned(k, sg_settings.compliance.banned_creatives) else 'ok'}")
print("\nCREATIVE POOL DONE (read-only)")
