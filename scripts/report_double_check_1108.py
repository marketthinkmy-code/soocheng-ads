# -*- coding: utf-8 -*-
"""READ-ONLY double check (owner 11/8「有哪些需要我做决定要我关的吗？现在 daily budget 多少？预测花到星期三总花费？
确保都有符合 CPA CPL 的条件，有没有误关？double check 下」). No PII.

A) per account: live daily budget (campaign CBO + ad-set ABO with a live ad), spend per day since 11/5, today so far.
B) EVERY ad switched Active → Inactive since Thursday 00:00 MYT (any actor), read back with campaign › ad set · ad id,
   and re-judged against the monitor rules from scratch:
     - Thu-week spend / regs / CPL vs the account line and floor (veteran floor RM150 if since-10/16 ≥10 regs @ CPL ≤40)
     - robust-UTM CPA at its OWN position since 10/29 (campaign core without «1-x-y» · ad set · creative keyword) —
       the monitor joins exact names, so a renamed campaign could hide a sale: this is the 误关 check.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow()
MYT = NOW + dt.timedelta(hours=8)
TODAY = MYT.date()
THU, U0, C0 = _week_start_thursday(TODAY), dt.date(2026, 10, 29), dt.date(2026, 11, 5)
THU_UTC = int(dt.datetime.combine(THU, dt.time(0), tzinfo=dt.timezone.utc).timestamp()) - 8 * 3600
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("年纪大", "年纪大的人"), ("将多", "用我的方法 将多"), ("用我的方法", "用我的方法"), ("korea", "korea"), ("盖电脑", "盖电脑"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("一个目的", "我只有一个目的"), ("求人", "赚美金=求人"), ("赚美金", "赚美金")]
core = lambda c: re.sub(r"\s+", " ", re.sub(r"\|\s*\d+-\d+-\d+\s*\|", "|", cpa.norm(c or "").replace("(webinarkit)", ""))).strip(" |")
cre = lambda a: next((v for k, v in CRE if k in (a or "").lower()), cpa.norm(a or ""))
key = lambda c, s, a: (core(c), cpa.norm(s or ""), cre(a))
digits = lambda v: re.sub(r"\D", "", v or "")
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
regs_by_key = defaultdict(set)
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if d and d >= U0 and "webinarkit" in (r.get("UTM Campaign") or "").lower():
        who = tuple(k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k)
        if who:
            regs_by_key[key(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(who)
print(f"现在 {MYT:%m-%d %H:%M} MYT · 周四窗口 {THU}→{TODAY} · Paid 表 {U0} 起成交 {len(paid)} 笔")

for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct, tok, k = s.meta.account_path, f"offsite_conversion.custom.{cc}", s.kpi
    zero = k.zero_lead_spend_myr if k.zero_lead_spend_myr is not None else k.cpl_min_spend_myr

    def ins(a, b, level="ad", inc=""):
        return g._get_all(acct + "/insights", {"fields": f"{level}_id,spend,actions{inc}", "level": level, "limit": "1000",
                                               "time_range": tr(a, b), **({"time_increment": "1"} if inc else {})})
    agg = lambda rows: {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in rows}
    wk, lt, rel, td = agg(ins(THU, TODAY)), agg(ins(dt.date(2026, 10, 16), TODAY)), agg(ins(U0, TODAY)), agg(ins(TODAY, TODAY))
    daily = g._get_all(acct + "/insights", {"fields": "spend,actions", "limit": "50", "time_range": tr(C0, TODAY), "time_increment": "1"})

    # ---- A) budget + pacing
    print(f"\n################ {label}")
    for d in daily:
        print(f"  {d['date_start']}: RM{float(d.get('spend') or 0):,.0f} · 报名 {extract_results(d.get('actions'), tok):.0f}")
    camps = {c["id"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,status,effective_status,daily_budget", "limit": "300"})}
    sets = {a["id"]: a for a in g._get_all(acct + "/adsets", {"fields": "name,status,effective_status,daily_budget,campaign_id", "limit": "500"})}
    ads = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,campaign_id,adset_id", "limit": "2000"})
    live = [a for a in ads if a["effective_status"] == "ACTIVE"]
    budget, seen = 0, set()
    for a in live:
        c, st = camps[a["campaign_id"]], sets[a["adset_id"]]
        if c.get("daily_budget") and c["id"] not in seen:
            seen.add(c["id"]); budget += int(c["daily_budget"]) // 100
            print(f"  预算 «{c['name']}» · campaign {c['id']} · CBO RM{int(c['daily_budget']) // 100}")
        elif st.get("daily_budget") and st["id"] not in seen:
            seen.add(st["id"]); budget += int(st["daily_budget"]) // 100
            print(f"  预算 «{c['name']}» › {st['name']} · adset {st['id']} · ABO RM{int(st['daily_budget']) // 100}")
    for c in camps.values():   # campaigns ON but with no live ad (budget not spending)
        if c["effective_status"] == "ACTIVE" and c["id"] not in {a["campaign_id"] for a in live}:
            print(f"  ⚠️ campaign ON 但没有在跑的 ad: «{c['name']}» · {c['id']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
    print(f"  ▶ {label} 在跑日预算合计 RM{budget} · 今天已花(全部 ad) RM{sum(v[0] for v in td.values()):,.0f}")

    # ---- live ads, re-judged
    def judge(aid, cname=""):
        ws, wr = wk.get(aid, (0.0, 0.0))
        ls, lr = lt.get(aid, (0.0, 0.0))
        ov = next((o for o in getattr(k, "campaign_overrides", []) if o.match and o.match in cname), None)
        line = k.cpl_threshold_myr
        if ov is not None:            # PR #88: NEW VIDEO campaigns judged at RM50 (0-reg floor / CPL floor / CPL line)
            vet = False
            fc = ov.cpl_min_spend_myr if ov.cpl_min_spend_myr is not None else k.cpl_min_spend_myr
            fz = ov.zero_lead_spend_myr if ov.zero_lead_spend_myr is not None else zero
            line = ov.cpl_threshold_myr if ov.cpl_threshold_myr is not None else line
        else:
            vet = bool(k.veteran_min_regs and lr >= k.veteran_min_regs and ls / lr <= k.veteran_max_cpl_myr)
            fc = max(k.cpl_min_spend_myr, k.veteran_min_spend_myr) if vet else k.cpl_min_spend_myr
            fz = max(zero, k.veteran_min_spend_myr) if vet else zero
        if wr == 0:
            v = "0报名·花满门槛→该关" if ws >= fz else f"0报名·未到门槛 RM{fz:.0f}"
        elif ws < fc:
            v = f"CPL {ws / wr:.0f}·未到门槛 RM{fc:.0f}"
        else:
            v = f"CPL {ws / wr:.0f} " + (f"超线(>{line:.0f})→该关" if ws / wr > line else f"线内(≤{line:.0f})")
        return ws, wr, ls, lr, vet, v

    def pos(a):
        return camps[a["campaign_id"]]["name"], sets[a["adset_id"]]["name"]

    def cpa_line(a):
        cn, sn = pos(a)
        ppl = regs_by_key.get(key(cn, sn, a["name"]), set())
        nb = sum(any(w in buyers for w in who) for who in ppl)
        sp = rel.get(a["id"], (0.0, 0.0))[0]
        return f"10/29起 RM{sp:,.0f} · UTM报名 {len(ppl)} → 原位成交 {nb}" + (f" · CPA RM{sp / nb:,.0f}" if nb else "")

    print(f"  -- 在跑 ad（{len(live)}）:")
    for a in sorted(live, key=pos):
        cn, sn = pos(a)
        ws, wr, ls, lr, vet, v = judge(a["id"], cn)
        print(f"   🟢 {cn} › {sn} · {a['name']} · ad {a['id']}{' · 老将' if vet else ''}\n"
              f"        周四起 RM{ws:.2f}/{wr:.0f} → {v} · 10/16起 RM{ls:,.0f}/{lr:.0f} · {cpa_line(a)}")

    # ---- B) every Active → Inactive on an ad since Thursday
    acts = g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data",
                                             "since": str(THU_UTC), "limit": "1000"})
    offs = {}
    for x in sorted(acts, key=lambda x: x["event_time"]):
        if "run_status" not in (x.get("event_type") or ""):
            continue
        try:
            ed = json.loads(x.get("extra_data") or "{}")
        except Exception:                                                # noqa: BLE001
            ed = {}
        new = ed.get("new_value")
        new = new.get("new_value", new) if isinstance(new, dict) else new
        offs.setdefault((x["object_id"], x["event_type"]), []).append((x["event_time"], x.get("actor_name"), str(new)))
    byid = {a["id"]: a for a in ads}
    print("  -- 周四起被关的（ad 层 Active→Inactive；时间 MYT）:")
    for (oid, et), evs in offs.items():
        last = evs[-1]
        if last[2] != "Inactive":
            continue
        t = (dt.datetime.fromisoformat(last[0].replace("Z", "+00:00").replace("+0000", "+00:00")) + dt.timedelta(hours=8)).strftime("%m-%d %H:%M")
        if "ad_run_status" in et and oid in byid:
            a = byid[oid]
            cn, sn = pos(a)
            ws, wr, ls, lr, vet, v = judge(oid, cn)
            print(f"   🔴 {t} [{last[1]}] {cn} › {sn} · {a['name']} · ad {oid} · 现状 {a['effective_status']}{' · 老将' if vet else ''}\n"
                  f"        周四起 RM{ws:.2f}/{wr:.0f} → {v} · 10/16起 RM{ls:,.0f}/{lr:.0f} · {cpa_line(a)}")
        elif "ad_run_status" not in et:
            nm = (camps.get(oid) or sets.get(oid) or {}).get("name", "?")
            print(f"   ⚫ {t} [{last[1]}] {et.replace('update_', '')} «{nm}» · {oid}")
print("\nDOUBLE CHECK DONE (read-only)")
