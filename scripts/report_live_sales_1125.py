# -*- coding: utf-8 -*-
"""READ-ONLY (11/25 22:3x, after the 11/25 live). Every Paid row dated ≥ 11/19: date, non-PII columns (header names that
are not name/email/phone), has-contact y/n, and its strict position (buyer's last ad-UTM registration on/before the
purchase → campaign › ad set · ad) looked up in MY 5.0 AND SG (insights since 10/29, deleted ads included). No PII."""
from __future__ import annotations

import datetime as dt
import json
import re

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
U0, C0 = dt.date(2026, 10, 29), dt.date(2026, 11, 19)
loose = lambda a: re.sub(r"[\W_]+", "", re.sub(r"^(?:video|image)\s*\d*\s*[：:]\s*", "", cpa.norm(a)))
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


rh, reg = table("Register", "Email")
ph, paid = table(s0.cpa.sales_tab, "UTM Campaign")
ad_col = next((h for h in rh if cpa._hkey(h) in ("utmadsname", "utmadname")), "UTM Ads Name")
PII = re.compile(r"name|email|e-mail|phone|电话|姓名|whatsapp|contact|ic|address|地址", re.I)
safe_cols = [h for h in ph if h and not PII.search(h)]
print("Paid 表非个资栏位：", " | ".join(safe_cols))
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
lix = {}
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for i in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": json.dumps(
            {"since": U0.isoformat(), "until": TODAY.isoformat()}), "fields": "ad_id,ad_name,adset_name,campaign_name", "limit": "500"}):
        lix[(_mkey(i["campaign_name"]), _mkey(i["adset_name"]), loose(i["ad_name"]))] = \
            f"{label} · {i['campaign_name']} › {i['adset_name']} · {i['ad_name']} · ad {i['ad_id']}"
find = lambda r: lix.get((_mkey(cpa.norm(r.get("UTM Campaign"))), _mkey(cpa.norm(r.get("UTM Ads Set"))), loose(r.get(ad_col))))
regs_by = {}
for i, r in enumerate(reg):
    d = cpa.parse_date(r.get("Created date", ""))
    if d:
        for k in who(r):
            regs_by.setdefault(k, []).append((d, i, r))
rows = [(cpa.parse_date(p.get("Date", "")), n, p) for n, p in enumerate(paid)]
rows = sorted([x for x in rows if x[0] and x[0] >= C0], key=lambda x: (x[0], x[1]))
print(f"\nPaid 表 {C0:%m/%d} 起 {len(rows)} 行（按日期）")
for d, n, p in rows:
    keys = who(p)
    extra = " · ".join(f"{h}={p.get(h, '').strip()}" for h in safe_cols if h not in ("Date",) and (p.get(h) or "").strip())
    if not keys:
        print(f"  {d:%m/%d} · 无电邮电话 · {extra}")
        continue
    h = sorted({(dd, i): r for k in keys for dd, i, r in regs_by.get(k, []) if U0 <= dd <= d and (r.get("UTM Campaign") or "").strip()}.items())
    allr = sorted({(dd, i) for k in keys for dd, i, r in regs_by.get(k, [])})
    first = allr[0][0] if allr else None
    if h:
        (rd, _), r = h[-1]
        pos = find(r) or f"认不到位置（UTM campaign = {r.get('UTM Campaign')}）"
        print(f"  {d:%m/%d} · 最后一次带 UTM 报名 {rd:%m/%d} → {pos} · 首次报名 {first:%m/%d} · {extra}")
    else:
        print(f"  {d:%m/%d} · 10/29 起没有带 UTM 的报名（首次报名 {first:%m/%d}）· {extra}" if first else f"  {d:%m/%d} · 报名表找不到此人 · {extra}")
print("\nLIVE SALES DONE (read-only)")
