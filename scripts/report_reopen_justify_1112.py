# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/11 23:3x「你确保这些列表里是有值得开的原因 比如 cpl cpa」).
For EVERY ad that will deliver after the 00:00 reopen (execute_reopen_all_1112.py: ads it reopens + ads already ACTIVE at
ad level under the 9 campaigns), print campaign › ad set · ad id with:
  Thu-week 11/5–11/11 spend/regs/CPL · 11/11 alone · 10/16起 spend/regs/CPL · 10/29起 spend · robust-UTM 原位成交 / CPA
and a verdict against the rules (MY line 60 · SG line 95, ≤80 good · NEW VIDEO RM80 · 30-day CPA ≤ RM960 · new ad ≤14 days)."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

U0, L0, W0, W1 = dt.date(2026, 10, 29), dt.date(2026, 10, 16), dt.date(2026, 11, 5), dt.date(2026, 11, 11)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人"), ("赚美金", "赚美金")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), cpa.norm(a or ""))
key = lambda c, s, a: (core(c), cpa.norm(s or ""), cre(a))
digits = lambda v: re.sub(r"\D", "", v or "")
em = lambda v: (v or "").strip().lower()
tel = lambda v: digits(v)[-8:]
CAMPS = {"config.my5.yaml": ("1048291251556714", ["120251840045110329", "120251840064210329", "120251840367640329",
                                                  "120251454704570329", "120251454700150329"]),
         "config.sg.yaml": ("1614065190214320", ["120250544490730521", "120250544550400521", "120250544649500521",
                                                 "120250144810670521"])}
EXTRA = {"120251454701640329", "120250144813920521"}

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


paid = [p for p in table(s0.cpa.sales_tab) if (cpa.parse_date(p.get("Date", "")) or dt.date(2000, 1, 1)) >= U0]
buyers = {k for p in paid for k in (em(p.get("Email")), tel(p.get("Phone Number"))) if k}
regs_by_key = defaultdict(set)
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if d and d >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower():
        who = tuple(k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k)
        if who:
            regs_by_key[key(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(who)
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · Paid 表 {U0} 起成交 {len(paid)} 笔")

for cfg, (cc, cids) in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g, acct, tok, k = graph_client(s), s.meta.account_path, f"offsite_conversion.custom.{cc}", s.kpi
    sg = "sg" in cfg
    line = k.cpl_threshold_myr

    def agg(a, b):
        rows = g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000", "time_range": tr(a, b)})
        return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in rows}
    wk, d11, lt, rel = agg(W0, W1), agg(W1, W1), agg(L0, TODAY), agg(U0, TODAY)
    print(f"\n################ {cfg} · 线 RM{line:.0f}" + (" (≤80 算好)" if sg else ""))
    for cid in cids:
        c = g.get_object(cid, "name,created_time")
        nv = "NEW VIDEO" in c["name"]
        ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,created_time,adset{name,status}", "limit": "100"})
        print(f"  «{c['name']}» {cid}")
        for a in sorted(ads, key=lambda x: (x["adset"]["name"], x["name"])):
            ban = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
            if ban or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
                continue
            will = (a["status"] == "ACTIVE") or (a["status"] == "PAUSED" and (nv or a["id"] in EXTRA))
            if not will:
                continue
            how = "本来就开" if a["status"] == "ACTIVE" else "00:00 开回"
            ws, wr = wk.get(a["id"], (0, 0)); ds, dr = d11.get(a["id"], (0, 0))
            ls, lr = lt.get(a["id"], (0, 0)); rs = rel.get(a["id"], (0, 0))[0]
            ppl = regs_by_key.get(key(c["name"], a["adset"]["name"], a["name"]), set())
            nb = sum(any(w in buyers for w in who) for who in ppl)
            age = (TODAY - dt.date.fromisoformat(a["created_time"][:10])).days
            cpl = lambda sp, r: f"CPL {sp / r:.0f}" if r else "0报名"
            if nv:
                fl = 80.0
                ok = (wr and ws / wr <= fl) or ws < fl
                why = (f"新视频 {age} 天（≤14 天新广告例外）· 花 RM{ws:.0f} 未到 RM80 门槛" if ws < fl else "") + \
                      (f" · {wr:.0f} 报名 {cpl(ws, wr)} ≤80 ✅" if wr and ws / wr <= fl else (" · 0 报名 ⚠️ 还没证明" if not wr else f" · {cpl(ws, wr)} >80 ❌"))
            else:
                lcpl = ls / lr if lr else 9e9
                good_cpa = nb and rs / nb <= 960
                ok = bool(good_cpa or (lr >= 5 and lcpl <= line))
                why = " · ".join(x for x in [
                    f"原位成交 {nb} · CPA RM{rs / nb:,.0f} ✅" if good_cpa else (f"10/29起 RM{rs:,.0f} 原位 0 成交" + (" ❌ 超过 RM960" if rs > 960 else "")),
                    f"10/16起 {cpl(ls, lr)}" + (" ✅" if lr >= 5 and lcpl <= line else " ❌")] if x)
            print(f"   {'🟢' if ok else '🟠'} [{how}] {c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}\n"
                  f"        周四周 RM{ws:.0f}/{wr:.0f} {cpl(ws, wr)} · 11/11 RM{ds:.0f}/{dr:.0f} · 10/16起 RM{ls:,.0f}/{lr:.0f} {cpl(ls, lr)}"
                  f" · 10/29起 RM{rs:,.0f} · UTM报名 {len(ppl)} → 原位成交 {nb}\n        → {why}")
print("\nJUSTIFY DONE (read-only)")
