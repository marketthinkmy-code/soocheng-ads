"""Surgical, explicitly-authorized pauses of NAMED entities (not a heuristic sweep).
Each id below was named/confirmed by the account owner. Logs to pause_log.json.
Run: python scripts/pause_named.py
"""
from __future__ import annotations

from adbot import state
from adbot.commands import graph_client
from adbot.settings import load_settings

# (entity_id, type, human label, reason, metrics) — each owner-authorized this turn.
TARGETS = [
    ("120245367223180688", "ad",
     "STOCKBLOOM #1 | Video 9：你不是不会赚，是赚了又还回去",
     "cpl_over_threshold", {"spend": 51.17, "results": 1, "cpl": 51.17}),
    ("120237949072030688", "adset",
     "MTC - Officer - 14/1/2026 | active ad set (high CPL)",
     "manual_user_request_high_cpl",
     {"spend": 726.52, "results": 12, "cpl": 60.54, "lifetime_cpl": 42.99}),
]


def main() -> None:
    g = graph_client(load_settings())
    for entity_id, etype, label, reason, metrics in TARGETS:
        before = g.get_object(entity_id, "effective_status").get("effective_status")
        if before != "ACTIVE":
            print(f"SKIP  {label}\n      already {before} (id={entity_id})")
            continue
        g.update_status(entity_id, "PAUSED")
        after = g.get_object(entity_id, "effective_status").get("effective_status")
        state.append_pause_log(entity_id, etype, reason, metrics)
        print(f"PAUSED {label}\n       {before} -> {after}  (id={entity_id}, reason={reason})")


if __name__ == "__main__":
    main()
