# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-24 scale step 2 inputs: each step-1 carrier (+ SG WINNERS Travel · 盖电脑) — budget, monitor cut
labels this Thu-week, spend/reg 10/22 · 10/23 · since-10/17 cumulative, CPL; plus any ad not ACTIVE/PAUSED (review)."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

MY = {"BUSINESS OWNER": "120251454700150329", "DAY TRADING": "120251454713670329",
      "TRAVEL MY": "120251500767290329", "BROAD MY": "120251454704570329"}
SG = {"LAL 5%": "120249918198320521"}
SG_WIN, SG_WIN_SETS = "120249964890710521", {"Investment | SG 28+", "Travel | SG 28+"}
CC = {"config.my5.yaml": "1048291251556714", "config.sg.yaml": "1614065190214320"}


def row(g, oid, tok, tr):
    r = g._get_all(oid + "/insights", {"fields": "spend,actions", "time_range": json.dumps(tr)})
    r = r[0] if r else {}
    return float(r.get("spend") or 0), extract_results(r.get("actions"), tok)


def show(g, name, oid, tok, line):
    o = g.get_object(oid, "name,daily_budget,effective_status,adlabels")
    labels = [l.get("name") for l in (o.get("adlabels") or []) if isinstance(l, dict)]
    out = []
    for tr in ({"since": "2026-10-22", "until": "2026-10-22"}, {"since": "2026-10-23", "until": "2026-10-23"},
               {"since": "2026-10-17", "until": "2026-10-23"}):
        sp, rg = row(g, oid, tok, tr); time.sleep(0.4)
        out.append(f"RM{sp:.0f}/{rg:.0f}={sp / rg:.0f}" if rg else f"RM{sp:.0f}/0")
    print(f"  {name:<34} {o['effective_status']:<8} RM{int(o.get('daily_budget') or 0) // 100:<4} 线{line} · "
          f"10/22 {out[0]} · 10/23 {out[1]} · 累计 {out[2]} · labels {labels}")


for cfg, carriers, line in (("config.my5.yaml", MY, 60), ("config.sg.yaml", SG, 95)):
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    tok = f"offsite_conversion.custom.{CC[cfg]}"
    print(f"\n## {cfg}")
    for n, oid in carriers.items():
        show(g, n, oid, tok, line)
    if cfg == "config.sg.yaml":
        for s in g._get_all(SG_WIN + "/adsets", {"fields": "name,ads{name}", "limit": "20"}):
            if s["name"] in SG_WIN_SETS:
                ads = ",".join(a["name"] for a in (s.get("ads") or {}).get("data", []))
                show(g, f"WINNERS {s['name']} [{ads[:14]}]", s["id"], tok, line)
print("\nSTEP2 INPUT DONE (read-only)")
