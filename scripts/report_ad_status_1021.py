# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-21: status of every ad in the Webinarkit campaigns (MY 5.0 + SG) — who is live, who is off."""
from __future__ import annotations

import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

PLAN = {
    "config.my5.yaml": ["120251454680840329", "120251454704570329", "120251454700150329", "120251454713670329", "120251500767290329"],
    "config.sg.yaml": ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521", "120249964890710521"],
}


def main() -> None:
    for cfg, camps in PLAN.items():
        g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
        print(f"\n######## {cfg}")
        for cid in camps:
            c = g.get_object(cid, "name,effective_status,daily_budget")
            print(f"\n «{c['name'][13:60]}» {c['effective_status']} RM{int(c.get('daily_budget') or 0) // 100}")
            for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,daily_budget}", "limit": "30"}):
                s = a.get("adset") or {}
                print(f"   {s.get('name', '')[:20]:<20} RM{int(s.get('daily_budget') or 0) // 100:<3} {a['name'][:28]:<28} {a['status']:<8} {a['effective_status']}")
            time.sleep(1)
    print("\nSTATUS DONE (read-only)")


if __name__ == "__main__":
    main()
