# -*- coding: utf-8 -*-
"""READ-ONLY full review (owner 11/5「确保目前的广告 cpl cpa 都好…看完全盘再 suggest budget」).
For every ad on MY 5.0 + SG that is LIVE, or paused by the monitor, or sits in a carrier being considered
(LUXURY MY, WINNERS MY): campaign › ad set · ad · id · state (在跑 / monitor关 / 人手关 / campaign关) ·
since-launch (10/16) spend · 报名 · CPL · last-7-days spend · 报名 · CPL · strict sales (Paid Student List joined to the
person's Register row that carries a UTM, matched to this exact position) · strict CPA.
Plus creative-level CPA reference (all 3 accounts, 7/14 → today, first-touch UTM ad name) and per-campaign totals."""
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

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
D7 = TODAY - dt.timedelta(days=6)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = {"盖电脑": lambda n: "盖电脑" in n, "korea": lambda n: "korea" in n, "用我的方法": lambda n: "用我的方法" in n and "将多" not in n,
       "年纪大的人": lambda n: "年纪大" in n, "我跟你讲": lambda n: "我跟你讲" in n, "不选 forex": lambda n: "不选 forex" in n or "不选forex" in n,
       "我只有一个目的": lambda n: "一个目的" in n}
cre_of = lambda n: next((k for k, f in CRE.items() if f(n.lower())), "其他")

# ── sales: Paid Student List; position = the paid row's UTM, or the buyer's Register row that carries a UTM ──
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
paid, reg = table(s0.cpa.sales_tab), table("Register")
idx = defaultdict(list)
for r in reg:
    for k in (em(r.get("Email")), tel(r.get("Phone Number"))):
        if k:
            idx[k].append(r)
key = lambda c, s, a: (_mkey(c), _mkey(s), cpa.norm(a))
strict = defaultdict(int)
cre_sales = defaultdict(int)
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d:
        continue
    if d >= dt.date(2026, 7, 14):
        cre_sales[cre_of(p.get("UTM Ads Name") or "")] += 1
    if d < dt.date(2026, 10, 16):
        continue
    cands = [key(p.get("UTM Campaign", ""), p.get("UTM Ads Set", ""), p.get("UTM Ads Name", ""))]
    for r in idx.get(em(p.get("Email"))) or idx.get(tel(p.get("Phone Number"))) or []:
        if "webinarkit" in (r.get("UTM Campaign") or "").lower():
            cands.append(key(r["UTM Campaign"], r.get("UTM Ads Set", ""), r.get("UTM Ads Name", "")))
    for k in dict.fromkeys(cands):
        strict[k] += 1

cre_spend = defaultdict(float)
out = {}
for label, cfg, cc in (("MY3", "config.yaml", None), ("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    for r in g._get_all(acct + "/insights", {"fields": "ad_name,spend", "level": "ad", "limit": "1000", "time_range": tr(dt.date(2026, 7, 14), TODAY)}):
        cre_spend[cre_of(r.get("ad_name") or "")] += float(r.get("spend") or 0)
    if not cc:
        continue
    tok = f"offsite_conversion.custom.{cc}"
    lt = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000", "time_range": tr(dt.date(2026, 10, 16), TODAY)})}
    w7 = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000", "time_range": tr(D7, TODAY)})}
    acts = g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                             "since": str(int(dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc).timestamp())), "limit": "5000"})
    off = {}
    for x in sorted(acts, key=lambda x: x["event_time"]):
        if "run_status" in (x.get("event_type") or "") and '"new_value":"Inactive"' in (x.get("extra_data") or "").replace(" ", ""):
            off[x["object_id"]] = ("monitor" if x.get("actor_name") == "STOCKBLOOM-ADS" else "人手") + " " + x["event_time"][5:10]
    ads = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,campaign{id,name,status},adset{id,name,status}", "limit": "2000"})
    rows = []
    for a in ads:
        if "(Webinarkit)" not in a["campaign"]["name"] or "🚫" in a["name"] or a["id"] not in lt:
            continue
        sp, rg = float(lt[a["id"]].get("spend") or 0), extract_results(lt[a["id"]].get("actions"), tok)
        if sp < 30:
            continue
        sp7, rg7 = (float(w7[a["id"]].get("spend") or 0), extract_results(w7[a["id"]].get("actions"), tok)) if a["id"] in w7 else (0.0, 0.0)
        if a["effective_status"] == "ACTIVE":
            state = "在跑"
        elif a["campaign"]["status"] != "ACTIVE":
            state = f"campaign关({off.get(a['campaign']['id'], '?')})"
        elif a["adset"]["status"] != "ACTIVE":
            state = f"adset关({off.get(a['adset']['id'], '?')})"
        else:
            state = f"ad关({off.get(a['id'], a['effective_status'])})"
        n = strict.get(key(a["campaign"]["name"], a["adset"]["name"], a["name"]), 0)
        rows.append((a["campaign"]["name"].replace("(Webinarkit) ", "").replace("STOCKBLOOM | ", ""), a["adset"]["name"], a["name"], a["id"], state, sp, rg, sp7, rg7, n))
    out[label] = rows

print(f"窗口：上线至今 = 10/16→{TODAY}；7天 = {D7}→{TODAY}")
for label, rows in out.items():
    print(f"\n################ {label}")
    camp = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0])
    for r in sorted(rows, key=lambda r: (r[0], r[4] != "在跑", -r[5])):
        c, st, an, aid, state, sp, rg, sp7, rg7, n = r
        cv = camp[c]
        cv[0] += sp; cv[1] += rg; cv[2] += sp7; cv[3] += rg7; cv[4] += n
        print(f"  {state:<22} {c[:34]} › {st[:24]} · {an[:26]} · ad {aid} · 至今 RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "")
              + f" · 7天 RM{sp7:.0f}/{rg7:.0f}" + (f"={sp7 / rg7:.0f}" if rg7 else "") + f" · 原位成交 {n}" + (f" CPA {sp / n:,.0f}" if n else ""))
    print("  -- campaign 合计（至今 · 7天 · 原位成交）")
    for c, v in camp.items():
        print(f"     {c[:44]:<44} 至今 RM{v[0]:.0f}/{v[1]:.0f}" + (f"={v[0] / v[1]:.0f}" if v[1] else "") + f" · 7天 RM{v[2]:.0f}/{v[3]:.0f}" + (f"={v[2] / v[3]:.0f}" if v[3] else "") + f" · 成交 {v[4]}")
print("\n素材 CPA 参考（MY3+MY5+SG，7/14→今天，first-touch，不是原位）:")
for k in sorted(CRE, key=lambda k: cre_spend[k] / cre_sales[k] if cre_sales[k] else 9e9):
    print(f"   {k:<10} 花费 RM{cre_spend[k]:,.0f} · 成交 {cre_sales[k]} · " + (f"CPA RM{cre_spend[k] / cre_sales[k]:,.0f}" if cre_sales[k] else "CPA —"))
print("\nFULL REVIEW DONE (read-only)")
