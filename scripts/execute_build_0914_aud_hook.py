# -*- coding: utf-8 -*-
"""Owner 2026-09-14「建」— the 4 HOOK creatives into two MY interest audiences:

  «STOCKBLOOM | DAY TRADING 30-55 | 0914 HOOK 重拍»   — DT interests cloned from
      the converting 🌟 DAY TRADING | 1-1-3 (DT Control) ad set.
  «STOCKBLOOM | BEER ALCOHOL 30-55 | 0914 HOOK 重拍»  — Beer/Alcohol interests
      cloned from the SG BEER campaign (the proven winner audience), geo → MY.

  Each: ABO, 4 ad sets × RM50/day PAUSED, 1 ad each REUSING the already-approved
  MY HOOK posts (zero re-review on this repeat-offender account; captions ride
  with the post, so the owner-corrected pairing is inherited from the live ads).
  Hard audience: advantage_audience=0 · age 30-55 hard (age_range stripped).
  No special ad category. Idempotent at (campaign, ad-name). Dry-run unless
  CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 5000
N = cpa.norm

HOOK_CAMP = "120248807549960575"        # MY 0911 HOOK 重拍 — holds the 4 approved posts
DT_SCAFFOLD = "DAY TRADING | 1-1-3"     # 🌟 DT Control — proven DT interest set
BEER_SG_FRAG = "BEER"                   # SG BEER campaign — proven winner interests

HOOKS = [
    "HOOK：Video 5：盖电脑，喂！",
    "HOOK：Video 12：不选 forex 不选黄金",
    "HOOK：Video 8：做么你 Trading 不用看盘的？",
    "HOOK：Video 12：炒过那么多，累而且不稳定",
]

BUILDS = [
    ("STOCKBLOOM | DAY TRADING 30-55 | 0914 HOOK 重拍", "Day Trading MY 30-55", "DT"),
    ("STOCKBLOOM | BEER ALCOHOL 30-55 | 0914 HOOK 重拍", "Beer Alcohol MY 30-55", "BEER"),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"0914 HOOK × 兴趣受众 · DT + BEER · 各 1-4-4 RM50 PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None

    # 1) the four approved posts (captions baked in — owner-corrected pairing)
    src_ads = g._get_all(
        f"{HOOK_CAMP}/ads",
        {"fields": "name,effective_status,"
                   "creative{effective_object_story_id,object_story_id}",
         "limit": "25"})
    time.sleep(1)
    posts = {}
    for want in HOOKS:
        hit = [a for a in src_ads if N(want) == N(a.get("name") or "")]
        if len(hit) != 1:
            print(f"⛔ post «{want}» 匹配 {len(hit)} — 停")
            return
        cr = hit[0].get("creative") or {}
        post = cr.get("effective_object_story_id") or cr.get("object_story_id")
        if not post:
            print(f"⛔ «{want}» 无 post id — 停")
            return
        posts[want] = post
        print(f"post ✓ «{want[:34]}»  {post}")

    # 2) DT base targeting (geo MY + locales + DT interests) from the DT Control ad set
    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1)
    dt_camp = next((c for c in camps if DT_SCAFFOLD in (c.get("name") or "")), None)
    if not dt_camp:
        print(f"⛔ DT scaffold «{DT_SCAFFOLD}» 找不到")
        return
    sc = (g._get_all(f"{dt_camp['id']}/adsets",
                     {"fields": "id,name,targeting,promoted_object", "limit": "5"})
          or [None])[0]
    time.sleep(1)
    base = _copy.deepcopy(sc.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences",
              "age_range", "targeting_relaxation_types"):
        base.pop(k, None)
    base["age_min"], base["age_max"] = 30, 55
    base["targeting_automation"] = {"advantage_audience": 0}   # 硬锁
    dt_flex = _copy.deepcopy(base.get("flexible_spec") or [])
    promo = sc.get("promoted_object") or {}
    n_dt = sum(len(fs.get("interests") or []) for fs in dt_flex)
    print(f"DT targeting ✓ interests×{n_dt} · geo {(base.get('geo_locations') or {}).get('countries')}"
          f" · locales {base.get('locales')} · 30-55 hard")

    # 3) BEER interests from the SG BEER campaign (geo/base stays MY)
    s_sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g_sg = graph_client(s_sg)
    sg_camps = g_sg._get_all(f"{s_sg.meta.account_path}/campaigns",
                             {"fields": "id,name", "limit": "500"})
    time.sleep(1)
    beer_camp = next((c for c in sg_camps if BEER_SG_FRAG in (c.get("name") or "").upper()), None)
    beer_flex = None
    if beer_camp:
        for a in g_sg._get_all(f"{beer_camp['id']}/adsets",
                               {"fields": "id,name,targeting", "limit": "5"}):
            fs = (a.get("targeting") or {}).get("flexible_spec")
            if fs and any(x.get("interests") for x in fs):
                beer_flex = _copy.deepcopy(fs)
                break
    if not beer_flex:
        print("⛔ SG BEER 兴趣抄不到 — 停（不猜）")
        return
    n_beer = sum(len(fs.get("interests") or []) for fs in beer_flex)
    beer_names = [i.get("name") for fs in beer_flex for i in (fs.get("interests") or [])]
    print(f"BEER interests ✓ ×{n_beer} 从 «{(beer_camp.get('name') or '')[:36]}»: "
          f"{'、'.join((x or '?')[:16] for x in beer_names[:6])}")

    tgts = {"DT": dt_flex, "BEER": beer_flex}
    if not CONFIRM:
        print(f"\n▶ would create 2 campaigns(ABO ACTIVE, special=[]) × 4 × "
              f"[adset RM50 PAUSED (硬锁兴趣, 30-55) + post-reuse ad ACTIVE]")
        return

    for camp_name, aset_name, key in BUILDS:
        camp_id = next((c["id"] for c in camps if (c.get("name") or "") == camp_name), None)
        if camp_id:
            print(f"· campaign exists ({camp_id}) — filling gaps")
        else:
            camp = g.create_campaign(
                acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                is_adset_budget_sharing_enabled="false",
                special_ad_categories=[], status="ACTIVE")
            camp_id = camp["id"]
            print(f"✓ campaign {camp_id}  «{camp_name}»")
            time.sleep(PACE)
        have = {N(a.get("name") or "") for a in g._get_all(
            f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
        tgt = _copy.deepcopy(base)
        tgt["flexible_spec"] = _copy.deepcopy(tgts[key])
        for want in HOOKS:
            if N(want) in have:
                print(f"  · «{want[:30]}» 已在 — skip")
                continue
            aset = g.create_adset(
                acct, name=aset_name, campaign_id=camp_id, daily_budget=DAILY,
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
                targeting=_copy.deepcopy(tgt), status="PAUSED")
            time.sleep(PACE)
            spec = {"name": f"MY | {key} HOOK | {want}", "object_story_id": posts[want]}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=want, adset_id=aset["id"],
                             creative={"creative_id": cr["id"]},
                             status="ACTIVE", conversion_domain=conv)
            print(f"  ✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{want[:30]}»")
            time.sleep(PACE)
        print()
    print("BUILD 0914 DT+BEER HOOK DONE — 全部 ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
