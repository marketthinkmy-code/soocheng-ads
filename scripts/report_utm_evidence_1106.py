# -*- coding: utf-8 -*-
"""READ-ONLY: registrations since 10/29 (reliable UTM) per position, matched robustly — campaign names get their
«| 1-1-N |» ad-count segment edited over time and ad names were retitled (e.g. «Video：freestyle korea» vs «freestyle: korea»),
so key = (campaign core without the 1-x-y segment, ad set, creative keyword). Shows the raw UTM spellings, per-key
registrants and how many of them are in the Paid Student List (Date ≥ 10/29). No PII."""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

U0 = dt.date(2026, 10, 29)
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), (a or "?")[:20])
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
buyers = set()
for p in table(s.cpa.sales_tab):
    d = cpa.parse_date(p.get("Date", ""))
    if d and d >= U0:
        buyers |= {k for k in (em(p.get("Email")), tel(p.get("Phone Number"))) if k}
raw, people = Counter(), defaultdict(set)
total = 0
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < U0 or "webinarkit" not in (r.get("UTM Campaign") or "").lower():
        continue
    total += 1
    raw[(r.get("UTM Campaign", "")[:60], r.get("UTM Ads Name", "")[:30])] += 1
    who = tuple(k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k)
    people[(core(r.get("UTM Campaign")), cpa.norm(r.get("UTM Ads Set") or ""), cre(r.get("UTM Ads Name")))].add(who)
print(f"10/29 起带 (Webinarkit) UTM 的报名行 {total} 行")
print("\n原始 UTM 写法（campaign · ad，前 25）:")
for (c, a), n in raw.most_common(25):
    print(f"   {n:>3}  «{c}» · «{a}»")
print("\n按 位置(campaign 核心名 › ad set › 素材) 合并：报名人数 → 其中成交")
for key, ps in sorted(people.items(), key=lambda kv: -len(kv[1])):
    nb = sum(any(w in buyers for w in who) for who in ps)
    print(f"   {len(ps):>3} → {nb}   {key[0][:40]} › {key[1][:24]} › {key[2]}")
print("\nUTM EVIDENCE DONE (read-only)")
