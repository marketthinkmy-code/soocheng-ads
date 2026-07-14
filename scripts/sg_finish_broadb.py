"""Finish the SG clone: add BROAD B's missing ads to the owner's existing ad set.
The main build created the other 4 campaigns successfully but hit the ad-account rate
limit at BROAD B. This is a tiny, idempotent top-up (only adds ads not already present).
Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
DST = "act_893025326577600"
BROADB_CAMP_NAME = "[SG] STOCKBLOOM | BROAD | 1-1-3 B"
BROADB_ADS = [
    ("video 2：你敢吗？", "1001334883061622_122109020937286543"),
    ("freestyle 1", "1001334883061622_122097411579286543"),          # owner already added
    ("video 6：街头突击采访！", "1001334883061622_122108595957286543"),
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None
    print(f"CONFIRM={CONFIRM}\n")

    camps = g._get_all(f"{DST}/campaigns", {"fields": "id,name", "limit": "200"})
    bc = [c for c in camps if c.get("name") == BROADB_CAMP_NAME]
    if not bc:
        print(f"⚠ campaign '{BROADB_CAMP_NAME}' not found"); return
    aset = g._get_all(f"{bc[0]['id']}/adsets", {"fields": "id,name", "limit": "5"})[0]
    asid = aset["id"]
    have = set()
    for ad in g._get_all(f"{asid}/ads", {
            "fields": "creative{effective_object_story_id,object_story_id}", "limit": "50"}):
        cr = ad.get("creative") or {}
        have.add(cr.get("effective_object_story_id") or cr.get("object_story_id"))
    print(f"campaign {bc[0]['id']} · adset {asid} · already has {len(have)} ad(s)\n")

    added = 0
    for name, osid in BROADB_ADS:
        if osid in have:
            print(f"  · keep existing: {name}")
            continue
        if not CONFIRM:
            print(f"  WOULD ADD  {name}  (post {osid})")
            added += 1
            continue
        spec = {"name": f"SG | {name}", "object_story_id": osid}
        if url_tags:
            spec["url_tags"] = url_tags
        cr = g.create_adcreative(DST, **spec)
        ad = g.create_ad(DST, name=name, adset_id=asid,
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"  ✓ ADDED AD {ad['id']}  {name}")
        added += 1

    print(f"\nDONE — {'added' if CONFIRM else 'planned'} {added} ad(s) to BROAD B (PAUSED).")


if __name__ == "__main__":
    main()
