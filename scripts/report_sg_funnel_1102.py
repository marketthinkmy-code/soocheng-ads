# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/2「新加坡的帳戶都很貴，告訴我 next action plan」) — where does SG lose vs MY?
1) Funnel 10/29→today per account and per live SG campaign: spend · CPM · link CTR · cost/link click · landing-page views ·
   LPV→报名 % · CPL · frequency.
2) Value of an SG lead: Register vs Paid Student List by phone country (+65 vs other), all-time and since 2026-09-01. No PII."""
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

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
TR = json.dumps({"since": "2026-10-29", "until": TODAY})
F = "campaign_name,spend,impressions,reach,frequency,cpm,inline_link_clicks,inline_link_click_ctr,actions"


def act(r, t):
    return sum(float(a["value"]) for a in r.get("actions") or [] if a["action_type"] == t)


def line(lbl, r, tok):
    sp, imp = float(r.get("spend") or 0), int(r.get("impressions") or 0)
    lc, lpv, rg = float(r.get("inline_link_clicks") or 0), act(r, "landing_page_view"), extract_results(r.get("actions"), tok)
    print(f"   {lbl[:58]:<58} RM{sp:>6.0f} · CPM {float(r.get('cpm') or 0):>4.0f} · freq {float(r.get('frequency') or 0):.1f} · "
          f"CTR {float(r.get('inline_link_click_ctr') or 0):.2f}% · RM{sp / lc if lc else 0:.2f}/click · LPV {lpv:.0f} · "
          f"LPV→报名 {100 * rg / lpv if lpv else 0:.0f}% · 报名 {rg:.0f} · CPL {sp / rg if rg else 0:.0f}")


print(f"① 漏斗 10/29 → {TODAY}")
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{cc}"
    acc = g._get_all(s.meta.account_path + "/insights", {"fields": F.replace("campaign_name,", ""), "time_range": TR})
    line(f"{label} 全账户", acc[0] if acc else {}, tok)
    for r in g._get_all(s.meta.account_path + "/insights", {"fields": F, "level": "campaign", "time_range": TR, "limit": "100"}):
        if float(r.get("spend") or 0) >= 50:
            line("  " + r["campaign_name"].replace("(Webinarkit) ", ""), r, tok)

print("\n② 一个报名值多少：Register vs Paid（按电话国码）")
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)
digits = lambda v: re.sub(r"\D", "", v or "")


def country(p):
    d = digits(p)
    if d.startswith("65") or (len(d) == 8 and d[:1] in "689"):
        return "SG"
    return "MY" if d.startswith("60") or d.startswith("01") else "其他"


def rows(tab):
    v = sc.read_tab(s.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if any("UTM" in c for c in r))
    return [dict(zip(v[hi], r)) for r in v[hi + 1:] if any(x.strip() for x in r)]


reg, paid = rows("Register"), rows(s.cpa.sales_tab)
dcol_r = next(c for c in reg[0] if "created" in c.lower())
since = dt.date(2026, 9, 1)
for lbl, flt in (("全部历史", lambda d: True), ("2026-09-01 起", lambda d: d is not None and d >= since)):
    rc = Counter(country(r.get("Phone Number")) for r in reg if flt(cpa.parse_date(r.get(dcol_r, ""))))
    pc = Counter(country(r.get("Phone Number")) for r in paid if flt(cpa.parse_date(r.get("Date", ""))))
    print(f"   {lbl}: " + " · ".join(f"{k} 报名 {rc[k]} → 成交 {pc[k]} = {100 * pc[k] / rc[k] if rc[k] else 0:.1f}%" for k in ("MY", "SG")))
print("\nSG FUNNEL DONE (read-only)")
