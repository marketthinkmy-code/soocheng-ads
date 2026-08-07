# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-24): give MY GOLF a compliant engine.

SG GOLF's real winner is `video 5：trading 早就不是这样了！` (5 of its 6 paid buyers). Reuse
that exact page post (creative + copy as one proven unit, keeps social proof) as a NEW ad in
the MY GOLF PICKLEBALL 1-1-3 ad set — built PAUSED for review.

Does NOT touch `freestyle 2` (owner's call to leave it). Resolves the post id dynamically from
the live SG GOLF ad (no hardcoded id). Idempotent. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY = "act_759339046918885"
SG_GOLF_CAMP = "120248220643620521"    # [SG] STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3
MY_GOLF_CAMP = "120247525942340575"    # STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3
NAME_MATCH = "video 5"                 # the winning ad's name substring on SG GOLF
AD_NAME = "video 5：trading 早就不是这样了！"


def pick_adset(g, camp):
    adsets = g._get_all(f"{camp}/adsets", {"fields": "id,name,effective_status", "limit": "50"})
    if not adsets:
        return None
    active = [a for a in adsets if a.get("effective_status") == "ACTIVE"]
    return (active or adsets)[0]


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    # 1) resolve the winning post id from the live SG GOLF ad
    sg_ads = g._get_all(f"{SG_GOLF_CAMP}/ads",
                        {"fields": "id,name,creative{id,effective_object_story_id,object_story_id}",
                         "limit": "100"})
    v5 = [a for a in sg_ads if NAME_MATCH in (a.get("name") or "").lower()]
    if len(v5) != 1:
        raise SystemExit(f"Expected exactly 1 SG GOLF ad matching «{NAME_MATCH}», found {len(v5)}: "
                         f"{[a.get('name') for a in v5]}")
    src = v5[0]
    cr = src.get("creative") or {}
    post_id = cr.get("effective_object_story_id") or cr.get("object_story_id")
    if not post_id:
        raise SystemExit(f"SG GOLF ad «{src.get('name')}» has no object_story_id — cannot reuse as a post.")
    print(f"source SG ad {src['id']} «{src.get('name')}»  post_id={post_id}")

    # 2) target MY GOLF ad set
    aset = pick_adset(g, MY_GOLF_CAMP)
    if not aset:
        raise SystemExit("MY GOLF has no ad set.")
    print(f"target MY GOLF adset {aset['id']} «{aset.get('name')}» [{aset.get('effective_status')}]\n")

    present = {(a.get("name") or "") for a in
               g._get_all(f"{aset['id']}/ads", {"fields": "name", "limit": "200"})}
    if AD_NAME in present:
        print(f"· «{AD_NAME}» already in MY GOLF ad set — skip (nothing to do)")
        return

    if not CONFIRM:
        print(f"WOULD INJECT into MY GOLF adset {aset['id']}: ad «{AD_NAME}» from post {post_id} (PAUSED)")
        print("\nDRY-RUN — set CONFIRM=true to apply.")
        return

    spec = {"name": f"MY | {AD_NAME}", "object_story_id": post_id}
    if s.meta.url_tags:
        spec["url_tags"] = s.meta.url_tags
    creative = g.create_adcreative(MY, **spec)
    ad = g.create_ad(MY, name=AD_NAME, adset_id=aset["id"],
                     creative={"creative_id": creative["id"]}, status="PAUSED",
                     conversion_domain=s.meta.conversion_domain_bare or None)
    print(f"✓ injected ad {ad['id']} «{AD_NAME}» into MY GOLF adset {aset['id']} (PAUSED)")
    print("\nDONE — freestyle 2 left untouched; owner activates video 5 in Ads Manager.")


if __name__ == "__main__":
    main()
