# -*- coding: utf-8 -*-
"""Finish the 2026-08-04 reopen: three parent campaigns are paused at CAMPAIGN level,
so 4 of the 8 reactivated ads still don't deliver. Activate exactly those campaigns —
after proving the wake-set (ads with effective_status=CAMPAIGN_PAUSED, i.e. ad-ACTIVE
under a paused campaign) matches the expected allowlist, so nothing else slips live.

MY LUXURY carries RM320/day; it gets cut to RM100/day BEFORE activation so the reopen
never fights the owner-approved MY->SG tilt. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")

# (label, config, campaign_id, name substring, allowed wake-set ad ids, new budget cents|None)
TARGETS = [
    ("SG TRAVEL (2)", "config.sg.yaml", "120248220651820521", "TRAVEL | 1-1-3 (2)",
     {"120248220653470521", "120248220656790521"}, None),
    ("SG BROAD B", "config.sg.yaml", "120248197444090521", "BROAD | 1-1-3 B",
     {"120248197444110521"}, None),
    ("MY LUXURY", "config.yaml", "120247585340620575", "LUXURY GOODS | 1-1-3",
     {"120247585343380575", "120247677652860575"}, 10000),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Reopen finish (campaign layer) — {mode}\n")
    clients: dict = {}
    for label, cfg, cid, name_sub, allowed, new_budget in TARGETS:
        g = clients.setdefault(cfg, graph_client(load_settings(REPO_ROOT / "config" / cfg)))
        c = g.get_object(cid, "id,name,effective_status,daily_budget")
        name, st = c.get("name", "?"), c.get("effective_status", "?")
        cur_b = int(c.get("daily_budget") or 0)
        if name_sub not in name:
            print(f"⛔ SKIP {label}: id {cid} is '{name}' — expected '{name_sub}'")
            continue
        if st == "ACTIVE":
            print(f"✓ {label}: '{name}' already ACTIVE")
            continue
        if st != "PAUSED":
            print(f"⚠️ SKIP {label}: '{name}' effective_status={st}")
            continue
        ads = g._get_all(f"{cid}/ads", {"fields": "id,name,effective_status", "limit": 200})
        wake = {a["id"]: a.get("name", "?") for a in ads
                if a.get("effective_status") == "CAMPAIGN_PAUSED"}
        extra = set(wake) - allowed
        print(f"{label}: '{name}' [{st}] RM{cur_b / 100:,.0f}/day — would wake "
              f"{len(wake)} ad(s): " + "; ".join(wake.values()))
        if extra:
            print(f"   ⛔ SKIP — unexpected ads would wake: {sorted(extra)}")
            continue
        if not CONFIRM:
            if new_budget:
                print(f"   ▶ would set budget RM{cur_b / 100:,.0f} -> RM{new_budget / 100:,.0f}/day, then ACTIVATE")
            else:
                print("   ▶ would ACTIVATE")
            continue
        try:
            if new_budget:
                g._request("POST", cid, data={"daily_budget": new_budget})
            g.update_status(cid, "ACTIVE")
            after = g.get_object(cid, "effective_status,daily_budget")
            print(f"   ✅ ACTIVATED — now {after.get('effective_status')} "
                  f"RM{int(after.get('daily_budget') or 0) / 100:,.0f}/day")
        except GraphError as e:
            print(f"   ❌ FAILED: {e} — continuing")


if __name__ == "__main__":
    main()
