# -*- coding: utf-8 -*-
"""READ-ONLY (11/25 20:49: Meta shows MY 22 / SG 3 registrations today with no spend since the 07:00 cap-pause,
vs Register-tab ad regs MY 1 / SG 0). Two questions:
 ① which ad positions got today's Meta registrations (campaign › ad set · ad ID, count);
 ② does counting today flip any ad into 'veteran' (since 10/16 ≥10 regs at CPL ≤40, bots removed — the monitor's own
    rule and parse) → RM150 floor next cycle. Compare veteran_since→yesterday vs veteran_since→today. No writes."""
from __future__ import annotations

import datetime as dt
import json

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, parse_metrics, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
YDAY = TODAY - dt.timedelta(days=1)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    k = s.kpi
    vs = cpa.parse_date(k.veteran_since)
    reg = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.register_tab)
    bots = cpa.bot_registrations(reg, since=vs, camp_key=_mkey, adset_key=_mkey)
    q = lambda a, b: {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {
        "level": "ad", "time_range": tr(a, b), "fields": "ad_id,spend,actions", "limit": "500"})}
    today, upto_y, upto_t = q(TODAY, TODAY), q(vs, YDAY), q(vs, TODAY)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,campaign{name,status},"
                                                     "adset{name,status,promoted_object}", "limit": "500"})
    token = result_action_type(s.meta.conversion_event)
    ccs = {str(c) for c in (s.meta.custom_conversions or [])}
    print(f"\n################ {label} · 今天 {TODAY} · 老将 = {k.veteran_since} 起 ≥{k.veteran_min_regs} 报名且 CPL ≤{k.veteran_max_cpl_myr:.0f}（扣机器人）")
    tot, flips = 0.0, []
    for a in ads:
        po = (a["adset"] or {}).get("promoted_object") or {}
        cc = str(po.get("custom_conversion_id") or "")
        tok = f"offsite_conversion.custom.{cc}" if cc and cc in ccs else token
        pos = f"{a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}"
        sp_t, rg_t = parse_metrics(today.get(a["id"]), tok)
        if rg_t:
            tot += rg_t
            print(f"  今天 Meta {rg_t:.0f} 报名 · 花费 RM{sp_t:.2f} · {pos} · campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']}")
        nb = sum(1 for d in bots.get((_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"])), []) if d >= vs)
        vet = []
        for src in (upto_y, upto_t):
            lsp, lrg = parse_metrics(src.get(a["id"]), tok)
            lrg = max(0.0, lrg - nb)
            vet.append((lrg >= k.veteran_min_regs and lsp / lrg <= k.veteran_max_cpl_myr, lsp, lrg))
        if vet[0][0] != vet[1][0]:
            flips.append((pos, vet))
    print(f"  今天 Meta 报名合计（按 ad 加总）：{tot:.0f}")
    print(f"  老将身份因今天的报名而改变：{len(flips)} 支")
    for pos, ((v0, s0, r0), (v1, s1, r1)) in flips:
        print(f"    {pos}\n      到昨天 RM{s0:,.0f} / {r0:.0f}（{'老将' if v0 else '非老将'}）→ 到今天 RM{s1:,.0f} / {r1:.0f}（{'老将' if v1 else '非老将'}）")
print("\nVET FLIP DONE (read-only)")
