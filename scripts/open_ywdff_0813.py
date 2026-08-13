# -*- coding: utf-8 -*-
"""Owner-approved 2026-08-13 («执行», step 2 of the plan): activate the single ad
«video 1：用我的方法» (120248256492180521) in [SG] STOCKBLOOM | INVESTMENT | 1-1-3.

The main run skipped it because the campaign read IN_PROCESS for a few seconds right
after its own +30% budget write — that transient state counts as active here.
Verify-then-write; idempotent; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD_ID = "120248256492180521"
NAME_SUB = "用我的方法"
CAMP_SUB = "investment"
OK_CAMP_STATUS = ("ACTIVE", "IN_PROCESS")


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Open 用我的方法 (SG INVESTMENT) — {mode}")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    ad = g.get_object(AD_ID, "name,effective_status,campaign{name,effective_status}")
    nm, st = ad.get("name", "?"), ad.get("effective_status", "?")
    camp = ad.get("campaign") or {}
    print(f"  «{nm}» status={st} · campaign «{camp.get('name')}» ({camp.get('effective_status')})")
    if cpa.norm(NAME_SUB) not in cpa.norm(nm) or CAMP_SUB not in cpa.norm(camp.get("name", "")):
        raise SystemExit("⛔ name/campaign verification failed — aborting")
    if camp.get("effective_status") not in OK_CAMP_STATUS:
        raise SystemExit(f"⛔ campaign status {camp.get('effective_status')} — aborting")
    if st == "ACTIVE":
        print("  ✓ already ACTIVE — nothing to do")
        return
    if not CONFIRM:
        print(f"  ▶ would ACTIVATE ad {AD_ID}")
        return
    g.update_status(AD_ID, "ACTIVE")
    time.sleep(3)
    after = g.get_object(AD_ID, "effective_status").get("effective_status")
    print(f"  ✅ ACTIVATED ad {AD_ID}  {st} -> {after}")


if __name__ == "__main__":
    main()
