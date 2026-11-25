# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/25「还有什么广告要开的？之前跑到成绩不错的，都开」). MY 5.0 + SG, every ad position since 10/29:
spend (Meta) · real regs (Register UTM, S1 bots off, strict campaign › ad set › ad) · real CPL · sales by the owner's 11/25 rule
(the buyer's registration FOR THAT WEBINAR — Paid Source = Register Source — must carry the ad's UTM; no-UTM re-registrations
count for no ad) · the monitor's OWN 60-day CPA (build_cpa_context + position_sales) so an instant CPA hard stop is visible ·
status of all 3 layers · banned / rejected / Webinarkit flags. Lists positions with ≥1 sale, or spend ≥ RM150 at real CPL ≤ the
account line. No writes, no PII."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, build_cpa_context, position_sales
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
U0 = dt.date(2026, 10, 29)
loose = lambda a: re.sub(r"[\W_]+", "", re.sub(r"^(?:video|image)\s*\d*\s*[：:]\s*", "", cpa.norm(a)))
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


rh, reg = table("Register", "Email")
_, paid = table(s0.cpa.sales_tab, "UTM Campaign")
ad_col = next((h for h in rh if cpa._hkey(h) in ("utmadsname", "utmadname")), "UTM Ads Name")
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
bot = lambda r: cpa.is_bot_registration(r.get("Name", ""), r.get("Experience", ""))
key_of = lambda r: (_mkey(cpa.norm(r.get("UTM Campaign"))), _mkey(cpa.norm(r.get("UTM Ads Set"))), loose(r.get(ad_col)))
src = lambda x: (x or "").strip().lower()

pos, lix = {}, {}
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ctx = build_cpa_context(g, s, TODAY)
    sold60, spend60 = ctx[0], ctx[2]
    buyers = ctx[3] if len(ctx) == 4 else None
    ins = g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": json.dumps(
        {"since": U0.isoformat(), "until": TODAY.isoformat()}), "fields": "ad_id,ad_name,adset_name,campaign_name,spend", "limit": "500"})
    live = {a["id"]: a for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,"
                                                                     "adset{name,status},campaign{name,status}", "limit": "500"})}
    line = s.kpi.cpl_threshold_myr
    for i in ins:
        a = live.get(i["ad_id"]) or dict(id=i["ad_id"], name=i["ad_name"], status="DELETED", effective_status="DELETED",
                                          adset=dict(name=i["adset_name"], status="—"), campaign=dict(name=i["campaign_name"], status="—"))
        n60 = position_sales(buyers, sold60, _mkey(a["campaign"]["name"]), a["adset"]["name"], a["name"])
        s60 = spend60.get(a["id"], 0.0)
        pos[a["id"]] = dict(acct=label, a=a, sp=float(i.get("spend") or 0), real=0, sales=[], line=line, n60=n60, s60=s60,
                            hard=s.cpa.hard_stop_myr,
                            banned=compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"])
        lix[(_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), loose(a["name"]))] = a["id"]

regs_by = defaultdict(list)
for i, r in enumerate(reg):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d:
        continue
    for k in who(r):
        regs_by[k].append((d, i, r))
    if d >= U0 and (r.get("UTM Campaign") or "").strip() and not bot(r):
        aid = lix.get(key_of(r))
        if aid:
            pos[aid]["real"] += 1
no_utm = 0
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < U0 or not who(p):
        continue
    mine = sorted({(dd, i): r for k in who(p) for dd, i, r in regs_by.get(k, []) if dd <= d}.items())
    if not mine:
        continue
    same = [r for (_dd, _i), r in mine if src(p.get("Source")) and src(r.get("Source")) == src(p.get("Source"))]
    r = same[-1] if same else mine[-1][1]          # the registration for THIS webinar (else the latest before purchase)
    aid = lix.get(key_of(r)) if (r.get("UTM Campaign") or "").strip() else None
    if aid:
        pos[aid]["sales"].append(d)
    else:
        no_utm += 1

print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 10/29 起 · 真 = 报名表去机器人 · 单 = 这一场的报名带该 ad UTM（owner 11/25 规则）"
      f" · 60天 = monitor 自己的 CPA 口径")
print(f"Paid 10/29 起有电邮电话、但这一场报名没带 UTM（旧名单重报，不算任何 ad）：{no_utm} 笔")
for acct in ("MY", "SG"):
    rows = [p for p in pos.values() if p["acct"] == acct and not p["banned"] and p["a"]["status"] != "DELETED"
            and (p["sales"] or (p["sp"] >= 150 and p["real"] and p["sp"] / p["real"] <= p["line"]))]
    rows.sort(key=lambda p: (-len(p["sales"]), (p["sp"] / len(p["sales"])) if p["sales"] else 9e9, p["sp"] / max(p["real"], 1)))
    print(f"\n################ {acct}（线 RM{rows[0]['line'] if rows else 0:.0f}）· 有单，或花费 ≥ RM150 且真 CPL ≤ 线")
    for p in rows:
        a, ns = p["a"], len(p["sales"])
        on = "在跑" if (a["status"], a["adset"]["status"], a["campaign"]["status"]) == ("ACTIVE",) * 3 else \
            f"campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']}"
        h = (f"60天 RM{p['s60']:,.0f}/{p['n60']}单 = CPA {p['s60'] / p['n60']:,.0f}" + (" ⚠️超硬线，开了会马上被关" if p['s60'] / p['n60'] > p['hard'] else
             f"（离硬线 RM{p['n60'] * p['hard'] - p['s60']:,.0f}）")) if p["n60"] else f"60天 RM{p['s60']:,.0f}/0单"
        wk = "" if a["campaign"]["name"].startswith("(Webinarkit)") else " ⚠️非Webinarkit"
        rj = " ⚠️被拒" if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES") else ""
        print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} · {on}{wk}{rj}\n"
              f"      RM{p['sp']:,.0f} · 真 {p['real']} · CPL {p['sp'] / max(p['real'], 1):.0f} · 单 {ns}"
              + (f" · CPA {p['sp'] / ns:,.0f} · 成交日 {', '.join(f'{x:%m/%d}' for x in sorted(p['sales']))}" if ns else "") + f" · {h}")
print("\nREOPEN CANDIDATES DONE (read-only)")
