# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「day trading（webinarkit）里有什么需要值得开的吗？没有的话，campaign 就关掉」).
Every ad in (Webinarkit) STOCKBLOOM | DAY TRADING | 1-1-5 | 1017: since-launch and 60-day spend / Meta regs (S1 bots off) / sales at
that exact position (buyer's last ad-UTM registration, strict campaign › ad set › ad, as the monitor), 60-day CPA, ban status, and who
paused it last (activity log). No PII."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, build_cpa_context, extract_results, position_sales
from adbot.settings import REPO_ROOT, load_settings

CID = "120251454713670329"
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
tok = "offsite_conversion.custom.1048291251556714"
ctx = build_cpa_context(g, s, TODAY)
sold60, _, spend60, buyers = ctx
bots = buyers.get("bots", {})
camp = g.get_object(CID, "name,status,effective_status,daily_budget")
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · «{camp['name']}» · campaign {CID} · {camp['status']} · CBO RM{int(camp.get('daily_budget') or 0) // 100}")
life = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(dt.date(2026, 10, 16), TODAY),
                                                                              "fields": "ad_id,spend,actions", "limit": "500"})}
acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                         "since": str(int(dt.datetime(2026, 10, 16).timestamp())), "limit": "1000"})
last_off = {}
for x in sorted(acts, key=lambda x: x["event_time"]):
    try:
        ex = json.loads(x.get("extra_data") or "{}")
    except ValueError:
        ex = {}
    if ex.get("new_value") in ("Inactive", "Paused") or ex.get("new_value") == 0:
        last_off[x.get("object_id")] = (x["event_time"], x.get("actor_name"))
ck = _mkey(camp["name"])
for a in g._get_all(CID + "/ads", {"fields": "name,status,effective_status,created_time,adset{name}", "limit": "100"}):
    r = life.get(a["id"], {})
    sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
    k = (ck, _mkey(a["adset"]["name"]), cpa.norm(a["name"]))
    nb = len(bots.get(k, []))
    ns = position_sales(buyers, sold60, ck, a["adset"]["name"], a["name"])
    sp60 = spend60.get(a["id"], 0.0)
    banned = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
    off = last_off.get(a["id"])
    print(f"  {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}{' · ⛔禁跑' if banned else ''}\n"
          f"     上线以来 RM{sp:,.0f} · Meta 报名 {rg:.0f}（机器人 {nb}）· 真 CPL {sp / max(rg - nb, 1):,.0f} · 原位成交 {ns}"
          f" · 60 天 CPA {('RM%.0f' % (sp60 / ns)) if ns else '∞'}"
          + (f" · 最后关闭 {off[0][:16]} UTC by {off[1]}" if off else ""))
print("DT WORTH DONE (read-only)")
