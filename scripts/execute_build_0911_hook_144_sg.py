# -*- coding: utf-8 -*-
"""Owner 2026-09-14:「帮我也建在 SG 那边」— SG twin of the 0911 HOOK 重拍 1-4-4.

  Campaign «[SG] STOCKBLOOM | BROAD SG 25+ | 0911 HOOK 重拍» — ABO, 4 ad sets ×
  RM50/day «Broad SG 25+» PAUSED (owner 审后自行开启), 1 video ad each, SG
  regulated fields (SINGAPORE_UNIVERSAL). No special ad category (owner untick).

  Videos + captions imported from the MY script — its VIDEOS list carries the
  owner-CORRECTED file↔hook pairing (HOOK 1=盖电脑 · 2=不选forex · 3=不用看盘 ·
  4=炒过那么多), so the SG build inherits the right pairing by construction.
  Videos are uploaded fresh to the SG account (video ids are per-account).

  Age rule (owner 2026-09-11「以後年齡放 30 開始」): broad scaffold is
  Advantage+ ON → set the suggestion range age_range [30, 55], matching what the
  owner set on the MY HOOK wave. Idempotent at (campaign, ad-name).
  Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time
from pathlib import Path

from adbot import cpa
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

from execute_build_0911_hook_144 import HEADLINE, VIDEOS  # noqa: E402  corrected pairing

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 5000                     # RM50/day per ad set
N = cpa.norm

CAMP_NAME = "[SG] STOCKBLOOM | BROAD SG 25+ | 0911 HOOK 重拍"
ASET_NAME = "Broad SG 25+"
SCAFFOLD = "BROAD | 1-1-3 B"
AGE_RANGE = [30, 55]             # match the MY HOOK wave the owner set by hand

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-4-4 HOOK SG build · «{CAMP_NAME}» · 4 ad sets × RM{DAILY/100:.0f}/day PAUSED — {mode}\n")
    print("配对（owner-corrected）：")
    for v in VIDEOS:
        print(f"   «{v['name']}»  ← drive {v['file'][:8]}…  caption={len(v['cap'])} chars")
    print()

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    link = s.meta.lead_destination.link_url

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1.2)
    sc_camp = next((c for c in camps if SCAFFOLD in (c.get("name") or "")), None)
    if not sc_camp:
        print(f"⛔ scaffold «{SCAFFOLD}» 找不到")
        return
    sc = (g._get_all(f"{sc_camp['id']}/adsets",
                     {"fields": "id,name,targeting,promoted_object", "limit": "5"})
          or [None])[0]
    time.sleep(1)
    tgt0 = _copy.deepcopy(sc.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences", "flexible_spec"):
        tgt0.pop(k, None)
    tgt0["age_range"] = AGE_RANGE          # Advantage+ 下的「建议 30 起」（CLAUDE.md 规则）
    promo = sc.get("promoted_object") or {}
    print(f"scaffold ✓ «{(sc.get('name') or '')[:40]}» → broad · age_range {AGE_RANGE}")

    if not CONFIRM:
        print(f"\n▶ would create campaign(ABO ACTIVE, special_ad_categories=[]) + 4 × "
              f"[adset «{ASET_NAME}» RM50 PAUSED (SG regulated) + 1 video ad ACTIVE]")
        return

    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=[], status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO ACTIVE, no special category — ad set 全 PAUSED 是闸门)")
        time.sleep(PACE)

    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
    drive = None
    for i, v in enumerate(VIDEOS):
        if N(v["name"]) in have:
            print(f"· «{v['name']}» 已在 — skip")
            continue
        aset = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
            targeting=_copy.deepcopy(tgt0), status="PAUSED",
            regional_regulated_categories=REGIONAL,
            regional_regulation_identities=REG_IDENTITIES)
        time.sleep(PACE)
        if drive is None:
            drive = DriveClient(s.secrets.google_sa_json)
        p = drive.download_file(v["file"], Path(f"/tmp/hook_sg_{i}.mp4"))
        vid = g.upload_video(acct, str(p), v["name"])
        time.sleep(PACE)
        thumb = g.get_video_thumbnail(vid)
        print(f"   ⬆ video {vid}  thumb={'✓' if thumb else '—'}")
        video_data = {"video_id": vid, "title": HEADLINE, "message": v["cap"],
                      "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                         "value": {"link": link}}}
        if thumb:
            video_data["image_url"] = thumb
        spec = {"name": f"SG | 0911 HOOK | {v['name']}",
                "object_story_spec": {"page_id": s.meta.page_id,
                                      "video_data": video_data}}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=v["name"], adset_id=aset["id"],
                         creative={"creative_id": cr["id"]},
                         status="ACTIVE", conversion_domain=conv)
        print(f"✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{v['name']}»")
        time.sleep(PACE)

    print("\nBUILD 0911 HOOK 1-4-4 SG DONE — 全部 ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
