"""Add the 3 best currently-running ads (by CPL + registrations, compliant) into the SG
RUNNING ad set (120248231846380521), reusing each ad's existing post id. PAUSED.
Idempotent (skips a post already present). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
DST = "act_893025326577600"
ADSET = "120248231846380521"      # [SG] STOCKBLOOM | RUNNING | 1-1

# picked from live CPL ranking on 3.0 (most registrations + good CPL + compliant)
ADS = [
    ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),  # CPL15.7 · 4 reg
    ("video 2：你敢吗？", "1001334883061622_122109020937286543"),               # CPL13.5 · 3 reg
    ("freestyle 1", "1001334883061622_122097411579286543"),                    # CPL12.2 · 3 reg
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None
    print(f"CONFIRM={CONFIRM}  adset={ADSET}\n")

    have = set()
    for ad in g._get_all(f"{ADSET}/ads", {
            "fields": "creative{effective_object_story_id,object_story_id}", "limit": "50"}):
        cr = ad.get("creative") or {}
        have.add(cr.get("effective_object_story_id") or cr.get("object_story_id"))
    print(f"ad set already has {len(have)} ad(s)\n")

    added = 0
    for name, osid in ADS:
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
        ad = g.create_ad(DST, name=name, adset_id=ADSET,
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"  ✓ ADDED AD {ad['id']}  {name}")
        added += 1

    print(f"\nDONE — {'added' if CONFIRM else 'planned'} {added} ad(s) into RUNNING ad set (PAUSED).")


if __name__ == "__main__":
    main()
