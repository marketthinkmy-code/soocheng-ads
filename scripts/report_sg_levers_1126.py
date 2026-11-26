# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/26「那 SG 要怎么降低 CPL？」). SG history 10/29 → 11/25 (11/13 bot day left out), Meta insights:
① by placement  ② by age  ③ by gender  ④ by hour of day (MYT)  ⑤ by audience (ad set name)  ⑥ by creative (ad name)
⑦ Register: SG-UTM registrations by UTM Placement + buyers (Paid row 0–8 days after that registration; approximate). No PII printed.
MY totals printed for ① as a comparison."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

RANGES = [(dt.date(2026, 10, 29), dt.date(2026, 11, 12)), (dt.date(2026, 11, 14), dt.date(2026, 11, 25))]
f = lambda r, k: float(r.get(k) or 0)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
FIELDS = "spend,impressions,inline_link_clicks,actions"
CREATIVES = ["用我的方法", "年纪大", "决定变少", "盖电脑", "korea", "不选 forex", "我跟你讲", "炒了五年", "不适合你", "越认真盯盘",
             "赚美金", "V1", "V2", "V3"]
AUDS = ["Broad", "LAL", "Investment", "Luxury", "Travel", "Golf", "Business Owner", "News", "Beer", "Omakase", "Day Trading"]


def acc(rows, tok, keyf):
    t = defaultdict(lambda: [0.0] * 5)
    for r in rows:
        k = keyf(r)
        v = t[k]
        v[0] += f(r, "spend"); v[1] += f(r, "impressions"); v[2] += f(r, "inline_link_clicks")
        v[3] += extract_results(r.get("actions"), "landing_page_view"); v[4] += extract_results(r.get("actions"), tok)
    return t


def line(v):
    sp, im, cl, lpv, rg = v
    d = lambda a, b, m=1.0: a / b * m if b else 0
    return (f"RM{sp:6.0f} · CPM RM{d(sp, im, 1000):4.0f} · CTR {d(cl, im, 100):4.2f}% · 每LPV RM{d(sp, lpv):5.2f} · LPV {lpv:4.0f}"
            f" · 报名 {rg:3.0f} · LPV→报名 {d(rg, lpv, 100):4.1f}% · CPL {('RM%.0f' % d(sp, rg)) if rg else '—'}")


def pull(g, acct, params):
    out = []
    for a, b in RANGES:
        out += g._get_all(acct + "/insights", dict(params, time_range=tr(a, b), limit="500"))
    return out


def show(t, tot_min=20):
    tot = sum(v[0] for v in t.values()) or 1
    for k, v in sorted(t.items(), key=lambda kv: -kv[1][0]):
        if v[0] >= tot_min:
            print(f"   {k:<32} {v[0] / tot * 100:3.0f}% · {line(v)}")


print("只读 · SG 10/29 → 11/25（不含 11/13 机器人日）· Meta insights")
for lab, cfg, cc in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab}")
    rows = pull(g, acct, {"fields": FIELDS, "level": "account", "breakdowns": "publisher_platform,platform_position"})
    t = acc(rows, tok, lambda r: f"{r['publisher_platform']}/{r['platform_position']}")
    tot = [sum(v[i] for v in t.values()) for i in range(5)]
    print(f"   合计 {line(tot)}")
    an = [sum(v[i] for k, v in t.items() if not k.startswith("audience_network")) for i in range(5)]
    print(f"   不含 AN {line(an)}")
    print("① 版位：")
    show(t)
    if lab != "SG":
        continue
    for name, bd in (("② 年龄", "age"), ("③ 性别", "gender")):
        print(f"{name}：")
        show(acc(pull(g, acct, {"fields": FIELDS, "level": "account", "breakdowns": bd}), tok, lambda r, bd=bd: r[bd]), 1)
    print("④ 钟点（MYT，三小时一组）：")
    rows = pull(g, acct, {"fields": FIELDS, "level": "account", "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone"})
    t = acc(rows, tok, lambda r: "%02d–%02d 时" % ((int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) // 3) * 3,
                                                  (int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) // 3) * 3 + 3))
    for k, v in sorted(t.items()):
        print(f"   {k:<10} {line(v)}")
    rows = pull(g, acct, {"fields": FIELDS + ",ad_name,adset_name", "level": "ad"})
    print("⑤ 受众（ad set 名字）：")
    show(acc(rows, tok, lambda r: next((a for a in AUDS if a.lower() in r["adset_name"].lower()), "其它:" + r["adset_name"][:20])))
    print("⑥ 素材（ad 名字）：")
    show(acc(rows, tok, lambda r: next((c for c in CREATIVES if c.lower() in r["ad_name"].lower()), "其它:" + r["ad_name"][:20])))

# ⑦ Register — SG-UTM registrations by placement + approximate buyers
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
SID = s0.cpa.spreadsheet_id
digits = lambda v: re.sub(r"\D", "", v or "")


def table(tab, key):
    v = sc.read_tab(SID, tab)
    hi = next(i for i, r in enumerate(v[:10]) if key in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


regs = table("Register", "Email")
paid = table(s0.cpa.sales_tab, "UTM Campaign")
sales = []
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    ids = {k for k in ((p.get("Email") or "").strip().lower(), digits(p.get("Phone Number"))[-8:]) if k}
    if d and ids:
        sales.append((d, ids))
D0, D1 = RANGES[0][0], RANGES[-1][1]
reg, buy = Counter(), Counter()
for r in regs:
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < D0 or d > D1 or d == dt.date(2026, 11, 13):
        continue
    if "[sg]" not in (r.get("UTM Campaign") or "").lower():
        continue
    fw = ((r.get("Name") or "").split() or [""])[0]
    if fw and (r.get("Experience") or "").strip() == fw * 2:
        continue
    pl = (r.get("UTM Placement") or "空").strip() or "空"
    reg[pl] += 1
    ids = {k for k in ((r.get("Email") or "").strip().lower(), digits(r.get("Phone Number"))[-8:]) if k}
    if any(ids & si and 0 <= (sd - d).days <= 8 for sd, si in sales):
        buy[pl] += 1
print("\n⑦ 报名表：带 [SG] UTM 的真报名（去机器人）× UTM Placement · 买家 = 报名后 0–8 天内出现在 Paid（近似）")
for pl, n in reg.most_common(20):
    print(f"   {pl[:40]:40s} 报名 {n:4d} · 买家 {buy[pl]:2d}" + (f" · 报名→成交 {buy[pl] / n:.1%}" if n else ""))
print(f"   合计 报名 {sum(reg.values())} · 买家 {sum(buy.values())}")
print("\nSG LEVERS 1126 DONE (read-only)")
