# -*- coding: utf-8 -*-
"""READ-ONLY morning watch (owner 「紧密看广告」 + 死忌 2026-10-25). Window = Thursday-to-today (the owner's view).
1) Every LIVE ad with spend ≥ RM100 (Thu-week or since creation) and ≤ 1 registration — campaign › ad set · ad id, with
   the monitor's own verdict/reason for it (evaluate_account, same rules as the live monitor).
2) Per campaign: yesterday vs the day before, and Thu-week to date (spend · reg · CPL).
3) The 赚美金 test ads (MY 5.0): status, Thu-week / lifetime spend · reg."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, evaluate_account, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
Y, YY = TODAY - dt.timedelta(days=1), TODAY - dt.timedelta(days=2)
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))


def rows(g, acct, level, since, until, fields):
    return g._get_all(acct + "/insights", {"fields": fields, "level": level, "limit": "500",
                                           "time_range": json.dumps({"since": since.isoformat(), "until": until.isoformat()})})


for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {label}（线 RM{s.kpi.cpl_threshold_myr:.0f} · 判 CPL 门槛 RM{s.kpi.cpl_min_spend_myr:.0f} · "
          f"0 报名门槛 RM{s.kpi.zero_lead_spend_myr:.0f} · 窗口 {s.kpi.cpl_lookback} {THU}→{TODAY}）")
    verdict = {d.ad_id: d for d in evaluate_account(g, s)}
    wk = {r["ad_id"]: r for r in rows(g, acct, "ad", THU, TODAY, "ad_id,ad_name,adset_name,campaign_name,spend,actions")}
    life = {r["ad_id"]: r for r in rows(g, acct, "ad", dt.date(2026, 10, 16), TODAY, "ad_id,spend,actions")}
    live = {a["id"]: a for a in g._get_all(acct + "/ads", {"fields": "name,effective_status,adset{name},campaign{name}", "limit": "500"})
            if a.get("effective_status") == "ACTIVE"}
    print("\n① 在跑、花了 ≥RM100、报名 ≤1 的广告（campaign › ad set · ad ID）:")
    n = 0
    for aid, a in live.items():
        w, l = wk.get(aid, {}), life.get(aid, {})
        ws, wr = float(w.get("spend") or 0), extract_results(w.get("actions"), tok)
        ls, lr = float(l.get("spend") or 0), extract_results(l.get("actions"), tok)
        if (ws >= 100 and wr <= 1) or (ls >= 100 and lr <= 1):
            d = verdict.get(aid)
            n += 1
            print(f"   {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · 周四起 RM{ws:.0f}/{wr:.0f} · "
                  f"10/16起 RM{ls:.0f}/{lr:.0f} · monitor: {('PAUSE' if d.should_pause else 'keep') + ' (' + d.reason + ')' if d else '不在评估范围'}")
    print(f"   共 {n} 支" if n else "   无")
    print("\n② campaign：前天 · 昨天 · 周四起")
    agg = defaultdict(lambda: {})
    for key, since, until in (("yy", YY, YY), ("y", Y, Y), ("wk", THU, TODAY)):
        for r in rows(g, acct, "campaign", since, until, "campaign_name,spend,actions"):
            agg[r["campaign_name"]][key] = (float(r.get("spend") or 0), extract_results(r.get("actions"), tok))
        time.sleep(0.5)
    tot = defaultdict(lambda: [0.0, 0.0])
    for c, v in sorted(agg.items(), key=lambda kv: -kv[1].get("wk", (0, 0))[0]):
        def f(k):
            sp, rg = v.get(k, (0.0, 0.0))
            tot[k][0] += sp; tot[k][1] += rg
            return f"RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "")
        print(f"   {c[:60]:<60} {YY.strftime('%m-%d')} {f('yy'):<14} {Y.strftime('%m-%d')} {f('y'):<14} 周四起 {f('wk')}")
    print("   合计: " + " · ".join(f"{k} RM{sp:.0f}/{rg:.0f}={sp / rg if rg else 0:.0f}" for k, (sp, rg) in tot.items()))
    if label == "MY 5.0":
        print("\n③ 赚美金测试 ads:")
        for aid, a in live.items():
            pass
        for a in g._get_all(acct + "/ads", {"fields": "name,effective_status,adset{name},campaign{name}", "limit": "500"}):
            if "赚美金，一定要接美国客户" in (a.get("name") or "") and a["effective_status"] not in ("DELETED", "ARCHIVED", "PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"):
                w, l = wk.get(a["id"], {}), life.get(a["id"], {})
                print(f"   {a['campaign']['name']} › {a['adset']['name']} · ad {a['id']} · {a['effective_status']} · "
                      f"周四起 RM{float(w.get('spend') or 0):.0f}/{extract_results(w.get('actions'), tok):.0f} · "
                      f"10/16起 RM{float(l.get('spend') or 0):.0f}/{extract_results(l.get('actions'), tok):.0f}")
print("\nMORNING WATCH DONE (read-only)")
