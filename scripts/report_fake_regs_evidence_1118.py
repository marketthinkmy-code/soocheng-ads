# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/18「你怎么知道这个是 fake sign up from bots?」). Evidence counts for the S1 rows
(Experience == first name ×2) vs normal rows — NO names / emails / phones printed."""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

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
fw = lambda r: ((r.get("Name") or "").split() or [""])[0]
is_s1 = lambda r: bool(fw(r)) and (r.get("Experience") or "").strip() == fw(r) * 2
name_in_email = lambda r: any(t.lower() in (r.get("Email") or "").split("@")[0].lower() for t in re.findall(r"[A-Za-z]{3,}", r.get("Name") or ""))
ph = lambda r: digits(r.get("Phone Number"))[-8:]
em = lambda r: (r.get("Email") or "").strip().lower()

all_dated = [(cpa.parse_date(r.get("Created date", "")), r) for r in regs]
s1 = [r for d, r in all_dated if is_s1(r)]
d0 = dt.date(2026, 10, 29)
normal = [r for d, r in all_dated if d and d >= d0 and not is_s1(r)]
print(f"S1 共 {len(s1)} 行（全表，所有日期）· 日期分布 {Counter(str(cpa.parse_date(r.get('Created date', ''))) for r in s1)}")
print(f"整张表历来「经验栏 = 名字打两次」的行数：{sum(is_s1(r) for _, r in all_dated)}（总行数 {len(regs)}）")
print(f"\n1) 电邮里有没有名字：S1 {sum(name_in_email(r) for r in s1)}/{len(s1)} · 10/29 起正常报名 {sum(name_in_email(r) for r in normal)}/{len(normal)}")
print(f"2) 电邮网域：S1 {Counter(em(r).split('@')[-1] for r in s1).most_common(5)}")
print(f"   正常报名 {Counter(em(r).split('@')[-1] for r in normal).most_common(5)}")
pc = Counter(ph(r) for r in s1)
print(f"3) 电话：S1 {len(s1)} 行用了 {len(pc)} 个不同号码；重复的号码 {sum(1 for v in pc.values() if v > 1)} 个")
ec = Counter(em(r) for r in s1)
print(f"   电邮：{len(ec)} 个不同电邮；重复 {sum(1 for v in ec.values() if v > 1)} 个")
before = {k for d, r in all_dated if d and d < dt.date(2026, 11, 11) for k in (ph(r), em(r)) if k}
print(f"4) 以前报名过（11/11 之前出现过同电话或电邮）：S1 {sum(1 for r in s1 if ph(r) in before or em(r) in before)}/{len(s1)}"
      f" · 对照：11/12–11/18 正常报名 {sum(1 for d, r in all_dated if d and dt.date(2026, 11, 12) <= d <= dt.date(2026, 11, 18) and not is_s1(r) and (ph(r) in before or em(r) in before))}"
      f"/{sum(1 for d, r in all_dated if d and dt.date(2026, 11, 12) <= d <= dt.date(2026, 11, 18) and not is_s1(r))}")
buyers = {k for p in paid for k in (em(p), ph(p)) if k}
print(f"5) S1 里有没有付费学员：{sum(1 for r in s1 if ph(r) in buyers or em(r) in buyers)}")
print(f"6) 电话国码：S1 {Counter('SG' if digits(r.get('Phone Number')).startswith('65') else 'MY' if digits(r.get('Phone Number')).startswith(('60', '01')) else '?' for r in s1)}")
print(f"7) 有没有时间（不只日期）栏位可以看提交时间：表头 {[h for h in regs[0].keys() if re.search('time|date|时间', h, re.I)]}")
print("EVIDENCE 1118 DONE (read-only)")
