# -*- coding: utf-8 -*-
"""READ-ONLY 10/29 recap of the 10/28 Webinarkit live. No PII printed (emails / phones only used for the join in-run).
1) Paid Student List rows dated ≥ 10/28 (+ any with Source containing oct28): date · amount · channel · source · sheet UTM,
   and the buyer's Register row UTM (campaign › ad set › ad), found by email then phone.
2) Register: webinar_oct28 registrations by day × (SG UTM / MY UTM / no UTM) × phone country.
3) Ad spend + Meta registrations for the oct28 cycle (10/22 → 10/28) per account."""
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

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)
paid = sc.read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
reg = sc.read_tab(s.cpa.spreadsheet_id, "Register")
ph_i = next(i for i, r in enumerate(paid[:8]) if "UTM Campaign" in r); ph = paid[ph_i]
rh_i = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r); rh = reg[rh_i]
em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
idx = {}
for r in reg[rh_i + 1:]:
    row = dict(zip(rh, r))
    for k in (em(row.get("Email")), tel(row.get("Phone Number"))):
        if k:
            idx.setdefault(k, []).append(row)

print("① 10/28 起的成交（不印个资）:")
n = 0
for r in paid[ph_i + 1:]:
    row = dict(zip(ph, r))
    d = cpa.parse_date(row.get("Date", ""))
    if not ((d and d >= dt.date(2026, 10, 28)) or "oct28" in (row.get("Source") or "").lower()):
        continue
    n += 1
    hits = idx.get(em(row.get("Email"))) or idx.get(tel(row.get("Phone Number"))) or []
    h = hits[-1] if hits else {}
    print(f"   {d} · {row.get('Purchase Amount', '') or '(金额空)'} · {row.get('Channel', '')} · {row.get('Source', '')} · "
          f"表内 UTM «{row.get('UTM Campaign', '')[:45]}» · 报名 UTM «{h.get('UTM Campaign', '')[:45]}» › {h.get('UTM Ads Set', '')[:28]} › {h.get('UTM Ads Name', '')[:30]} · 报名日 {h.get('Created date', '')[:10]}")
print(f"   共 {n} 笔")

print("\n② Register · webinar_oct28 报名:")
cnt = Counter()
for r in reg[rh_i + 1:]:
    row = dict(zip(rh, r))
    if "oct28" not in (row.get("Source") or "").lower():
        continue
    u = (row.get("UTM Campaign") or "").strip().lower()
    d = re.sub(r"\D", "", row.get("Phone Number") or "")
    ccode = "+65" if (d.startswith("65") and len(d) == 10) or (len(d) == 8 and d[:1] in "689") else "+60"
    cnt[("SG UTM" if "[sg]" in u else ("MY UTM" if u else "无UTM"), ccode)] += 1
for k, v in sorted(cnt.items()):
    print(f"   {k[0]:<7} {k[1]}  {v}")
print(f"   合计 {sum(cnt.values())}")

print("\n③ 10/22→10/28 广告花费 / Meta 报名:")
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    st = load_settings(REPO_ROOT / "config" / cfg)
    r = graph_client(st)._get_all(st.meta.account_path + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": "2026-10-22", "until": "2026-10-28"})})
    r = r[0] if r else {}
    sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}")
    print(f"   {label}: RM{sp:,.0f} · 报名 {rg:.0f} · CPL {sp / rg if rg else 0:.0f}")
print("\nLIVE RECAP 1029 DONE (read-only)")
