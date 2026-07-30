# -*- coding: utf-8 -*-
"""Owner decision 2026-07-30:「video 12 不能，还是禁跑吧」— re-list video 12 炒过那么多.

The TOP3 resubmission passed review, but the same-day fresh copies in BEER ALCOHOL /
DAY TRADING (both accounts) were REJECTED — the re-list trigger fired.

This script (idempotent, dry-run unless CONFIRM=true):
  1. finds every video-12 ad in the BEER ALCOHOL / DAY TRADING campaigns and switches the
     rejected ones OFF (PAUSED) — they can't deliver anyway; leaving rejected ads toggled-on
     only adds negative weight on a repeat-offender account. Reversible, never deletes.
  2. read-only reports the TRAVEL TOP3 video-12 instances (approved ones stay running under
     the owner's CPL/CPA rule — untouched here).
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ACCTS = [("SG", "act_893025326577600"), ("MY", "act_759339046918885")]
THEME_MARKERS = ("BEER ALCOHOL", "DAY TRADING")
TOP3_MARKER = "TRAVEL TOP3"
REJECTED = {"DISAPPROVED", "WITH_ISSUES"}


def v12(name: str) -> bool:
    return "炒过那么多" in (name or "")


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  re-list video 12: pause rejected copies in theme campaigns\n")

    for label, acct in ACCTS:
        camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
        theme = [c for c in camps if any(m in (c.get("name") or "") for m in THEME_MARKERS)]
        top3 = [c for c in camps if TOP3_MARKER in (c.get("name") or "")]

        for c in theme:
            for a in g._get_all(f"{c['id']}/ads",
                                {"fields": "id,name,status,effective_status", "limit": "50"}):
                if not v12(a.get("name")):
                    continue
                st = a.get("effective_status") or ""
                if st in REJECTED or a.get("status") == "ACTIVE":
                    if not CONFIRM:
                        print(f"  WOULD PAUSE [{label}] {c.get('name')[:38]}: ad {a['id']} ({st})")
                    else:
                        g.update_status(a["id"], "PAUSED")
                        print(f"  ✓ PAUSED [{label}] {c.get('name')[:38]}: ad {a['id']} (was {st})")
                else:
                    print(f"  · [{label}] {c.get('name')[:38]}: ad {a['id']} already {st} — skip")

        for c in top3:
            for a in g._get_all(f"{c['id']}/ads",
                                {"fields": "id,name,effective_status", "limit": "50"}):
                if v12(a.get("name")):
                    print(f"  ℹ️ TOP3 [{label}] {c.get('name')[:38]}: video 12 ad {a['id']} "
                          f"status={a.get('effective_status')} (approved instance — untouched)")

    print("\nDONE — rejected video-12 copies paused; TOP3 instances reported only."
          if CONFIRM else "\nDRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
