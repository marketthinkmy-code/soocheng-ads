# -*- coding: utf-8 -*-
"""READ-ONLY detail for the two pending MY recommendations (owner「给我详情」):
  ① TRAVEL MY campaign 120251500767290329 — every ad (live or not): created, status, today · Thu-week · lifetime, strict sales.
     Plus the reallocation targets BUSINESS OWNER 120251454700150329 / LUXURY MY 120251454680840329 (budget, Thu-week, lifetime).
  ② BROAD MY › Broad | MY 28+ · Video：用我的方法 · ad 120251456458520329 — same detail, plus its campaign siblings.
Strict sale = Paid Student List row whose UTM campaign › ad set › ad equals this exact position."""
from __future__ import annotations

import datetime as dt
import json

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
TOK = "offsite_conversion.custom.1048291251556714"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
sales, _c, _h = cpa.parse_sales(SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab), 2399.0)


def ins(obj, since, level="ad"):
    key = "ad_id" if level == "ad" else "campaign_id"
    return {r[key]: (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)) for r in g._get_all(
        obj + "/insights", {"fields": f"{key},spend,actions", "level": level, "limit": "200",
                            "time_range": json.dumps({"since": since.isoformat(), "until": TODAY.isoformat()})})}


f = lambda v: f"RM{v[0]:.0f}/{v[1]:.0f}" + (f"={v[0] / v[1]:.0f}" if v[1] else "")


def camp_detail(cid):
    c = g.get_object(cid, "name,effective_status,daily_budget,created_time")
    td, wk, lt = ins(cid, TODAY), ins(cid, THU), ins(cid, dt.date(2026, 10, 1))
    tot = [0.0, 0.0]
    for v in lt.values():
        tot[0] += v[0]; tot[1] += v[1]
    wt = [sum(v[0] for v in wk.values()), sum(v[1] for v in wk.values())]
    print(f"\n«{c['name']}» · campaign {cid} · {c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100}/天 · 建于 {c['created_time'][:10]}")
    print(f"   campaign 合计：周四起 {f(wt)} · 建立至今 {f(tot)}")
    for a in g._get_all(cid + "/ads", {"fields": "name,effective_status,created_time,adset{name}", "limit": "50"}):
        key = (_mkey(c["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"]))
        n = sum(1 for x in sales if (_mkey(x.campaign), _mkey(x.adset), x.ad) == key)
        if a["id"] not in lt and a["effective_status"] != "ACTIVE":
            continue
        print(f"   · {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['effective_status']} · 今天 {f(td.get(a['id'], (0, 0)))} · "
              f"周四起 {f(wk.get(a['id'], (0, 0)))} · 至今 {f(lt.get(a['id'], (0, 0)))} · 原位成交 {n}")
    return c


print(f"窗口：周四 {THU} → 今天 {TODAY}")
print("\n================ ① TRAVEL MY")
camp_detail("120251500767290329")
print("\n   ── 转去的目标 ──")
for cid in ("120251454700150329", "120251454680840329"):
    camp_detail(cid)
print("\n================ ② BROAD MY")
camp_detail("120251454704570329")
print("\nMY PENDING DONE (read-only)")
