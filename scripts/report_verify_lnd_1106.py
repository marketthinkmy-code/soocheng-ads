# -*- coding: utf-8 -*-
"""READ-ONLY verification (owner 11/6「确保你的建议是对的…重新盘一轮」) for reopening
DAY TRADING › Day Trading | MY 28+ · Video：年纪大的人做不了交易？ · ad 120251454717600329. Every number from this run. No PII.
A. API facts for the ad: status, who paused it + when, spend/报名 since 10/16, Thu-week, per day since 10/29.
B. Veteran test exactly as the monitor computes it (current config), and what decide() returns for its Thu-week numbers.
C. Sales evidence in the reliable-UTM period (Register rows created ≥ 10/29, when the UTM fix went live):
   per creative (all MY 5.0 + SG positions): unique registrants with that UTM ad name → how many of them are in the
   Paid Student List with a Date ≥ 10/29 (buyers) → reg→sale %. Same for this exact position.
D. The old creative-CPA reference recomputed, with its spend split by account, to show what it was built on."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, decide, extract_results, parse_metrics
from adbot.settings import REPO_ROOT, load_settings

AID = "120251454717600329"
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
TOK = "offsite_conversion.custom.1048291251556714"
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})

print("A. 广告本身")
a = g.get_object(AID, "name,status,effective_status,created_time,campaign{name,status},adset{name,status}")
print(f"   {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {AID} · {a['status']}/{a['effective_status']} · 建 {a['created_time'][:10]}")
for x in sorted(g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                                 "since": str(int(dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc).timestamp())), "limit": "5000"}),
                key=lambda x: x["event_time"]):
    if x.get("object_id") == AID and "run_status" in (x.get("event_type") or "") and "new_value" in (x.get("extra_data") or ""):
        nv = re.search(r'"new_value":"(Active|Inactive)"', (x.get("extra_data") or "").replace(" ", ""))
        if nv:
            t = dt.datetime.fromisoformat(x["event_time"].replace("+0000", "+00:00")) + dt.timedelta(hours=8)
            print(f"   {t:%m-%d %H:%M} MYT · {x.get('actor_name')} → {nv.group(1)}")


def ins(since, until, inc=None):
    p = {"fields": "spend,actions,date_start", "time_range": tr(since, until)}
    if inc:
        p["time_increment"] = inc
    return g._get_all(AID + "/insights", p)


r = (ins(dt.date(2026, 10, 16), TODAY) or [{}])[0]
lsp, lrg = float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)
r = (ins(THU, TODAY) or [{}])[0]
wsp, wrg = float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)
print(f"   10/16 起: RM{lsp:.2f} / {lrg:.0f} 报名 = CPL {lsp / lrg if lrg else 0:.1f}")
print(f"   周四({THU})起: RM{wsp:.2f} / {wrg:.0f} 报名")
print("   每日（10/29 起）: " + " · ".join(f"{d['date_start'][5:]} RM{float(d.get('spend') or 0):.0f}/{extract_results(d.get('actions'), TOK):.0f}"
                                      for d in ins(dt.date(2026, 10, 29), TODAY, "1")))

print("\nB. 老将判定（照现在 main 的设定）")
k = s.kpi
vet = lrg >= k.veteran_min_regs and lrg and lsp / lrg <= k.veteran_max_cpl_myr
print(f"   设定: ≥{k.veteran_min_regs} 报名 且 CPL ≤{k.veteran_max_cpl_myr} (since {k.veteran_since}) · 门槛 RM{k.veteran_min_spend_myr}")
print(f"   结果: {'是老将' if vet else '不是老将'}（{lrg:.0f} 报名，CPL {lsp / lrg if lrg else 0:.1f}）")
zero = k.zero_lead_spend_myr if k.zero_lead_spend_myr is not None else k.cpl_min_spend_myr
kv = k.model_copy(update={"cpl_min_spend_myr": max(k.cpl_min_spend_myr, k.veteran_min_spend_myr),
                          "zero_lead_spend_myr": max(zero, k.veteran_min_spend_myr)}) if vet else k
print(f"   开回后 monitor 对本周 RM{wsp:.2f}/{wrg:.0f} 的判断: {decide(wsp, wrg, kv)[:2]}（不当老将时: {decide(wsp, wrg, k)[:2]}）")

print("\nC. UTM 修好后（报名日 ≥ 10/29）：报名 → 成交")
sc = SheetsClient(s.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
CRE = {"年纪大的人": "年纪大", "用我的方法": "用我的方法", "korea": "korea", "盖电脑": "盖电脑", "我跟你讲": "我跟你讲",
       "不选 forex": "不选 forex", "我只有一个目的": "一个目的"}
paid = [p for p in table(s.cpa.sales_tab) if (cpa.parse_date(p.get("Date", "")) or dt.date(2000, 1, 1)) >= dt.date(2026, 10, 29)]
buyer_keys = set()
for p in paid:
    for kk in (em(p.get("Email")), tel(p.get("Phone Number"))):
        if kk:
            buyer_keys.add(kk)
print(f"   Paid Student List 10/29 起成交 {len(paid)} 笔")
by_cre, by_pos = defaultdict(set), defaultdict(set)
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < dt.date(2026, 10, 29) or "webinarkit" not in (r.get("UTM Campaign") or "").lower():
        continue
    person = em(r.get("Email")) or tel(r.get("Phone Number"))
    adn = (r.get("UTM Ads Name") or "").lower()
    for c, kw in CRE.items():
        if kw.lower() in adn:
            by_cre[c].add(person)
    if "年纪大" in adn and "day trading" in (r.get("UTM Campaign") or "").lower() and "day trading" in (r.get("UTM Ads Set") or "").lower():
        by_pos["DT 年纪大"].add(person)
isbuyer = lambda pp: pp in buyer_keys
for c in CRE:
    regs = by_cre[c]
    b = sum(isbuyer(pp) for pp in regs)
    print(f"   {c:<10} 带 UTM 报名 {len(regs):>3} 人 → 成交 {b}" + (f"（{100 * b / len(regs):.1f}%）" if regs else ""))
regs = by_pos["DT 年纪大"]
print(f"   本支位置（DAY TRADING › 年纪大）报名 {len(regs)} 人 → 成交 {sum(isbuyer(pp) for pp in regs)}")

print("\nD. 之前的「素材 CPA 参考」是怎么来的（7/14 起，成交名单 UTM ad 名含 年纪大，first-touch）")
sales = [p for p in table(s.cpa.sales_tab) if (cpa.parse_date(p.get("Date", "")) or dt.date(2000, 1, 1)) >= dt.date(2026, 7, 14)
         and "年纪大" in (p.get("UTM Ads Name") or "")]
print(f"   成交 {len(sales)} 笔 · 日期 {sorted(str(cpa.parse_date(p.get('Date', ''))) for p in sales)}")
for label, cfg in (("MY3", "config.yaml"), ("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    st = load_settings(REPO_ROOT / "config" / cfg)
    sp = sum(float(x.get("spend") or 0) for x in graph_client(st)._get_all(st.meta.account_path + "/insights", {
        "fields": "ad_name,spend", "level": "ad", "limit": "1000", "time_range": tr(dt.date(2026, 7, 14), TODAY)}) if "年纪大" in (x.get("ad_name") or ""))
    print(f"   {label} 年纪大 花费 RM{sp:,.0f}")
print("\nVERIFY DONE (read-only)")
