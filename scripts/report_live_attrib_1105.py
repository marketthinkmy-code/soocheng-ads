# -*- coding: utf-8 -*-
"""READ-ONLY post-live attribution for the 11/4 Webinarkit live (first live with the fixed UTM). No PII printed.
Paid Student List rows dated ≥ 11/04: date · amount · phone country · UTM campaign › ad set › ad.
Each sale is matched to its EXACT position (campaign › ad set › ad) on MY 5.0 / SG; per matched position:
spend since 10/16 (the Webinarkit launch) → strict CPA. Also: per account totals, unmatched / blank-UTM sales,
and webinar_nov4 registrations by country for reg→sale rate."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

LIVE = dt.date(2026, 11, 4)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)
vals = sc.read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
hi = next(i for i, r in enumerate(vals[:8]) if "UTM Campaign" in r)
h = vals[hi]
digits = lambda v: re.sub(r"\D", "", v or "")
country = lambda p: "SG" if digits(p).startswith("65") or (len(digits(p)) == 8 and digits(p)[:1] in "689") else "MY"
rows = []
for r in vals[hi + 1:]:
    row = dict(zip(h, r))
    d = cpa.parse_date(row.get("Date", ""))
    if d and d >= LIVE:
        rows.append(row)
print(f"① Paid Student List · {LIVE} 起成交 {len(rows)} 笔")
pos = {}
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    st = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(st)
    for r in g._get_all(st.meta.account_path + "/insights", {"fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions", "level": "ad", "limit": "1000",
                                                             "time_range": json.dumps({"since": "2026-10-16", "until": TODAY.isoformat()})}):
        k = (_mkey(r["campaign_name"]), _mkey(r["adset_name"]), cpa.norm(r["ad_name"]))
        pos[k] = (label, r["campaign_name"], r["adset_name"], r["ad_name"], r["ad_id"], float(r.get("spend") or 0),
                  extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}"))
hits, kinds = defaultdict(list), Counter()
for row in rows:
    c, a_s, a = (row.get("UTM Campaign") or "").strip(), (row.get("UTM Ads Set") or "").strip(), (row.get("UTM Ads Name") or "").strip()
    k = (_mkey(c), _mkey(a_s), cpa.norm(a))
    amt = row.get("Purchase Amount", "")
    if k in pos:
        hits[k].append((row.get("Date", ""), amt, country(row.get("Phone Number"))))
        kinds["对上原位"] += 1
        tag = "✅ 原位"
    elif not c:
        kinds["UTM 空白"] += 1
        tag = "— 空白"
    else:
        kinds["UTM 有但对不上现有位置（旧 campaign/自然）"] += 1
        tag = "✗ 对不上"
    print(f"   {row.get('Date', '')[:12]:<12} {amt:<10} {country(row.get('Phone Number'))} · {tag} · «{c[:55]}» › {a_s[:30]} › {a[:34]}")
print("   ", dict(kinds))
print("\n② 原位 CPA（花费 = 该位置 10/16 起累计）")
acct = Counter()
for k, lst in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    label, cn, sn, an, aid, sp, rg = pos[k]
    acct[label] += len(lst)
    print(f"   {label} · {cn} › {sn} · {an} · ad {aid} · 花费 RM{sp:,.0f} · 报名 {rg:.0f} · 成交 {len(lst)} · CPA RM{sp / len(lst):,.0f}")
print("   各账户原位成交:", dict(acct))
reg = sc.read_tab(s.cpa.spreadsheet_id, "Register")
rh = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r)
rc = Counter(country(dict(zip(reg[rh], r)).get("Phone Number")) for r in reg[rh + 1:] if "nov4" in (dict(zip(reg[rh], r)).get("Source") or "").lower())
sc_ = Counter(country(r.get("Phone Number")) for r in rows)
print(f"\n③ webinar_nov4 报名 {dict(rc)} → 成交 {dict(sc_)} · 转成交率 " + " · ".join(f"{k} {100 * sc_[k] / rc[k]:.1f}%" for k in rc if rc[k]))
print("\nLIVE ATTRIB DONE (read-only)")
