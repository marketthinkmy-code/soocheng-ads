# -*- coding: utf-8 -*-
"""owner 2026-11-18 ~22:4x「我刚刚 update 了 paid student list，有成交记录的，都可以一起开，确保有开到哦！有时候 campaign 开了，ad set/ ad 没有开到。」
At/after 11/19 00:00 MYT: every MY 5.0 / SG ad POSITION with ≥1 sale (Paid Student List rows dated ≥ 10/29, matched by email / phone to
Register rows since 10/29 carrying that position's (Webinarkit) UTM — the robust-UTM join of report_cycle_review) is opened on ALL THREE
layers (ad, ad set, campaign) and read back. Never opens a banned / 🚫 / DISAPPROVED ad. No PII printed.
Also prints each position's 60-day spend ÷ sales (the monitor's CPA basis) so positions the monitor would hard-stop (> RM1,200) are visible.
Refuses writes before 2026-11-19 00:00 MYT. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TODAY = NOW.date()
U0 = dt.date(2026, 10, 29)
SEVEN = {"120251454713670329", "120251840045110329", "120251840367640329", "120251454700150329", "120251454704570329",
         "120250144810670521", "120250544490730521"}  # the 7 campaigns the owner closed 11/18 11:21–11:22
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人"), ("赚美金", "赚美金"),
       ("炒了五年", "炒了五年"), ("越认真盯盘", "越认真盯盘"), ("决定变少", "决定变少"), ("不适合你", "这条视频不适合你")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), cpa.norm(a or ""))
key = lambda c, s, a: (core(c), cpa.norm(s or ""), cre(a))
digits = lambda v: re.sub(r"\D", "", v or "")
ids = lambda r: {k for k in ((r.get("Email") or "").strip().lower(), digits(r.get("Phone Number"))[-8:]) if k}
fw = lambda r: ((r.get("Name") or "").split() or [""])[0]
is_bot = lambda r: bool(fw(r)) and (r.get("Experience") or "").strip() == fw(r) * 2

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, k):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if k in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


paid = table(s0.cpa.sales_tab, "UTM Campaign")
regs = table("Register", "Email")
buyers = set()
n_paid = 0
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if d and d >= U0 and ids(p):
        buyers |= ids(p); n_paid += 1
sales_by_key = defaultdict(set)
for r in regs:
    d = cpa.parse_date(r.get("Created date", ""))
    if d and d >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower() and not is_bot(r) and ids(r) & buyers:
        sales_by_key[key(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(tuple(sorted(ids(r))))
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'} · Paid 表 10/29 起成交行 {n_paid} · 能对回广告位置的 key {len(sales_by_key)}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 19, 0, 0), "owner said 00:00 — refusing before 2026-11-19 00:00 MYT"

for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    sp60 = {r["ad_id"]: float(r.get("spend") or 0) for r in g._get_all(acct + "/insights", {
        "fields": "ad_id,spend", "level": "ad", "limit": "1000", "time_range": tr(TODAY - dt.timedelta(days=59), TODAY)})}
    ads = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,adset{id,name,status,daily_budget},campaign{id,name,status,daily_budget}",
                                     "limit": "1000"})
    print(f"\n######## {label}")
    hit = 0
    for a in ads:
        ad_set, camp = a.get("adset") or {}, a.get("campaign") or {}
        n = len(sales_by_key.get(key(camp.get("name"), ad_set.get("name"), a["name"]), ()))
        if not n:
            continue
        hit += 1
        banned = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
        cpa60 = sp60.get(a["id"], 0.0) / n
        print(f"  {camp['name'].replace('(Webinarkit) ', '')} › {ad_set.get('name')} · {a['name']} · ad {a['id']}")
        print(f"     成交 {n} · 60 天花费 RM{sp60.get(a['id'], 0):,.0f} → CPA RM{cpa60:,.0f}{'（超 1,200 硬线，monitor 可能马上关）' if cpa60 > 1200 else ''}"
              f" · 现状 campaign {camp.get('status')} / ad set {ad_set.get('status')} / ad {a['status']} ({a['effective_status']})"
              f"{' · 在 11/18 关的 7 个 campaign 里' if camp.get('id') in SEVEN else ' · ⚠️ 不在那 7 个 campaign 里'}")
        if banned or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
            print("     ⛔ 禁跑 / 被拒 → 不开")
            continue
        if CONFIRM:
            for oid, st in ((a["id"], a["status"]), (ad_set.get("id"), ad_set.get("status")), (camp.get("id"), camp.get("status"))):
                if oid and st != "ACTIVE":
                    g.update_status(oid, "ACTIVE"); time.sleep(2)
            b = g.get_object(a["id"], "status,effective_status,adset{status},campaign{status}")
            print(f"     ✅ 回读 campaign {b['campaign']['status']} / ad set {b['adset']['status']} / ad {b['status']} ({b['effective_status']})")
    print(f"  共 {hit} 支有成交")
print("\nREOPEN SALES ADS 1119 DONE" + ("" if CONFIRM else " (dry-run)"))
