# -*- coding: utf-8 -*-
"""READ-ONLY (11/28 morning watch: new Paid rows this cycle). For each Paid row dated 11/26 or later that has
contact info: the Paid row's own Source / UTM columns, then EVERY Register-tab registration of that buyer (matched by email/phone):
created date + non-PII columns (Source/webinar, UTM campaign / ad set / ad / placement). Never prints names, emails, phones."""
from __future__ import annotations

import datetime as dt
import re

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]], hi


rh, reg, _ = table("Register", "Email")
ph, paid, phi = table(s0.cpa.sales_tab, "UTM Campaign")
PII = re.compile(r"name|名字|姓名|email|e-mail|phone|电话|whatsapp|contact|address|地址|remark|备注|experience|ip", re.I)
rcols = [h for h in rh if h and not PII.search(h)]
print("报名表非个资栏位：", " | ".join(rcols))
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
by = {}
for i, r in enumerate(reg):
    for k in who(r):
        by.setdefault(k, set()).add(i)
for n, p in enumerate(paid, start=phi + 2):
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < dt.date(2026, 11, 26):
        continue
    if not who(p):
        print(f"\n== Paid 第 {n} 行 · {d:%m/%d} · Channel={p.get('Channel', '')} · 没有电邮 / 电话 = 空白行，不算成交")
        continue
    print(f"\n== Paid 第 {n} 行 · {d:%m/%d} · Channel={p.get('Channel', '')} · Source={p.get('Source', '')} · "
          f"Paid 行自带 UTM：{p.get('UTM Campaign', '') or '（空）'} › {p.get('UTM Ads Set', '') or '（空）'} · {p.get('UTM Ads Name', '') or '（空）'}")
    rows = sorted({i for k in who(p) for i in by.get(k, ())}, key=lambda i: (cpa.parse_date(reg[i].get("Created date", "")) or dt.date(1900, 1, 1), i))
    print(f"   报名表里这位买家共 {len(rows)} 次报名：")
    for i in rows:
        r = reg[i]
        print("    · " + " · ".join(f"{h}={(r.get(h) or '').strip()}" for h in rcols if (r.get(h) or "").strip()))
print("\nBUYER REGS DONE (read-only)")
