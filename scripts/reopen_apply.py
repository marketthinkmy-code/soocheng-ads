# -*- coding: utf-8 -*-
"""Reactivate the owner-approved mis-killed ads from the 2026-08-04 reopen review.

Owner directive 2026-08-04:「全部聽你的，執行」on the reopen list — 8 ads across MY + SG
that sit paused with real 60d sales at CPA under the hard stop (see reopen_review.py,
ops run #88). Surgical and explicitly-authorized like pause_named.py, in reverse:
verify each ad's name/campaign/status first, then set status=ACTIVE. The CPL monitor's
CPA rescue keeps protecting these afterwards (real sales ≤ hard-stop never CPL-pause).

Dry-run by default; CONFIRM=true (the adbot-ops `confirm` input) applies the writes.
"""
from __future__ import annotations

import os

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")

# (ad_id or None, expected ad-name substring, expected campaign substring) — ids from
# reopen_review run #88; video 12 不选 forex has no id there (was mis-filtered), so it
# resolves by name + campaign on the account instead.
TARGETS = {
    "MY": ("config.yaml", [
        ("120247585354180575", "你敢吗", "business"),
        ("120247524817870575", "你没有本钱", "travel"),
        (None, "video 12：不选 forex 不选黄金", "luxury"),
    ]),
    "SG": ("config.sg.yaml", [
        ("120248197444110521", "freestyle 1", "broad"),
        ("120248220656790521", "盖电脑", "travel"),
        ("120248220645830521", "trading 早就不是这样了", "golf"),
        ("120248220653470521", "你没有本钱", "travel"),
        ("120248256492180521", "用我的方法", "invest"),
    ]),
}
FIELDS = "id,name,effective_status,adset{effective_status},campaign{name,effective_status}"


def resolve_by_name(g, acct: str, name_sub: str, camp_sub: str):
    """Find the single paused ad matching name+campaign substrings; None if ambiguous."""
    ads = g._get_all(f"{acct}/ads", {"fields": "id,name,effective_status,campaign{name}",
                                    "limit": 200})
    hits = [a for a in ads
            if cpa.norm(name_sub) in cpa.norm(a.get("name", ""))
            and camp_sub in cpa.norm((a.get("campaign") or {}).get("name", ""))
            and a.get("effective_status") != "ACTIVE"]
    if len(hits) == 1:
        return hits[0]["id"]
    print(f"   ⚠️ resolve '{name_sub}' × '{camp_sub}': {len(hits)} matches "
          f"({[h['id'] for h in hits]}) — skipping, needs a manual id")
    return None


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Reopen apply — {mode}\n")
    activated = skipped = 0
    for label, (cfg, targets) in TARGETS.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        print(f"═══ [{label}] {s.meta.account_path} ═══")
        for ad_id, name_sub, camp_sub in targets:
            if ad_id is None:
                ad_id = resolve_by_name(g, s.meta.account_path, name_sub, camp_sub)
                if ad_id is None:
                    skipped += 1
                    continue
            ad = g.get_object(ad_id, FIELDS)
            name, st = ad.get("name", "?"), ad.get("effective_status", "?")
            camp = (ad.get("campaign") or {})
            aset_st = (ad.get("adset") or {}).get("effective_status", "?")
            ok_name = cpa.norm(name_sub) in cpa.norm(name)
            ok_camp = camp_sub in cpa.norm(camp.get("name", ""))
            head = f"{name} ({camp.get('name', '?')})"
            if not (ok_name and ok_camp):
                print(f"   ⛔ SKIP {head} — id {ad_id} doesn't match expected "
                      f"'{name_sub}'/'{camp_sub}'")
                skipped += 1
                continue
            if st == "ACTIVE":
                print(f"   ✓ already ACTIVE: {head}")
                continue
            if st not in ("PAUSED",):
                print(f"   ⚠️ SKIP {head} — effective_status={st} (adset={aset_st}, "
                      f"campaign={camp.get('effective_status', '?')}) — not a plain ad-level pause")
                skipped += 1
                continue
            if not CONFIRM:
                print(f"   ▶ would ACTIVATE {head}  [ad {ad_id}]")
                activated += 1
                continue
            g.update_status(ad_id, "ACTIVE")
            after = g.get_object(ad_id, "effective_status").get("effective_status")
            print(f"   ✅ ACTIVATED {head}  {st} -> {after}  [ad {ad_id}]")
            activated += 1
    verb = "activated" if CONFIRM else "would activate"
    print(f"\nDone: {verb} {activated} · skipped {skipped}")


if __name__ == "__main__":
    main()
