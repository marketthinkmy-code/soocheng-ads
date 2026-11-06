# -*- coding: utf-8 -*-
"""READ-ONLY full audit (owner 11/6「其他的广告数据全部都要重新，认真，盘一轮。再建议我。不要马虎疏忽」).
Every (Webinarkit) ad on MY 5.0 + SG with ≥RM30 spend since 10/16, plus its campaign. All numbers from this run. No PII.
Per ad: campaign › ad set · ad · id · state (live / who paused what, when, MYT) · since 10/16 · last 7 days · Thu-week ·
veteran (monitor config) · what the monitor decides on its Thu-week numbers (as-is if live; as-if-reopened if paused) ·
reliable-UTM evidence: registrants since 10/29 carrying this exact position's UTM → how many are in the Paid Student List
(Date ≥ 10/29) · Paid rows whose own UTM is this exact position (since 10/16).
Per campaign: status, who paused, daily budget, totals. Then spend since 11/5 vs the RM6,250 plan."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, _week_start_thursday, decide, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU, D7, L0, U0 = _week_start_thursday(TODAY), TODAY - dt.timedelta(days=6), dt.date(2026, 10, 16), dt.date(2026, 10, 29)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
fmt = lambda sp, rg: f"RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "")

# ── sheets ──
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:8]) if "UTM Campaign" in r)
    return [dict(zip(v[hi], r)) for r in v[hi + 1:]]


em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
pkey = lambda c, s, a: (_mkey(c or ""), _mkey(s or ""), cpa.norm(a or ""))
paid = table(s0.cpa.sales_tab)
buyers = set()
paid_pos = defaultdict(int)
n_paid_rel = 0
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d:
        continue
    if d >= U0:
        n_paid_rel += 1
        for k in (em(p.get("Email")), tel(p.get("Phone Number"))):
            if k:
                buyers.add(k)
    if d >= L0:
        paid_pos[pkey(p.get("UTM Campaign"), p.get("UTM Ads Set"), p.get("UTM Ads Name"))] += 1
reg_pos = defaultdict(set)
for r in table("Register"):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < U0 or "webinarkit" not in (r.get("UTM Campaign") or "").lower():
        continue
    who = [k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k]
    if who:
        reg_pos[pkey(r.get("UTM Campaign"), r.get("UTM Ads Set"), r.get("UTM Ads Name"))].add(tuple(who))
print(f"窗口：至今 = {L0}→{TODAY} · 7天 = {D7}→{TODAY} · 周四起 = {THU}→{TODAY} · 可靠 UTM = 报名日 ≥{U0}（Paid 表 {U0} 起成交 {n_paid_rel} 笔）")

for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct, tok, k = s.meta.account_path, f"offsite_conversion.custom.{cc}", s.kpi
    zero = k.zero_lead_spend_myr if k.zero_lead_spend_myr is not None else k.cpl_min_spend_myr

    def ins(a, b):
        return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in g._get_all(
            acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000", "time_range": tr(a, b)})}
    lt, d7, wk = ins(L0, TODAY), ins(D7, TODAY), ins(THU, TODAY)
    off = {}
    for x in sorted(g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                      "since": str(int(dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc).timestamp())), "limit": "5000"}),
                    key=lambda x: x["event_time"]):
        m = re.search(r'"new_value":"(Active|Inactive)"', (x.get("extra_data") or "").replace(" ", ""))
        if "run_status" in (x.get("event_type") or "") and m:
            t = dt.datetime.fromisoformat(x["event_time"].replace("+0000", "+00:00")) + dt.timedelta(hours=8)
            off[x["object_id"]] = (m.group(1), "monitor" if x.get("actor_name") == "STOCKBLOOM-ADS" else ("人手" if x.get("actor_name") not in ("Meta", None) else "Meta"), f"{t:%m-%d %H:%M}")
    camps = {c["id"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,status,effective_status,daily_budget", "limit": "300"})}
    sets = {a["id"]: a for a in g._get_all(acct + "/adsets", {"fields": "name,status,daily_budget", "limit": "600"})}
    ads = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,campaign_id,adset_id", "limit": "2000"})
    by_camp = defaultdict(list)
    for a in ads:
        c = camps.get(a["campaign_id"], {})
        if "(Webinarkit)" not in c.get("name", "") or lt.get(a["id"], (0, 0))[0] < 30:
            continue
        by_camp[a["campaign_id"]].append(a)
    budget_live = 0
    print(f"\n################ {label}（线 CPL {k.cpl_threshold_myr:.0f} · CPL 判断起点 RM{k.cpl_min_spend_myr:.0f} · 0 报名 RM{zero:.0f} · 老将 ≥{k.veteran_min_regs} 报名且 CPL≤{k.veteran_max_cpl_myr:.0f} → RM{k.veteran_min_spend_myr:.0f}）")
    for cid, lst in sorted(by_camp.items(), key=lambda kv: camps[kv[0]]["name"]):
        c = camps[cid]
        cb = int(c.get("daily_budget") or 0) // 100
        cs = off.get(cid)
        live_n = sum(a["effective_status"] == "ACTIVE" for a in lst)
        if c["status"] == "ACTIVE" and live_n:
            budget_live += cb if cb else sum(int(sets[a["adset_id"]].get("daily_budget") or 0) // 100 for a in {x["adset_id"]: x for x in lst if x["effective_status"] == "ACTIVE"}.values())
        tl = [sum(lt.get(a["id"], (0, 0))[i] for a in lst) for i in (0, 1)]
        t7 = [sum(d7.get(a["id"], (0, 0))[i] for a in lst) for i in (0, 1)]
        print(f"\n  ■ «{c['name']}» · campaign {cid} · {c['status']}" + (f"（{cs[1]} {cs[2]} 关）" if c["status"] != "ACTIVE" and cs else "")
              + (f" · CBO RM{cb}" if cb else " · ABO") + f" · 在跑 ad {live_n} · 至今 {fmt(*tl)} · 7天 {fmt(*t7)}")
        for a in sorted(lst, key=lambda a: (a["effective_status"] != "ACTIVE", -lt.get(a["id"], (0, 0))[0])):
            sp, rg = lt.get(a["id"], (0.0, 0.0))
            vet = rg >= k.veteran_min_regs > 0 and sp / rg <= k.veteran_max_cpl_myr
            kk = k.model_copy(update={"cpl_min_spend_myr": max(k.cpl_min_spend_myr, k.veteran_min_spend_myr),
                                      "zero_lead_spend_myr": max(zero, k.veteran_min_spend_myr)}) if vet else k
            ws, wr = wk.get(a["id"], (0.0, 0.0))
            dec = decide(ws, wr, kk)
            verdict = ("会被关" if dec[0] else "不会被关") + f"({dec[1]})"
            st = sets.get(a["adset_id"], {})
            if a["effective_status"] == "ACTIVE":
                state = "🟢在跑"
            elif c["status"] != "ACTIVE":
                state = "⚫campaign关"
            elif st.get("status") != "ACTIVE":
                o = off.get(a["adset_id"])
                state = f"⚫adset关({o[1]} {o[2]})" if o else "⚫adset关"
            else:
                o = off.get(a["id"])
                state = f"🔴ad关({o[1]} {o[2]})" if o else f"🔴ad关({a['effective_status']})"
            key = pkey(c["name"], st.get("name"), a["name"])
            regs = reg_pos.get(key, set())
            nb = sum(any(w in buyers for w in who) for who in regs)
            ban = " 🚫禁跑" if compliance.is_banned(a["name"], s.compliance.banned_creatives) else ""
            print(f"    {state:<26} {st.get('name', '')[:22]} · {a['name'][:24]} · ad {a['id']}{ban}\n"
                  f"        至今 {fmt(sp, rg)} · 7天 {fmt(*d7.get(a['id'], (0, 0)))} · 周四起 {fmt(ws, wr)} · {'老将' if vet else '非老将'} · monitor{'' if a['effective_status'] == 'ACTIVE' else '(若开回)'}: {verdict}"
                  f" · 可靠UTM报名 {len(regs)}→成交 {nb} · Paid原位 {paid_pos.get(key, 0)}")
    sp5 = sum(v[0] for v in ins(dt.date(2026, 11, 5), TODAY).values())
    print(f"\n  {label} 在跑日预算合计 RM{budget_live} · 11/5 起已花 RM{sp5:,.0f}")
print("\nFULL AUDIT DONE (read-only)")
