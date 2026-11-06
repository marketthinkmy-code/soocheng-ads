# -*- coding: utf-8 -*-
"""READ-ONLY pass/fail audit (owner 11/6「再重新复盘全部 MY & SG，哪些 CPA CPL 不过关…精确的数据分析」). No PII.
Window for CPA = the reliable-UTM period 10/29 → today (Register UTM = this registration's source since the 10/29 fix).
Account level : spend 10/29→today ÷ ALL Paid Student List sales dated ≥10/29 from that country (phone code) = true account CPA.
Ad level      : every (Webinarkit) ad with ≥RM30 spend since 10/29 (live or paused):
  CPL  — Thu-week (owner's window) and 10/29→today, from Meta.
  CPA  — 10/29→today spend ÷ buyers among the people whose Register row carries this ad's UTM (robust match: campaign core
         without the «1-x-y» segment · ad set · creative keyword). Verdict: ≤1,500 过关 · 1,500–2,000 观察 · >2,000 不过关;
         0 buyers → 已花 >RM2,000 = 不过关, else 未能判定 (spend so far shown).
  CPL verdict — MY line 60; SG ≤80 好 / 80–95 观察 / >95 不过关; judged only once the window spend ≥ the monitor floor."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU, U0 = _week_start_thursday(TODAY), dt.date(2026, 10, 29)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人"), ("赚美金", "赚美金")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), cpa.norm(a or ""))
key = lambda c, s, a: (core(c), cpa.norm(s or ""), cre(a))
digits = lambda v: re.sub(r"\D", "", v or "")
country = lambda p: "SG" if digits(p).startswith("65") or (len(digits(p)) == 8 and digits(p)[:1] in "689") else "MY"
em = lambda v: (v or "").strip().lower()
tel = lambda v: digits(v)[-8:]

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


paid = [p for p in table(s0.cpa.sales_tab) if (cpa.parse_date(p.get("Date", "")) or dt.date(2000, 1, 1)) >= U0]
buyers = {k for p in paid for k in (em(p.get("Email")), tel(p.get("Phone Number"))) if k}
sales_by_country = defaultdict(int)
for p in paid:
    sales_by_country[country(p.get("Phone Number"))] += 1
regs_by_key = defaultdict(set)
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if d and d >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower():
        who = tuple(k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k)
        if who:
            regs_by_key[key(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(who)
traced = 0
print(f"CPA 窗口 {U0}→{TODAY} · 周四窗口 {THU}→{TODAY} · Paid 表 {U0} 起成交 {len(paid)} 笔（MY {sales_by_country['MY']} · SG {sales_by_country['SG']}）")


def cpa_verdict(sp, nb):
    if nb:
        c = sp / nb
        return f"CPA RM{c:,.0f} " + ("✅过关" if c <= 1500 else ("⚠️观察" if c <= 2000 else "❌不过关"))
    return f"0 成交/已花 RM{sp:,.0f} " + ("❌不过关(>2,000 未成交)" if sp > 2000 else "⏳未能判定")


for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct, tok, k = s.meta.account_path, f"offsite_conversion.custom.{cc}", s.kpi
    zero = k.zero_lead_spend_myr if k.zero_lead_spend_myr is not None else k.cpl_min_spend_myr

    def ins(a, b):
        return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in g._get_all(
            acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000", "time_range": tr(a, b)})}
    rel, wk, lt = ins(U0, TODAY), ins(THU, TODAY), ins(dt.date(2026, 10, 16), TODAY)
    ads = g._get_all(acct + "/ads", {"fields": "name,effective_status,campaign{name,status},adset{name}", "limit": "2000"})
    acc_sp = sum(v[0] for v in rel.values())
    acc_rg = sum(v[1] for v in rel.values())
    ns = sales_by_country[label.split()[0]]
    print(f"\n################ {label} · {U0} 起花费 RM{acc_sp:,.0f} · 报名 {acc_rg:.0f} · CPL {acc_sp / acc_rg:.0f} · "
          f"该国成交 {ns} 笔 → 账户 CPA RM{acc_sp / ns if ns else 0:,.0f}（含对不回广告的成交）")
    line, good = k.cpl_threshold_myr, (80.0 if label == "SG" else k.cpl_threshold_myr)
    rows = []
    for a in ads:
        sp, rg = rel.get(a["id"], (0.0, 0.0))
        if sp < 30 or "(Webinarkit)" not in a["campaign"]["name"]:
            continue
        ws, wr = wk.get(a["id"], (0.0, 0.0))
        ls, lr = lt.get(a["id"], (0.0, 0.0))
        vet = k.veteran_min_regs and lr >= k.veteran_min_regs and ls / lr <= k.veteran_max_cpl_myr
        floor_cpl = max(k.cpl_min_spend_myr, k.veteran_min_spend_myr) if vet else k.cpl_min_spend_myr
        floor_zero = max(zero, k.veteran_min_spend_myr) if vet else zero

        def cpl_v(spx, rgx, floor_c, floor_z):
            if rgx == 0:
                return f"RM{spx:.0f}/0 " + ("❌0报名" if spx >= floor_z else "⏳未到门槛")
            c = spx / rgx
            if spx < floor_c:
                return f"RM{spx:.0f}/{rgx:.0f}={c:.0f} ⏳未到门槛"
            if label == "SG":
                return f"RM{spx:.0f}/{rgx:.0f}={c:.0f} " + ("✅" if c <= good else ("⚠️" if c <= line else "❌"))
            return f"RM{spx:.0f}/{rgx:.0f}={c:.0f} " + ("✅" if c <= line else "❌")
        ppl = regs_by_key.get(key(a["campaign"]["name"], a["adset"]["name"], a["name"]), set())
        nb = sum(any(w in buyers for w in who) for who in ppl)
        traced += nb
        rows.append((a["effective_status"] != "ACTIVE", a["campaign"]["name"], a, ws, wr, sp, rg, vet, floor_cpl, floor_zero, len(ppl), nb,
                     cpl_v(ws, wr, floor_cpl, floor_zero), cpl_v(sp, rg, k.cpl_min_spend_myr, zero), cpa_verdict(sp, nb)))
    for off, cname, a, ws, wr, sp, rg, vet, fc, fz, npl, nb, wv, rv, cv in sorted(rows, key=lambda r: (r[0], r[1])):
        st = "🟢在跑" if not off else ("⚫campaign关" if a["campaign"]["status"] != "ACTIVE" else "🔴已关")
        ban = " 🚫禁跑" if compliance.is_banned(a["name"], s.compliance.banned_creatives) else ""
        print(f"  {st} {cname.replace('(Webinarkit) ', '').replace('STOCKBLOOM | ', '')[:36]} › {a['adset']['name'][:22]} · {a['name'][:26]} · ad {a['id']}{ban}{' · 老将' if vet else ''}\n"
              f"      CPL 周四起 {wv} · 10/29起 {rv} · UTM 报名 {npl} 人→成交 {nb} · {cv}")
print(f"\n能对回原位的成交合计 {traced} 笔 / {len(paid)} 笔")
print("PASS/FAIL DONE (read-only)")
