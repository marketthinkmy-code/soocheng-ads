# -*- coding: utf-8 -*-
"""owner 2026-10-12「我想照你刚刚建议的做」— SG tonight, no budget changes:
  1. reopen 0905 «video 1：用我的方法» (ad → adset → campaign), ad set budget left as is (RM50);
     requires ban gate clean, cpa.hold present, every OTHER ad in that campaign PAUSED at ad level.
  2. add «HOOK：Video 12：不选 forex 不选黄金» to the LUXURY GOODS ad set by post reuse (the same page post
     the 0911 winner runs), created PAUSED so the owner flips it after review (SOP: never auto-activate).
Dry-run unless CONFIRM=true. No PII."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD_0905 = "video 1：用我的方法"
AD_WINNER = "HOOK：Video 12：不选 forex 不选黄金"


def rm(c) -> str:
    return f"RM{int(c or 0) / 100:.0f}"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    time.sleep(0.8)

    def find(key: str) -> dict:
        hits = [c for c in camps if key in (c.get("name") or "")]
        assert len(hits) == 1, f"{key}: expected 1 campaign, got {[c.get('name') for c in hits]}"
        return hits[0]

    # ── 1. 0905 reopen ─────────────────────────────────────────────────────────
    c = find("| 0905")
    sets = g._get_all(c["id"] + "/adsets", {"fields": "id,name,status,effective_status,daily_budget", "limit": "20"})
    ads = g._get_all(c["id"] + "/ads", {"fields": "id,name,status,effective_status,adset_id", "limit": "100"})
    time.sleep(0.8)
    print(f"1) 0905 «{c.get('name')}» campaign {c.get('status')} / eff {c.get('effective_status')}")
    for a in sets:
        print(f"   adset «{(a.get('name') or '')[:30]}» {a.get('status')} / {rm(a.get('daily_budget'))}")
    tgt = [a for a in ads if (a.get("name") or "") == AD_0905]
    assert len(tgt) == 1, f"0905: expected 1 «{AD_0905}», got {len(tgt)}"
    ad = tgt[0]
    aset = next(a for a in sets if a["id"] == ad.get("adset_id"))
    others = [a for a in ads if a["id"] != ad["id"] and a.get("status") == "ACTIVE"]
    banned = compliance.banned_reason(AD_0905, s.compliance.banned_creatives)
    held = any(h and h in AD_0905 for h in s.cpa.hold)
    print(f"   target «{AD_0905}» {ad.get('status')} / eff {ad.get('effective_status')} · ban {'⛔' if banned else 'clean'} · hold {held}")
    for a in others:
        print(f"   ⚠️ other ad ACTIVE at ad level: «{(a.get('name') or '')[:40]}»")
    assert not banned and held, "0905 preconditions failed"
    reopen = not others
    if not reopen:
        print("   ✗ other ads are ACTIVE at ad level — carriers NOT reactivated (owner to decide)")
    elif CONFIRM:
        if ad.get("status") != "ACTIVE":
            g.update_status(ad["id"], "ACTIVE"); time.sleep(0.8)
        if aset.get("status") != "ACTIVE":
            g.update_status(aset["id"], "ACTIVE"); time.sleep(0.8)
        if c.get("status") != "ACTIVE":
            g.update_status(c["id"], "ACTIVE"); time.sleep(0.8)
        print(f"   ✓ ad / adset / campaign → ACTIVE (adset budget stays {rm(aset.get('daily_budget'))})")
    else:
        print(f"   plan: ad → ACTIVE · adset → ACTIVE (budget stays {rm(aset.get('daily_budget'))}) · campaign → ACTIVE")

    # ── 2. LUXURY GOODS + winner post ─────────────────────────────────────────
    win_c = find("0911 HOOK")
    win_ads = g._get_all(win_c["id"] + "/ads", {"fields": "id,name,status,creative{id,effective_object_story_id}", "limit": "50"})
    time.sleep(0.8)
    win = [a for a in win_ads if (a.get("name") or "") == AD_WINNER and a.get("status") == "ACTIVE"]
    assert len(win) == 1, f"0911: expected 1 ACTIVE «{AD_WINNER}», got {len(win)}"
    post = (win[0].get("creative") or {}).get("effective_object_story_id")
    assert post, "winner has no effective_object_story_id"
    lg = find("LUXURY GOODS")
    lg_sets = [a for a in g._get_all(lg["id"] + "/adsets", {"fields": "id,name,status,daily_budget", "limit": "20"}) if a.get("status") == "ACTIVE"]
    lg_ads = g._get_all(lg["id"] + "/ads", {"fields": "id,name,status,effective_status", "limit": "50"})
    time.sleep(0.8)
    assert len(lg_sets) == 1, f"LUXURY GOODS: expected 1 ACTIVE ad set, got {len(lg_sets)}"
    print(f"\n2) LUXURY GOODS «{lg.get('name')}» CBO {rm(lg.get('daily_budget'))} · adset «{(lg_sets[0].get('name') or '')[:30]}»")
    for a in lg_ads:
        print(f"   ad «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')}")
    assert not compliance.banned_reason(AD_WINNER, s.compliance.banned_creatives), "winner banned?!"
    exists = [a for a in lg_ads if (a.get("name") or "") == AD_WINNER]
    print(f"   post to reuse: {post} (from 0911's «{AD_WINNER}»)")
    if exists:
        print(f"   · already has «{AD_WINNER}» ({exists[0].get('status')}) — nothing to create")
    elif CONFIRM:
        spec = {"name": f"SG | {AD_WINNER} @ LUXURY GOODS", "object_story_id": post}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        new = g.create_ad(acct, name=AD_WINNER, adset_id=lg_sets[0]["id"],
                          creative={"creative_id": cr["id"]}, status="PAUSED", conversion_domain=conv)
        print(f"   ✓ ad {new['id']} «{AD_WINNER}» created PAUSED in LUXURY GOODS (review runs; owner flips)")
    else:
        print(f"   plan: create «{AD_WINNER}» PAUSED in LUXURY GOODS via post reuse")

    if CONFIRM:
        time.sleep(5.0)
        print("\n── 验证 ──")
        c2 = g.get_object(c["id"], "name,status,effective_status")
        a2 = g.get_object(ad["id"], "name,status,effective_status")
        print(f"  0905 campaign {c2.get('status')} / eff {c2.get('effective_status')} · ad «{a2.get('name')}» {a2.get('status')} / eff {a2.get('effective_status')}")
        for a in g._get_all(lg["id"] + "/ads", {"fields": "id,name,status,effective_status", "limit": "50"}):
            print(f"  LUXURY GOODS ad «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')}")
    print("SG TONIGHT DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
