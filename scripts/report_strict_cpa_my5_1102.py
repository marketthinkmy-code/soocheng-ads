# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/2「我也要知道 CPA，确保是他们自己的 campaign - ad set - ad」).
Every MY 5.0 ad that has spent (10/8 → today), live or paused: lifetime spend · 报名 · CPL · STRICT sales (Paid Student
List rows whose UTM campaign › ad set › ad == this exact position) · strict CPA.
Plus: Paid rows dated ≥ 10/16 — how many carry any MY 5.0 campaign in UTM, and how many have no UTM (explains blanks)."""
from __future__ import annotations

import datetime as dt
import json
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
TOK = "offsite_conversion.custom.1048291251556714"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
sales, _c, _h = cpa.parse_sales(SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab), 2399.0)
strict = Counter((_mkey(x.campaign), _mkey(x.adset), x.ad) for x in sales)
camps = {c["id"]: c["name"] for c in g._get_all(s.meta.account_path + "/campaigns", {"fields": "name", "limit": "300"})}
mykeys = {_mkey(n) for n in camps.values()}

perf = g._get_all(s.meta.account_path + "/insights", {"fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions", "level": "ad", "limit": "1000",
                                                      "time_range": json.dumps({"since": "2026-10-08", "until": TODAY})})
st = {a["id"]: a["effective_status"] for a in g._get_all(s.meta.account_path + "/ads", {"fields": "effective_status", "limit": "1000"})}
rows = []
for r in perf:
    sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)
    if sp < 50:
        continue
    n = strict[(_mkey(r["campaign_name"]), _mkey(r["adset_name"]), cpa.norm(r["ad_name"]))]
    rows.append((r, sp, rg, n))
print(f"MY 5.0 · 10/8 → {TODAY} · 花费 ≥RM50 的 ad（原位 = 同一 campaign › ad set › ad）")
for r, sp, rg, n in sorted(rows, key=lambda x: (-x[3], x[1] / x[2] if x[2] else 9e9)):
    print(f"   {st.get(r['ad_id'], '?'):<16} {r['campaign_name'].replace('(Webinarkit) ', '')[:40]} › {r['adset_name'][:24]} · {r['ad_name'][:28]} · ad {r['ad_id']} · "
          f"RM{sp:.0f}/{rg:.0f}" + (f" CPL {sp / rg:.0f}" if rg else "") + f" · 原位成交 {n}" + (f" · CPA RM{sp / n:,.0f}" if n else " · CPA —"))
recent = [x for x in sales if x.date and x.date >= dt.date(2026, 10, 16)]
print(f"\nPaid 表 10/16 起的成交 {len(recent)} 笔：UTM campaign 属于 MY 5.0 的 {sum(_mkey(x.campaign) in mykeys for x in recent)} 笔 · "
      f"UTM 空白 {sum(not (x.campaign or '').strip() for x in recent)} 笔 · 其他（旧账户/旧 campaign/自然）{sum(bool((x.campaign or '').strip()) and _mkey(x.campaign) not in mykeys for x in recent)} 笔")
print("STRICT CPA MY5 DONE (read-only)")
