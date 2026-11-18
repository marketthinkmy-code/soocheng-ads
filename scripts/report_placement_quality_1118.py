# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/18 fake-registration question). Register rows since 10/29 grouped by UTM Placement:
registrations, suspected-bot S1 rows (Experience = first name ×2), and buyers (Paid Student List email/phone match). No PII printed."""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

D0 = dt.date(2026, 10, 29)
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
buyers = set()
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if d and d >= D0:
        buyers |= {k for k in ((p.get("Email") or "").strip().lower(), digits(p.get("Phone Number"))[-8:]) if k}


def s1(r):
    fw = ((r.get("Name") or "").split() or [""])[0]
    return bool(fw) and (r.get("Experience") or "").strip() == fw * 2


reg, bot, buy = Counter(), Counter(), Counter()
bot_day = Counter()
for r in regs:
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < D0:
        continue
    pl = (r.get("UTM Placement") or "空").strip() or "空"
    reg[pl] += 1
    if s1(r):
        bot[pl] += 1
        bot_day[(d, pl)] += 1
    ids = {k for k in ((r.get("Email") or "").strip().lower(), digits(r.get("Phone Number"))[-8:]) if k}
    if ids & buyers:
        buy[pl] += 1
print(f"10/29 起 Register 按 UTM Placement（报名 · 疑似机器人 S1 · 买家）· 买家识别码 {len(buyers)}")
for pl, n in reg.most_common(30):
    print(f"   {pl[:40]:40s} 报名 {n:4d} · S1 {bot[pl]:3d} · 买家 {buy[pl]:3d}" + (f" · 报名→成交 {buy[pl] / n:.1%}" if n else ""))
print("S1 按日期 × 版位:")
for (d, pl), n in sorted(bot_day.items()):
    print(f"   {d} · {pl} · {n}")
print("PLACEMENT QUALITY 1118 DONE (read-only)")
