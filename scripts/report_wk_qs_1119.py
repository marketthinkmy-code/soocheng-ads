# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「为什么 DAY TRADING 的 campaign 还开着？…V4 决定变少 / 年纪大 原本是什么受众在跑？…为什么要加 News V4？什么时候有出单？」).
 A) DAY TRADING campaign: status, budget, every ad inside (status / effective_status).
 B) every ad (MY 5.0 + SG) whose name has 决定变少 or 年纪大: campaign › ad set · ad id, status, created, spend + Meta regs since 10/29,
    sales credited to that exact position (buyer's last ad-UTM registration on/before purchase, strict campaign › ad set › ad).
 C) the Paid rows credited to MY NEW VIDEO · News › News | MY 28+ · V4: date · Channel · Source, and the buyer's registration history. No PII."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
U0 = dt.date(2026, 10, 29)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


rh, reg = table("Register", "Email")
_, paid = table(s0.cpa.sales_tab, "UTM Campaign")
ad_col = next((h for h in rh if cpa._hkey(h) in ("utmadsname", "utmadname")), "UTM Ads Name")
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
regs_by = defaultdict(list)
for i, r in enumerate(reg):
    d = cpa.parse_date(r.get("Created date", ""))
    if d:
        for k in who(r):
            regs_by[k].append((d, i, r))
hist = lambda ks: [r for (_, _), r in sorted({(d, i): r for k in ks for d, i, r in regs_by.get(k, [])}.items())]
key = lambda c, s, a: (_mkey(cpa.norm(c)), _mkey(cpa.norm(s)), cpa.norm(a))
credit = defaultdict(list)   # position key -> [(paid row no, paid dict, history)]
for n, p in enumerate(paid):
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < U0 or not who(p):
        continue
    h = [r for r in hist(who(p)) if U0 <= cpa.parse_date(r["Created date"]) <= d and (r.get("UTM Campaign") or "").strip()]
    if h:
        r = h[-1]
        credit[key(r["UTM Campaign"], r.get("UTM Ads Set", ""), r.get(ad_col, ""))].append((n, p, hist(who(p))))

print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT")
targets = []
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{code}"
    ins = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(U0, TODAY),
                                                                                 "fields": "ad_id,spend,actions", "limit": "500"})}
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,created_time,adset{name,status,daily_budget},"
                                                              "campaign{id,name,status,effective_status,daily_budget}", "limit": "500"})
    if label == "MY":
        print("\n== A) DAY TRADING campaign")
        camps = {}
        for a in ads:
            if "DAY TRADING" in a["campaign"]["name"]:
                camps.setdefault(a["campaign"]["id"], (a["campaign"], []))[1].append(a)
        for cid, (c, lst) in camps.items():
            print(f"   «{c['name']}» · campaign {cid} · 开关 {c['status']} / 实际 {c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
            for a in lst:
                print(f"     - {a['adset']['name']} · {a['name']} · ad {a['id']} · ad 开关 {a['status']} / 实际 {a['effective_status']} · ad set {a['adset']['status']}")
    for a in ads:
        if "决定变少" in a["name"] or "年纪大" in a["name"]:
            i = ins.get(a["id"], {})
            sp = float(i.get("spend") or 0)
            rg = extract_results(i.get("actions"), tok)
            k = key(a["campaign"]["name"], a["adset"]["name"], a["name"])
            targets.append((label, a, sp, rg, credit.get(k, [])))

print("\n== B) 名字有「决定变少」或「年纪大」的所有 ad（10/29 起）")
for crea in ("决定变少", "年纪大"):
    print(f"   -- {crea}")
    for label, a, sp, rg, cr in sorted([t for t in targets if crea in t[1]["name"]], key=lambda t: -t[2]):
        print(f"   {label} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}\n"
              f"        建于 {a['created_time'][:10]} · 现在 {a['effective_status']} · 10/29 起 RM{sp:,.0f} / Meta 报名 {rg:.0f} · 原位成交 {len(cr)}"
              + (f" · CPA RM{sp / len(cr):,.0f}" if cr else ""))

print("\n== C) 算给 News V4 的成交")
for label, a, sp, rg, cr in targets:
    if label == "MY" and "NEW VIDEO · News" in a["campaign"]["name"] and "决定变少" in a["name"]:
        for n, p, h in cr:
            print(f"   Paid 第 {n + 2} 行 · 日期 {p.get('Date')} · Channel {p.get('Channel') or '—'} · Source {p.get('Source') or '—'} · 金额 {p.get('Purchase Amount') or '—'}"
                  f" · Paid UTM {p.get('UTM Campaign') or '—'}")
            for r in h:
                print(f"     报名 {r.get('Created date')} · Source {r.get('Source') or '—'} · UTM {r.get('UTM Campaign') or '—'} › {r.get('UTM Ads Set') or '—'} · {r.get(ad_col) or '—'}")
print("\nWK QS DONE (read-only)")
