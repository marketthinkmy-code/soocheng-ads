# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-04) small budget tilt, step 1 of 2:

  MY TRAVEL | 1-1-3 (the burning one, campaign 120247524817830575)  -30% (bite the
      RM119-CPL burn; step 2 on Thursday's weekly reset lands the total -RM100~150/day)
  [SG] GOLF PICKBLEBALL | 1-1-3   +up to 30%, capped +RM100/day (CPA-558 王牌 reopened)
  [SG] TRAVEL | 1-1-3 (2)         +up to 30%, capped +RM100/day (盖电脑 472 / 你没有本钱 710)

Targets are pinned by campaign ID (two MY TRAVEL campaigns exist — name matching is not
safe). Reads live daily_budget, prints current -> proposed, applies only on CONFIRM=true.
Each POST is isolated so one rejection (e.g. an account cap) never blocks the rest.
"""
from __future__ import annotations

import os

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")

# (label, config, campaign_id, expected name substring, pct delta, abs cap in cents|None)
TARGETS = [
    ("MY TRAVEL (burner)", "config.yaml", "120247524817830575", "TRAVEL | 1-1-3", -0.30, None),
    ("SG GOLF",            "config.sg.yaml", "120248220643620521", "GOLF", +0.30, 10000),
    ("SG TRAVEL (2)",      "config.sg.yaml", "120248220651820521", "TRAVEL | 1-1-3 (2)", +0.30, 10000),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Budget tilt step 1 — {mode}\n")
    clients: dict = {}
    for label, cfg, cid, name_sub, pct, cap in TARGETS:
        g = clients.setdefault(cfg, graph_client(load_settings(REPO_ROOT / "config" / cfg)))
        c = g.get_object(cid, "id,name,effective_status,daily_budget")
        name, st = c.get("name", "?"), c.get("effective_status", "?")
        cur = int(c.get("daily_budget") or 0)
        if name_sub not in name:
            print(f"⛔ SKIP {label}: id {cid} is '{name}' — expected '{name_sub}'")
            continue
        if cur <= 0:
            print(f"⛔ SKIP {label}: '{name}' has no campaign daily_budget (cur={cur}) — "
                  f"budget may sit at ad-set level; needs a manual look")
            continue
        delta = int(cur * pct)
        if cap is not None and abs(delta) > cap:
            delta = cap if delta > 0 else -cap
        new = cur + delta
        line = (f"{label}: {name} [{st}]  RM{cur / 100:,.0f} -> RM{new / 100:,.0f}/day "
                f"({'+' if delta >= 0 else ''}RM{delta / 100:,.0f})")
        if not CONFIRM:
            print(f"▶ would set  {line}")
            continue
        try:
            g._request("POST", cid, data={"daily_budget": new})
            after = int(g.get_object(cid, "daily_budget").get("daily_budget") or 0)
            print(f"✅ set  {line}  (verified RM{after / 100:,.0f})")
        except GraphError as e:
            print(f"❌ FAILED {label}: {e} — continuing with the rest")


if __name__ == "__main__":
    main()
