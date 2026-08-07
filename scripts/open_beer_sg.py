# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-07「開 BEER」): wake the SG BEER ALCOHOL campaign and its
un-banned 炒过那么多 copy — the zero-re-review path back for the July 8-sale creative.

Wake-set verified live: campaign-ACTIVE resumes only 早就不是这样了 (ad-active copy);
炒过那么多 is then activated explicitly. 盖电脑 / freestyle 1 in this campaign stay
ad-paused (not in scope). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")

CAMPAIGN = ("120248577877480521", "BEER ALCOHOL")
ALLOWED_WAKE = {"120248577951920521"}            # video 5：trading 早就不是这样了！
CHAO = ("120248577931520521", "炒过那么多", "beer")


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Open SG BEER — {mode}\n")
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))

    cid, name_sub = CAMPAIGN
    c = g.get_object(cid, "id,name,effective_status,daily_budget")
    name, st = c.get("name", "?"), c.get("effective_status", "?")
    if name_sub not in name:
        raise SystemExit(f"⛔ id {cid} is '{name}' — expected '{name_sub}'")
    ads = g._get_all(f"{cid}/ads", {"fields": "id,name,effective_status", "limit": 200})
    wake = {a["id"]: a.get("name", "?") for a in ads
            if a.get("effective_status") == "CAMPAIGN_PAUSED"}
    extra = set(wake) - ALLOWED_WAKE
    print(f"'{name}' [{st}] RM{int(c.get('daily_budget') or 0)/100:,.0f}/day — "
          f"campaign-ACTIVE wakes: {list(wake.values())}")
    if extra:
        raise SystemExit(f"⛔ unexpected wake-set: {sorted(extra)} — aborting")

    if st == "PAUSED":
        if CONFIRM:
            g.update_status(cid, "ACTIVE")
            after = g.get_object(cid, "effective_status").get("effective_status")
            print(f"✅ campaign ACTIVATED: {st} -> {after}")
        else:
            print("▶ would ACTIVATE campaign")
    elif st == "ACTIVE":
        print("✓ campaign already ACTIVE")
    else:
        print(f"⚠️ campaign effective_status={st} — not touching")

    ad_id, ad_sub, camp_sub = CHAO
    ad = g.get_object(ad_id, "id,name,effective_status,campaign{name}")
    aname, ast = ad.get("name", "?"), ad.get("effective_status", "?")
    acamp = (ad.get("campaign") or {}).get("name", "?")
    if ad_sub not in aname or camp_sub not in acamp.casefold():
        print(f"⛔ SKIP 炒过那么多: id {ad_id} is '{aname}' / '{acamp}'")
    elif ast == "ACTIVE":
        print(f"✓ 炒过那么多 already ACTIVE")
    elif ast not in ("PAUSED", "CAMPAIGN_PAUSED"):
        print(f"⚠️ SKIP 炒过那么多: effective_status={ast}（若为 DISAPPROVED 则无法投放，需 owner 决定是否重送审）")
    elif CONFIRM:
        try:
            g.update_status(ad_id, "ACTIVE")
            after = g.get_object(ad_id, "effective_status").get("effective_status")
            print(f"✅ 炒过那么多 ACTIVATED: {ast} -> {after}")
        except GraphError as e:
            print(f"❌ FAILED 炒过那么多: {e}")
    else:
        print(f"▶ would ACTIVATE 炒过那么多 [{ast}]")


if __name__ == "__main__":
    main()
