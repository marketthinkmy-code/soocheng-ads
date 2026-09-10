# -*- coding: utf-8 -*-
"""Owner 2026-09-10:「新加坡的也建」— SG twin of the 0910 1-4-4 build.

  Campaign «[SG] STOCKBLOOM | BROAD SG 25+ | 0910 重拍» — ABO, 4 ad sets ×
  RM50/day PAUSED («Broad SG 25+»), 1 ad each, SG regulated-category fields.
  Same 4 creatives: image uploaded fresh to the SG account; the 3 重拍 videos
  reuse the already-approved posts (resolved from the SG account's own ads).
  Broad scaffold «BROAD | 1-1-3 B». Idempotent. Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time
from pathlib import Path

from adbot import cpa
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 5000
N = cpa.norm

CAMP_NAME = "[SG] STOCKBLOOM | BROAD SG 25+ | 0910 重拍"
ASET_NAME = "Broad SG 25+"
SCAFFOLD = "BROAD | 1-1-3 B"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
IMG_FILE = "1QK843z3SQ0SxB8uJbGOb7-Xkd2BziHb6"

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

from execute_build_0910_144 import CAP_IMG  # noqa: E402  same owner-approved copy

REUSE = [
    ("重拍：Video 5：盖电脑，喂！", "重拍：video 5：盖电脑"),
    ("重拍：Video 6：我跟你讲！", "重拍：video 6：我跟你讲"),
    ("重拍：厌倦了等待", "重拍：厌倦了等待"),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-4-4 SG build · «{CAMP_NAME}» · 4 ad sets × RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    link = s.meta.lead_destination.link_url
    cta = {"type": s.meta.call_to_action or "SIGN_UP", "value": {"link": link}}

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
    tgt0.pop("custom_audiences", None)
    tgt0.pop("excluded_custom_audiences", None)
    tgt0.pop("flexible_spec", None)
    promo = sc.get("promoted_object") or {}
    print(f"scaffold ✓ «{(sc.get('name') or '')[:40]}» → broad (interests stripped)")

    pool = g._get_all(
        f"{acct}/ads",
        {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
         "limit": "500"})
    time.sleep(1.2)

    def resolve_post(frag):
        best = []
        for a in pool:
            if N(frag) not in N(a.get("name") or ""):
                continue
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            if post:
                bad = a.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED")
                act = a.get("effective_status") == "ACTIVE"
                best.append((0 if act else (2 if bad else 1), post))
        best.sort()
        return best[0][1] if best else None

    plan = [{"name": "Image：iPhone Duo 对比", "kind": "image"}]
    for disp, frag in REUSE:
        post = resolve_post(frag)
        if post:
            plan.append({"name": disp, "kind": "post", "post": post})
            print(f"   post ✓ «{disp}»  {post}")
        else:
            print(f"   ⛔ «{disp}» 无可用已过审 post — 这支跳过")

    if not CONFIRM:
        print(f"\n▶ would create campaign(ABO ACTIVE) + {len(plan)} × "
              f"[adset «{ASET_NAME}» RM50 PAUSED + ad ACTIVE] · SG regulated fields")
        print(f"   image ad: 上传 {IMG_FILE} · headline «{HEADLINE}» · link {link}")
        return

    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=s.meta.special_ad_categories,
            special_ad_category_country=["SG"], status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO, ACTIVE — ad set 全 PAUSED 才是闸门)")
        time.sleep(PACE)

    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}

    img_hash = None
    for t in plan:
        if N(t["name"]) in have:
            print(f"· «{t['name']}» 已在 — skip")
            continue
        aset = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
            targeting=_copy.deepcopy(tgt0), status="PAUSED",
            regional_regulated_categories=REGIONAL,
            regional_regulation_identities=REG_IDENTITIES)
        time.sleep(PACE)

        if t["kind"] == "image":
            if img_hash is None:
                drive = DriveClient(s.secrets.google_sa_json)
                p = drive.download_file(IMG_FILE, Path("/tmp/img_0910_sg.png"))
                img_hash = g.upload_image(acct, str(p))
                print(f"   ⬆ image uploaded hash={img_hash[:16]}…")
                time.sleep(PACE)
            spec = {"name": f"SG | 0910 | {t['name']}",
                    "object_story_spec": {
                        "page_id": s.meta.page_id,
                        "link_data": {"image_hash": img_hash, "link": link,
                                      "message": CAP_IMG, "name": HEADLINE,
                                      "call_to_action": cta}}}
        else:
            spec = {"name": f"SG | 0910 | {t['name']}",
                    "object_story_id": t["post"]}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=t["name"], adset_id=aset["id"],
                         creative={"creative_id": cr["id"]},
                         status="ACTIVE", conversion_domain=conv)
        print(f"✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{t['name']}»")
        time.sleep(PACE)

    print("\nBUILD 0910 1-4-4 SG DONE — 全部 ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
