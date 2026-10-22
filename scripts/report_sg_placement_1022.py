# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: SG 0-reg day — spend / LPV / regs by placement and by country, 10/20 · 10/21 · 10/22,
SG vs MY. Answers: did delivery shift to junk placements or out-of-country?"""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CC = {"config.sg.yaml": "1614065190214320", "config.my5.yaml": "1048291251556714"}
for cfg, cc in CC.items():
    st = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(st)
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n######## {cfg}")
    for bd in ("publisher_platform,platform_position", "country", "device_platform"):
        print(f"  ── by {bd}")
        for d in ("2026-10-20", "2026-10-21", "2026-10-22"):
            rows = g._get_all(st.meta.account_path + "/insights", {
                "fields": "spend,inline_link_clicks,actions", "breakdowns": bd, "level": "account",
                "time_range": json.dumps({"since": d, "until": d}), "limit": "100"})
            rows = sorted(rows, key=lambda r: -float(r.get("spend") or 0))
            print(f"   {d}: " + " | ".join(
                f"{'/'.join(str(r.get(k, '')) for k in bd.split(','))} RM{float(r.get('spend') or 0):.0f} "
                f"clk{r.get('inline_link_clicks', 0)} LPV{extract_results(r.get('actions'), 'landing_page_view'):.0f} "
                f"reg{extract_results(r.get('actions'), tok):.0f}"
                for r in rows if float(r.get('spend') or 0) >= 3))
            time.sleep(1)
print("\nPLACEMENT DONE (read-only)")
