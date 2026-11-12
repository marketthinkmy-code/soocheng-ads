# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/12 Thursday review). Per webinar cycle: Meta spend / regs (Thu→Wed before the live, MY 5.0 + SG)
vs sales dated live-day → next Tuesday (Paid Student List rows that carry an email or phone; blank rows skipped).
Country by phone code. No PII printed."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

LIVES = [dt.date(2026, 10, 14), dt.date(2026, 10, 21), dt.date(2026, 10, 28), dt.date(2026, 11, 4), dt.date(2026, 11, 11)]
digits = lambda v: re.sub(r"\D", "", v or "")
cc = lambda v: "SG" if digits(v).startswith("65") else ("MY" if digits(v).startswith(("60", "01")) else "?")
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
hi = next(i for i, r in enumerate(v[:10]) if "UTM Campaign" in r)
paid = [dict(zip(v[hi], r)) for r in v[hi + 1:]]
paid = [(cpa.parse_date(p.get("Date", "")), p) for p in paid if (p.get("Email") or "").strip() or digits(p.get("Phone Number"))]
paid = [(d, p) for d, p in paid if d]

acc = {}
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    acc[label] = (graph_client(s), s.meta.account_path, f"offsite_conversion.custom.{code}")

print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 成交 = 直播日→下周二（空行不算）· 花费 = 直播前 周四→周三")
for live in LIVES:
    a, b = live - dt.timedelta(days=6), live
    s_to = min(live + dt.timedelta(days=6), (dt.datetime.utcnow() + dt.timedelta(hours=8)).date())
    sales = [p for d, p in paid if live <= d <= live + dt.timedelta(days=6)]
    byc = Counter(cc(p.get("Phone Number")) for p in sales)
    line = []
    tot_sp = tot_rg = 0.0
    for label, (g, acct, tok) in acc.items():
        rows = g._get_all(acct + "/insights", {"fields": "spend,actions", "time_range": tr(a, b)})
        sp = sum(float(r.get("spend") or 0) for r in rows)
        rg = sum(extract_results(r.get("actions"), tok) for r in rows)
        tot_sp += sp; tot_rg += rg
        n = byc.get(label, 0)
        line.append(f"{label} RM{sp:,.0f}/{rg:.0f}报名 · 成交 {n}" + (f" · 每学员 RM{sp / n:,.0f}" if n else ""))
    n = len(sales)
    print(f"  直播 {live:%m/%d}（花费 {a:%m/%d}–{b:%m/%d}，成交算到 {s_to:%m/%d}）: 合计 RM{tot_sp:,.0f} / {tot_rg:.0f} 报名 · 成交 {n}"
          f" (MY {byc.get('MY', 0)} · SG {byc.get('SG', 0)} · ? {byc.get('?', 0)})"
          + (f" · 每学员 RM{tot_sp / n:,.0f} · 报名→成交 {n / tot_rg:.1%}" if n and tot_rg else ""))
    print("      " + " | ".join(line))
print("\nCYCLE TREND DONE (read-only)")
