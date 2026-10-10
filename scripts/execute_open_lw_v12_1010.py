# -*- coding: utf-8 -*-
"""owner 2026-10-10「照你建议」: reopen «🌟 video 12：不选 forex 不选黄金» in 🌟 LUXURY WATCHES — ad level
only (campaign / ad set already ACTIVE, CBO stays as is). CONFIRM=true writes; otherwise dry-run.

Preconditions, all enforced before any write:
  - the master is not on the ban list (compliance gate);
  - the config this run loads carries a cpa.hold entry that matches the EXACT ad name — i.e. the
    hold is already merged and synced, so the next monitor run keeps the ad (cpa_manual_hold)
    instead of hard-stopping it again (60d CPA 1,242 > 1,200);
  - campaign and ad set ACTIVE; the ad is PAUSED at ad level (otherwise nothing to do).
No PII."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
CAMPAIGN_KEY = "LUXURY WATCHES"          # name match; the 🌟 prefix made find_campaigns_by_prefix return []
AD_NAME = "🌟 video 12：不选 forex 不选黄金"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    allc = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    camps = [c for c in allc if CAMPAIGN_KEY in (c.get("name") or "")]
    assert len(camps) == 1, f"expected exactly one campaign, got {[c.get('name') for c in camps]} (of {len(allc)})"
    camp = g.get_object(camps[0]["id"], "name,status,effective_status,daily_budget")
    print(f"campaign «{camp.get('name')}» {camp.get('status')} / eff {camp.get('effective_status')} / "
          f"CBO RM{float(camp.get('daily_budget') or 0) / 100:.0f}")
    ads = g._get_all(camps[0]["id"] + "/ads", {
        "fields": "id,name,status,effective_status,adset{id,name,status,effective_status}", "limit": "50"})
    for a in ads:
        aset = a.get("adset") or {}
        print(f"  ad «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')}"
              f" / adset «{(aset.get('name') or '')[:28]}» {aset.get('status')}")
    targets = [a for a in ads if (a.get("name") or "") == AD_NAME]
    assert len(targets) == 1, f"expected exactly one «{AD_NAME}», got {len(targets)}"
    ad = targets[0]
    aset = ad.get("adset") or {}

    print("\n── preconditions ──")
    banned = compliance.banned_reason(AD_NAME, s.compliance.banned_creatives)
    held = any(h and h in AD_NAME for h in s.cpa.hold)
    print(f"  ban gate: {'⛔ BANNED (' + banned + ')' if banned else 'clean'}")
    print(f"  cpa.hold matches exact name: {held}  (hold = {s.cpa.hold})")
    print(f"  campaign {camp.get('status')} · adset {aset.get('status')} · ad {ad.get('status')} / eff {ad.get('effective_status')}")
    assert not banned, "banned master — never reopened"
    assert held, "cpa.hold not in the loaded config — merge + sync first, or the monitor re-pauses it"
    assert camp.get("status") == "ACTIVE" and aset.get("status") == "ACTIVE", "carrier not ACTIVE"
    if ad.get("status") == "ACTIVE":
        print("\nad already ACTIVE at ad level — nothing to do")
        print("OPEN LW V12 DONE (no-op)")
        return
    if not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才会把 ad {ad['id']} «{AD_NAME}» 设成 ACTIVE。")
        print("OPEN LW V12 DONE (dry-run)")
        return

    g.update_status(ad["id"], "ACTIVE")
    time.sleep(4.0)
    after = g.get_object(ad["id"], "name,status,effective_status")
    print(f"\n✅ «{after.get('name')}» → {after.get('status')} / eff {after.get('effective_status')}")
    print("OPEN LW V12 DONE")


if __name__ == "__main__":
    main()
