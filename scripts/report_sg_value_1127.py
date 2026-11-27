# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/27「你会建议我不跑 SG 吗」). Per webinar cycle since 10/29, MY 5.0 vs SG:
cycle spend (Meta, Thu → Wed) · real registrations for that webinar (Register Source = that webinar, Webinarkit UTM,
S1 bots off; account by [SG] in the UTM campaign) · sales by WK's 11/25 rule (a Paid row counts for an account only if the
buyer's registration FOR THAT WEBINAR carries that account's Webinarkit UTM; no-UTM re-registrations = 旧名单, credited to
no account; Paid rows with no email/phone = blank placeholders) · cost per student · reg → sale %. No PII printed."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CYCLES = [("nov4", dt.date(2026, 10, 29), dt.date(2026, 11, 4)), ("nov11", dt.date(2026, 11, 5), dt.date(2026, 11, 11)),
          ("nov18", dt.date(2026, 11, 12), dt.date(2026, 11, 18)), ("nov25", dt.date(2026, 11, 19), dt.date(2026, 11, 25))]
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
label = lambda v: (re.search(r"webinar_([a-z]+\d+)", (v or "").lower()) or [None, ""])[1]
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


reg = table("Register", "Email")
paid = table(s0.cpa.sales_tab, "UTM Campaign")
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
bot = lambda r: cpa.is_bot_registration(r.get("Name", ""), r.get("Experience", ""))
acct_of = lambda u: ("SG" if "[sg]" in u.lower() else "MY") if "webinarkit" in (u or "").lower() else None

print("Register Source 标签（本表 10/29 起）:", dict(Counter(label(r.get("Source")) for r in reg
      if (cpa.parse_date(r.get("Created date", "")) or dt.date(2000, 1, 1)) >= CYCLES[0][1])))
spend = defaultdict(float)
for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for w, a, b in CYCLES:
        for r in g._get_all(s.meta.account_path + "/insights", {"level": "account", "fields": "spend", "time_range": tr(a, b)}):
            spend[(lab, w)] += float(r.get("spend") or 0)

regs = Counter()
reg_by = defaultdict(list)                     # (contact key, webinar label) -> registrations for that webinar
for r in reg:
    w = label(r.get("Source"))
    if w not in {c[0] for c in CYCLES} or bot(r):
        continue
    a = acct_of(r.get("UTM Campaign"))
    if a:
        regs[(a, w)] += 1
    for k in who(r):
        reg_by[(k, w)].append(a)

sales, other = Counter(), Counter()
for p in paid:
    w = label(p.get("Source"))
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < CYCLES[0][1]:
        continue
    if not who(p):
        other["空白行（无电邮电话）"] += 1
        continue
    if w not in {c[0] for c in CYCLES}:
        other[f"Source 不是这四场（{w or '空'}）"] += 1
        continue
    accts = {a for k in who(p) for a in reg_by.get((k, w), [])}
    hit = [a for a in ("SG", "MY") if a in accts]
    if hit:
        sales[(hit[0], w)] += 1
    elif accts or any((k, w) in reg_by for k in who(p)):
        other[f"{w} 旧名单无 UTM 重报"] += 1
    else:
        other[f"{w} 这一场没有报名记录"] += 1

print("\n场次      | 账户 | 花费    | 真报名 | 真 CPL | 成交 | 每学员成本 | 报名→成交")
tot = defaultdict(lambda: [0.0, 0, 0])
for w, a, b in CYCLES:
    for lab in ("MY", "SG"):
        sp, rg, sl = spend[(lab, w)], regs[(lab, w)], sales[(lab, w)]
        t = tot[lab]; t[0] += sp; t[1] += rg; t[2] += sl
        print(f"{w:<9} | {lab}   | RM{sp:6.0f} | {rg:5d} | {('RM%.0f' % (sp / rg)) if rg else '—':>6} | {sl:3d} |"
              f" {('RM%.0f' % (sp / sl)) if sl else '—':>9} | {('%.1f%%' % (sl / rg * 100)) if rg else '—'}")
for lab in ("MY", "SG"):
    sp, rg, sl = tot[lab]
    print(f"合计 4 场 | {lab}   | RM{sp:6.0f} | {rg:5d} | {('RM%.0f' % (sp / rg)) if rg else '—':>6} | {sl:3d} |"
          f" {('RM%.0f' % (sp / sl)) if sl else '—':>9} | {('%.1f%%' % (sl / rg * 100)) if rg else '—'}")
print("\n其它 Paid 行（不算任何账户）:", dict(other))
print("\nSG VALUE 1127 DONE (read-only)")
