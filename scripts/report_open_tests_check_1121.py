# -*- coding: utf-8 -*-
"""Read-only follow-up ~1h after the plan-B openings (owner 11/18: confirm it really delivers + spends).
Lists every test campaign built 11/19 (all 5, incl. SG LOW CPL which must still be PAUSED): three layers + effective_status per ad,
and today's (MYT) spend per ad."""
import datetime as dt

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CAMPS = [("config.sg.yaml", "120250705800700521", "开（owner 11/19 17:1x 自己开）"), ("config.my5.yaml", "120251995650640329", "开（owner 11/21 10:4x「现在开」）"),
         ("config.sg.yaml", "120250705919180521", "开（owner 11/21 10:4x「现在开」）"),
         ("config.sg.yaml", "120250706566080521", "开（owner 11/19 17:1x 自己开）"),
         ("config.my5.yaml", "120251993979260329", "开（owner 11/19 开）"), ("config.my5.yaml", "120251993985380329", "开（owner 11/19 开）")]
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读")
for cfg, cid, want in CAMPS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    c = g.get_object(cid, "name,status,effective_status,daily_budget")
    spend = {r["ad_id"]: float(r.get("spend") or 0) for r in g.account_insights(
        s.meta.account_path, level="ad", fields="ad_id,spend", time_range={"since": NOW.date().isoformat(), "until": NOW.date().isoformat()})}
    print(f"\n■ {c['name']} · campaign {cid} · 应该 {want} · 现在 {c['status']} → {c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
    for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "200"}):
        sp = spend.get(a["id"], 0.0)
        flag = "🟢" if a["effective_status"] == "ACTIVE" and sp > 0 else ("🟡" if a["effective_status"] == "ACTIVE" else "⚪")
        print(f"   {flag} {a['adset']['name']} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']}"
              f" → 实际 {a['effective_status']} · 今天 RM{sp:.2f}")
print("\nCHECK DONE")
