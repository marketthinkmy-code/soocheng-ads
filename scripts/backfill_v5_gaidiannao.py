# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-30): backfill the video-12 gap — restore 1-1-3.

video 12 炒过那么多 is re-listed 禁跑, leaving BEER ALCOHOL / DAY TRADING / TRAVEL TOP3
(SG + MY = 6 campaigns) each running only 2 ads. Inject `video 5：盖电脑，喂！` as the 3rd:
30d 8 buyers, 46 historical, and — unlike video 12 — it has passed EVERY fresh review across
both accounts (scale_apply / sg_copy_build / new-acct copies). New copies still re-enter
review; history says they pass, but that's Meta's call, not ours.

Same pattern as inject_golf_video5.py: resolve the post id dynamically from live ads
(creative + copy stay one proven unit, social proof kept), idempotent per ad set (skips if a
盖电脑 ad already exists), everything PAUSED — owner activates. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time
from collections import Counter

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5

ACCTS = [("SG", "act_893025326577600"), ("MY", "act_759339046918885")]
CAMP_MARKERS = ("BEER ALCOHOL", "DAY TRADING", "TRAVEL TOP3")
AD_NAME = "video 5：盖电脑，喂！"
MATCH = "盖电脑"
KNOWN_POST = "1001334883061622_1788611461813837"   # cross-check only; resolution is live


def resolve_post(g) -> str:
    """Pick the 盖电脑 post id from live ads (prefer ACTIVE instances); print every
    distinct id found so the dry-run eyeball catches a stray variant."""
    cands = []
    for label, acct in ACCTS:
        for a in g._get_all(f"{acct}/ads",
                            {"fields": "name,effective_status,"
                                       "creative{effective_object_story_id,object_story_id}",
                             "limit": "200"}):
            if MATCH not in (a.get("name") or ""):
                continue
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            if post:
                cands.append((a.get("effective_status") or "?", post, label))
    if not cands:
        raise SystemExit(f"‼️ no live ad matching «{MATCH}» on either account")
    by_id = Counter(p for _st, p, _l in cands)
    for pid, n in by_id.most_common():
        states = Counter(st for st, p, _l in cands if p == pid)
        print(f"  post {pid}  ×{n}  {dict(states)}")
    active = [p for st, p, _l in cands if st == "ACTIVE"]
    pick = active[0] if active else by_id.most_common(1)[0][0]
    if pick != KNOWN_POST:
        print(f"  ⚠️ resolved {pick} ≠ known {KNOWN_POST} — using the live-resolved one")
    print(f"  → using post {pick}")
    return pick


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  backfill «{AD_NAME}» into "
          f"{' / '.join(CAMP_MARKERS)} × SG+MY  ·  PAUSED\n")

    print("== resolve 盖电脑 post ==")
    post = resolve_post(g)
    conv = s.meta.conversion_domain_bare or None

    built = skipped = 0
    for label, acct in ACCTS:
        camps = [c for c in g._get_all(f"{acct}/campaigns",
                                       {"fields": "id,name", "limit": "500"})
                 if any(m in (c.get("name") or "") for m in CAMP_MARKERS)]
        print(f"\n══ {label}  {acct}  ({len(camps)} target campaigns) ══")
        if len(camps) != len(CAMP_MARKERS):
            print(f"  ⚠️ expected {len(CAMP_MARKERS)} campaigns, found "
                  f"{[c.get('name') for c in camps]}")
        for c in sorted(camps, key=lambda x: x.get("name") or ""):
            adsets = g._get_all(f"{c['id']}/adsets",
                                {"fields": "id,name,effective_status", "limit": "50"})
            if not adsets:
                print(f"  ‼️ {c.get('name')}: no ad set — skip")
                continue
            active = [a for a in adsets if a.get("effective_status") == "ACTIVE"]
            aset = (active or adsets)[0]
            roster = g._get_all(f"{aset['id']}/ads",
                                {"fields": "name,effective_status", "limit": "200"})
            names = ", ".join(f"«{a.get('name')}» {a.get('effective_status')}"
                              for a in roster) or "(empty)"
            print(f"  {c.get('name')}\n     adset {aset['id']}: {names}")
            if any(MATCH in (a.get("name") or "") for a in roster):
                print(f"     · already has a 盖电脑 ad — skip")
                skipped += 1
                continue
            if not CONFIRM:
                print(f"     WOULD ADD «{AD_NAME}» (PAUSED)")
                built += 1
                continue
            spec = {"name": f"{label} | {AD_NAME}", "object_story_id": post}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=AD_NAME, adset_id=aset["id"],
                             creative={"creative_id": cr["id"]}, status="PAUSED",
                             conversion_domain=conv)
            print(f"     ✓ ad {ad['id']}  «{AD_NAME}» (PAUSED)")
            built += 1
            time.sleep(PACE)

    verb = "added" if CONFIRM else "would add"
    print(f"\nSUMMARY: {verb} {built} · skipped {skipped} (already present)")
    print("DONE — PAUSED; owner activates in Ads Manager." if CONFIRM
          else "DRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
