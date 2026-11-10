# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/10「看回所有 paid student list 记录，分开新加坡 & 马来西亚成交的统计，list down top 3 有成交记录的 ad set」).
Every row of the Paid Student List → country by phone (+65 / 8-digit 6/8/9 = SG, else MY) → grouped by UTM ad set (normalised:
case/space/🌟/🚫 stripped). Prints all ad sets with ≥1 sale per country, with the campaigns they came from, first/last sale date,
and how many rows have no ad-set UTM. No PII printed."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
rows = [dict(zip(v[hi], r)) for r in v[hi + 1:]]
digits = lambda x: re.sub(r"\D", "", x or "")
country = lambda p: "SG" if digits(p).startswith("65") or (len(digits(p)) == 8 and digits(p)[:1] in "689") else "MY"
print(f"Paid Student List 表头: {[h for h in v[hi] if h][:14]}")
by = {"SG": defaultdict(list), "MY": defaultdict(list)}
blank = defaultdict(int)
total = defaultdict(int)
for r in rows:
    if not any((r.get(k) or "").strip() for k in ("Phone Number", "Email", "UTM Campaign")):
        continue
    c = country(r.get("Phone Number"))
    total[c] += 1
    st = cpa.norm(r.get("UTM Ads Set") or "")
    d = cpa.parse_date(r.get("Date", ""))
    if not st:
        blank[c] += 1
        continue
    by[c][st].append((d, cpa.norm(r.get("UTM Campaign") or ""), cpa.norm(r.get("UTM Ads Name") or "")))
for c in ("SG", "MY"):
    print(f"\n################ {c} · 成交 {total[c]} 笔 · 有 ad set UTM {total[c] - blank[c]} · 没有 ad set UTM {blank[c]}")
    for st, lst in sorted(by[c].items(), key=lambda kv: -len(kv[1])):
        ds = sorted(d for d, *_ in lst if d)
        recent = sum(1 for d in ds if d >= dt.date(2026, 9, 1))
        camps = defaultdict(int)
        for _, cp, _ in lst:
            camps[cp] += 1
        ads = defaultdict(int)
        for *_, an in lst:
            ads[an] += 1
        print(f"  {len(lst):>3} 笔 · «{st}» · {ds[0] if ds else '?'} → {ds[-1] if ds else '?'} · 9/1 起 {recent} 笔")
        for cp, n in sorted(camps.items(), key=lambda kv: -kv[1])[:4]:
            print(f"        campaign {n} 笔 «{cp[:70]}»")
        print("        ad: " + " · ".join(f"{a[:24]}×{n}" for a, n in sorted(ads.items(), key=lambda kv: -kv[1])[:5]))
print("\nPAID ADSET DONE (read-only)")
