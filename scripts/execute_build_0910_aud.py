# -*- coding: utf-8 -*-
"""Owner 2026-09-10 (👌🏼 on the recommendation): second-audience wave for the
0910 重拍+图 creatives.

  MY: «STOCKBLOOM | LUXURY GOODS 30-55 | 0910 重拍»   scaffold LUXURY GOODS | 1-1-3
      (interests kept, age 30-55 attempted; special-ad-category may strip ages —
      same fallback as build_0905, reported honestly)
  SG: «[SG] STOCKBLOOM | PURCHASE LAL 1-5% | 0910 重拍» scaffold 🌟 PURCHASE LAL
      1-5% | 1-5-3 — custom_audiences KEPT (the LALs are the targeting)

  Each: ABO, 4 ad sets × RM50/day PAUSED, 1 ad each — Image：iPhone Duo 对比
  (re-upload per account; same bytes → same hash) + 3 重拍 posts reused from the
  account's own approved instances. Idempotent. Dry-run unless CONFIRM=true."""
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
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
IMG_FILE = "1QK843z3SQ0SxB8uJbGOb7-Xkd2BziHb6"

from execute_build_0910_144 import CAP_IMG  # noqa: E402

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

REUSE = [
    ("重拍：Video 5：盖电脑，喂！", "重拍：video 5：盖电脑"),
    ("重拍：Video 6：我跟你讲！", "重拍：video 6：我跟你讲"),
    ("重拍：厌倦了等待", "重拍：厌倦了等待"),
]

SPECS = [
    {"label": "MY", "cfg": "config.yaml", "sg": False, "geo": ["MY"],
     "camp": "STOCKBLOOM | LUXURY GOODS 30-55 | 0910 重拍",
     "aset": "Luxury Goods 30-55", "scaffold": "LUXURY GOODS | 1-1-3",
     "age": (30, 55), "keep_custom": False},
    {"label": "SG", "cfg": "config.sg.yaml", "sg": True, "geo": ["SG"],
     "camp": "[SG] STOCKBLOOM | PURCHASE LAL 1-5% | 0910 重拍",
     "aset": "Purchase LAL 1-5%", "scaffold": "PURCHASE LAL 1-5%",
     "age": None, "keep_custom": True},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"0910 第二受众波 · MY Luxury + SG LAL · 各 4 ad sets × RM50 PAUSED — {mode}\n")

    for spec in SPECS:
        s = load_settings(REPO_ROOT / "config" / spec["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        link = s.meta.lead_destination.link_url
        cta = {"type": s.meta.call_to_action or "SIGN_UP", "value": {"link": link}}
        print(f"══ [{spec['label']}] {spec['camp']} ══")
        try:
            camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
            time.sleep(1.2)
            sc_camp = next((c for c in camps
                            if spec["scaffold"] in (c.get("name") or "")), None)
            if not sc_camp:
                print(f"  ⛔ scaffold «{spec['scaffold']}» 找不到 — 跳过\n")
                continue
            sc_all = g._get_all(f"{sc_camp['id']}/adsets",
                                {"fields": "id,name,targeting,promoted_object",
                                 "limit": "25"})
            time.sleep(1)
            sc = sc_all[0]
            tgt0 = _copy.deepcopy(sc.get("targeting") or {})
            if not spec["keep_custom"]:
                tgt0.pop("custom_audiences", None)
            else:
                # LAL 阶梯：把 scaffold campaign 里所有格的 custom_audiences
                # union 去重 → 一个真正的 1-5% 受众
                seen, merged = set(), []
                for a in sc_all:
                    for ca in ((a.get("targeting") or {}).get("custom_audiences") or []):
                        if ca.get("id") and ca["id"] not in seen:
                            seen.add(ca["id"])
                            merged.append({"id": ca["id"]})
                tgt0["custom_audiences"] = merged
            tgt0.pop("excluded_custom_audiences", None)
            if spec["age"]:
                tgt0["age_min"], tgt0["age_max"] = spec["age"]
            promo = sc.get("promoted_object") or {}
            n_cust = len(tgt0.get("custom_audiences") or [])
            print(f"  scaffold ✓ «{(sc.get('name') or '')[:44]}» "
                  f"(custom_audiences kept: {n_cust})")

            pool = g._get_all(
                f"{acct}/ads",
                {"fields": "name,effective_status,"
                           "creative{effective_object_story_id,object_story_id}",
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
                    print(f"     post ✓ «{disp}»")
                else:
                    print(f"     ⛔ «{disp}» 无可用 post — 跳过这支")

            if not CONFIRM:
                print(f"  ▶ would create campaign(ABO ACTIVE) + {len(plan)} × "
                      f"[adset «{spec['aset']}» RM50 PAUSED + ad]\n")
                continue

            camp_id = next((c["id"] for c in camps
                            if (c.get("name") or "") == spec["camp"]), None)
            if camp_id:
                print(f"  · campaign exists ({camp_id}) — filling gaps")
            else:
                camp = g.create_campaign(
                    acct, name=spec["camp"], objective="OUTCOME_SALES",
                    buying_type="AUCTION", is_adset_budget_sharing_enabled="false",
                    special_ad_categories=s.meta.special_ad_categories,
                    special_ad_category_country=spec["geo"], status="ACTIVE")
                camp_id = camp["id"]
                print(f"  ✓ campaign {camp_id}")
                time.sleep(PACE)

            have = {N(a.get("name") or "") for a in g._get_all(
                f"{camp_id}/ads", {"fields": "name", "limit": "50"})}

            img_hash = None
            for t in plan:
                if N(t["name"]) in have:
                    print(f"  · «{t['name']}» 已在 — skip")
                    continue
                tgt = _copy.deepcopy(tgt0)
                kw = dict(name=spec["aset"], campaign_id=camp_id, daily_budget=DAILY,
                          optimization_goal="OFFSITE_CONVERSIONS",
                          billing_event="IMPRESSIONS",
                          bid_strategy="LOWEST_COST_WITHOUT_CAP",
                          promoted_object=promo, targeting=tgt, status="PAUSED")
                if spec["sg"]:
                    kw.update(regional_regulated_categories=REGIONAL,
                              regional_regulation_identities=REG_IDENTITIES)
                try:
                    aset = g.create_adset(acct, **kw)
                except Exception as e:
                    low = str(e).lower()
                    if "age" in low and "bid" not in low and "age_min" in tgt:
                        print("  ⚠️ 特殊广告类别拒绝年龄限制 — 去掉 30-55 重试")
                        tgt.pop("age_min", None)
                        tgt.pop("age_max", None)
                        kw["targeting"] = tgt
                        aset = g.create_adset(acct, **kw)
                    else:
                        raise
                time.sleep(PACE)

                if t["kind"] == "image":
                    if img_hash is None:
                        drive = DriveClient(s.secrets.google_sa_json)
                        p = drive.download_file(
                            IMG_FILE, Path(f"/tmp/img_0910_{spec['label']}.png"))
                        img_hash = g.upload_image(acct, str(p))
                        time.sleep(PACE)
                    cr_spec = {"name": f"{spec['label']} | 0910 {spec['aset']} | {t['name']}",
                               "object_story_spec": {
                                   "page_id": s.meta.page_id,
                                   "link_data": {"image_hash": img_hash, "link": link,
                                                 "message": CAP_IMG, "name": HEADLINE,
                                                 "call_to_action": cta}}}
                else:
                    cr_spec = {"name": f"{spec['label']} | 0910 {spec['aset']} | {t['name']}",
                               "object_story_id": t["post"]}
                if s.meta.url_tags:
                    cr_spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **cr_spec)
                ad = g.create_ad(acct, name=t["name"], adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]},
                                 status="ACTIVE", conversion_domain=conv)
                print(f"  ✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{t['name']}»")
                time.sleep(PACE)
        except Exception as e:
            print(f"  ❌ {str(e)[:140]} — continuing")
        print()

    print("BUILD 0910 AUD DONE — 全部 PAUSED，owner 审后自行开启。"
          if CONFIRM else "DRY-RUN — 核对后 confirm=true。")


if __name__ == "__main__":
    main()
