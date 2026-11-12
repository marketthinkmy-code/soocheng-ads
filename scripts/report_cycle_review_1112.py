# -*- coding: utf-8 -*-
"""READ-ONLY Thursday review (owner 11/12「来，星期四复盘。昨天有 3 个成交。<sheet gid 1805763216> 告诉我，你有什么建议？我要做什么决定？」).
No PII printed (no names / emails / phones).
A) which tab gid 1805763216 is; its header.
B) every paid row dated ≥ 11/11 (that tab + Paid Student List): date · country (phone code) · paid-row UTM ·
   the buyer's Register rows since 10/29 carrying a (Webinarkit) UTM → campaign › ad set › ad (robust-UTM position).
C) cycle 11/5–11/11 per account (Meta spend / regs / CPL) and per position with cycle spend ≥ RM40:
   spend · regs · CPL · robust-UTM sales at that position since 10/29 · CPA (since 10/29 spend / sales)."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

GID = 1805763216
U0, C0, C1 = dt.date(2026, 10, 29), dt.date(2026, 11, 5), dt.date(2026, 11, 11)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人"), ("赚美金", "赚美金"),
       ("炒了五年", "炒了五年"), ("越认真盯盘", "越认真盯盘"), ("决定变少", "决定变少"), ("不适合你", "这条视频不适合你")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), cpa.norm(a or ""))
key = lambda c, s, a: (core(c), cpa.norm(s or ""), cre(a))
digits = lambda v: re.sub(r"\D", "", v or "")
em = lambda v: (v or "").strip().lower()
tel = lambda v: digits(v)[-8:]
cc = lambda v: "SG" if digits(v).startswith("65") else ("MY" if digits(v).startswith("60") or digits(v).startswith("01") else "?")

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
SID = s0.cpa.spreadsheet_id
meta = sc._svc.spreadsheets().get(spreadsheetId=SID, fields="sheets.properties(sheetId,title)").execute()
tabs = {p["properties"]["sheetId"]: p["properties"]["title"] for p in meta["sheets"]}
gtab = tabs.get(GID, "?")
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 链接分页 gid {GID} = «{gtab}» · sales_tab = «{s0.cpa.sales_tab}»")


def table(tab):
    v = sc.read_tab(SID, tab)
    hi = next((i for i, r in enumerate(v[:10]) if any(h in r for h in ("UTM Campaign", "Date", "Email"))), 0)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


hdr, grows = table(gtab)
print(f"  «{gtab}» 表头: {[h for h in hdr if h and not re.search('name|email|phone|mail|电话|名字', h, re.I)]}")
_, prows = table(s0.cpa.sales_tab)
_, regs = table("Register")

reg_by_person = defaultdict(list)
regs_by_key = defaultdict(set)
for r in regs:
    d = cpa.parse_date(r.get("Created date", ""))
    ids = tuple(k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k)
    for k in ids:
        reg_by_person[k].append(r)
    if d and d >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower() and ids:
        regs_by_key[key(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(ids)


def sales_since(rows, d0):
    out = []
    for p in rows:
        d = cpa.parse_date(p.get("Date", "") or p.get("Created date", "") or p.get("Timestamp", ""))
        if d and d >= d0:
            out.append((d, p))
    return out


print(f"\n== B) 成交（日期 ≥ 11/11）")
seen = set()
for label, rows in ((gtab, grows), (s0.cpa.sales_tab, prows)):
    ss = sales_since(rows, C1)
    print(f"  «{label}»: {len(ss)} 笔")
    for d, p in ss:
        ids = tuple(k for k in (em(p.get("Email")), tel(p.get("Phone Number"))) if k)
        dup = any(k in seen for k in ids)
        seen.update(ids)
        print(f"   · {d} · {cc(p.get('Phone Number'))}" + (" · (同一人，上面已列)" if dup else "")
              + f" · 成交行 UTM: {p.get('UTM Campaign') or '空'} › {p.get('UTM Ads Set') or '空'} › {p.get('UTM Ads Name') or '空'}")
        if dup:
            continue
        rr = []
        for k in ids:
            rr += [r for r in reg_by_person.get(k, []) if r not in rr]
        rr.sort(key=lambda r: cpa.parse_date(r.get("Created date", "")) or dt.date(2000, 1, 1))
        for r in rr:
            rd = cpa.parse_date(r.get("Created date", ""))
            ok = rd and rd >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower()
            print(f"        报名 {rd} · {r.get('Source') or '?'} · {'✅ UTM 可用' if ok else ('UTM 不可用(10/28前)' if rd and rd < U0 else 'UTM 空/非广告')}"
                  f" · {r.get('UTM Campaign') or '空'} › {r.get('UTM Ads Set') or '空'} › {r.get('UTM Ads Name') or '空'}")
        if not rr:
            print("        报名表找不到此人（电邮/电话都对不上）")

paid_all = sales_since(prows, U0) + [x for x in sales_since(grows, U0) if gtab != s0.cpa.sales_tab]
buyers = {k for _, p in paid_all for k in (em(p.get("Email")), tel(p.get("Phone Number"))) if k}
print(f"\n  10/29 起成交（两表合并去重前）{len(paid_all)} 笔 · 买家识别码 {len(buyers)}")

print("\n== C) 周期 11/5–11/11")
for label, cfg, ccode in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g, acct, tok = graph_client(s), s.meta.account_path, f"offsite_conversion.custom.{ccode}"
    rows = g._get_all(acct + "/insights", {"fields": "campaign_name,adset_name,ad_name,ad_id,spend,actions", "level": "ad",
                                            "limit": "1000", "time_range": tr(C0, C1)})
    rel = {r["ad_id"]: float(r.get("spend") or 0) for r in g._get_all(acct + "/insights", {
        "fields": "ad_id,spend", "level": "ad", "limit": "1000", "time_range": tr(U0, TODAY)})}
    tsp = sum(float(r.get("spend") or 0) for r in rows)
    trg = sum(extract_results(r.get("actions"), tok) for r in rows)
    print(f"  ######## {label}: RM{tsp:,.0f} · 报名 {trg:.0f} · CPL {tsp / trg if trg else 0:.0f}")
    for r in sorted(rows, key=lambda r: -float(r.get("spend") or 0)):
        sp = float(r.get("spend") or 0)
        if sp < 40:
            continue
        rg = extract_results(r.get("actions"), tok)
        ppl = regs_by_key.get(key(r["campaign_name"], r["adset_name"], r["ad_name"]), set())
        nb = sum(any(w in buyers for w in who) for who in ppl)
        rs = rel.get(r["ad_id"], 0.0)
        print(f"   {r['campaign_name'].replace('(Webinarkit) ', '').replace('STOCKBLOOM | ', '')} › {r['adset_name']} · {r['ad_name']} · ad {r['ad_id']}\n"
              f"        周期 RM{sp:,.0f} / {rg:.0f} 报名" + (f" · CPL {sp / rg:.0f}" if rg else "")
              + f" · 10/29起 RM{rs:,.0f} · UTM报名 {len(ppl)} → 原位成交 {nb}" + (f" · CPA RM{rs / nb:,.0f}" if nb else ""))
print("\nCYCLE REVIEW DONE (read-only)")
