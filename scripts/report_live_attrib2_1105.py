# -*- coding: utf-8 -*-
"""READ-ONLY: the 11/4 live's sales carry no UTM in the Paid Student List, so join each buyer (email, then phone) to
their webinar_nov4 Register row(s) — the Register UTM is this registration's UTM since the 10/29 fix — and attribute
to the exact campaign › ad set › ad; strict CPA = that position's spend since 10/16 ÷ its sales. No PII printed."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

LIVE = dt.date(2026, 11, 4)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
digits = lambda v: re.sub(r"\D", "", v or "")
country = lambda p: "SG" if digits(p).startswith("65") or (len(digits(p)) == 8 and digits(p)[:1] in "689") else "MY"
paid = [r for r in table(s.cpa.sales_tab) if (cpa.parse_date(r.get("Date", "")) or dt.date(2000, 1, 1)) >= LIVE]
reg = table("Register")
idx = defaultdict(list)
for r in reg:
    for k in (em(r.get("Email")), tel(r.get("Phone Number"))):
        if k:
            idx[k].append(r)
pos = {}
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    st = load_settings(REPO_ROOT / "config" / cfg)
    for r in graph_client(st)._get_all(st.meta.account_path + "/insights", {"fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions", "level": "ad", "limit": "1000",
                                                                            "time_range": json.dumps({"since": "2026-10-16", "until": TODAY.isoformat()})}):
        pos[(_mkey(r["campaign_name"]), _mkey(r["adset_name"]), cpa.norm(r["ad_name"]))] = (
            label, r["campaign_name"], r["adset_name"], r["ad_name"], r["ad_id"], float(r.get("spend") or 0),
            extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}"))
print(f"11/4 起成交 {len(paid)} 笔 → 对回 webinar_nov4 报名行的 UTM：")
hits = defaultdict(int)
for i, p in enumerate(paid, 1):
    rows = idx.get(em(p.get("Email"))) or idx.get(tel(p.get("Phone Number"))) or []
    nov4 = [r for r in rows if "nov4" in (r.get("Source") or "").lower()]
    r = (nov4 or rows or [{}])[-1]
    c, a_s, a = (r.get("UTM Campaign") or "").strip(), (r.get("UTM Ads Set") or "").strip(), (r.get("UTM Ads Name") or "").strip()
    k = (_mkey(c), _mkey(a_s), cpa.norm(a))
    tag = "✅ 原位" if k in pos else ("— 报名 UTM 空白" if not c else "✗ 旧 UTM/对不上")
    if k in pos:
        hits[k] += 1
    print(f"  #{i} {p.get('Purchase Amount', '')} · {country(p.get('Phone Number'))} · 报名行 {'nov4' if nov4 else ('其他场次' if rows else '找不到')} "
          f"{(r.get('Created date') or '')[:10]} · {tag} · «{c[:50]}» › {a_s[:28]} › {a[:32]}")
print("\n原位 CPA（该位置 10/16 起累计花费 ÷ 原位成交）:")
for k, n in sorted(hits.items(), key=lambda kv: -kv[1]):
    label, cn, sn, an, aid, sp, rg = pos[k]
    print(f"  {label} · {cn} › {sn} · {an} · ad {aid} · 花费 RM{sp:,.0f} · 报名 {rg:.0f} · 成交 {n} · CPA RM{sp / n:,.0f}")
print("\nLIVE ATTRIB2 DONE (read-only)")
