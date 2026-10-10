# -*- coding: utf-8 -*-
"""owner 2026-10-10「Broad MY 放回 RM100」: restore the MY 5.0 «BROAD MY 30+» campaign CBO that the
monitor cut RM100 → RM70 on 2026-10-09 15:32 SGT (first over-CPL breach of the Thu-week, korea @ Broad
CPL 67 > RM60; it has since recovered to CPL 44). Budget only — the ADBOT_CPL30_ soft-reduce label
stays, so a second breach this Thu-week still pauses the breaching ad per the 9/10 rule.
CONFIRM=true writes; otherwise dry-run. Refuses unless the campaign is currently exactly RM70. No PII."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
CAMPAIGN_ID = "120251329174460329"          # [MY] STOCKBLOOM | BROAD MY 30+ | 1-1-5 | 1008
EXPECT_CENTS, TARGET_CENTS = 7000, 10000


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    camp = g.get_object(CAMPAIGN_ID, "name,status,effective_status,daily_budget,adlabels")
    name = camp.get("name") or ""
    cents = int(camp.get("daily_budget") or 0)
    labels = [l.get("name") for l in ((camp.get("adlabels") or {}).get("data") or [])
              if isinstance(camp.get("adlabels"), dict)] or \
             [l.get("name") for l in (camp.get("adlabels") or []) if isinstance(l, dict)]
    print(f"campaign «{name}» {camp.get('status')} / eff {camp.get('effective_status')} / CBO RM{cents / 100:.0f}")
    print(f"  labels: {labels}")
    assert "BROAD MY" in name.upper(), f"unexpected campaign: {name}"
    if cents == TARGET_CENTS:
        print("\nalready RM100 — nothing to do")
        print("RESTORE BROAD MY DONE (no-op)")
        return
    assert cents == EXPECT_CENTS, f"expected RM70 (monitor's cut), found RM{cents / 100:.0f} — someone changed it; stopping"
    if not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才会把 CBO RM{cents / 100:.0f} → RM{TARGET_CENTS / 100:.0f}。")
        print("RESTORE BROAD MY DONE (dry-run)")
        return
    g.update_daily_budget(CAMPAIGN_ID, TARGET_CENTS)
    time.sleep(3.0)
    after = g.get_object(CAMPAIGN_ID, "name,daily_budget,status")
    print(f"\n✅ «{after.get('name')}» CBO → RM{int(after.get('daily_budget') or 0) / 100:.0f} ({after.get('status')})")
    print("RESTORE BROAD MY DONE")


if __name__ == "__main__":
    main()
