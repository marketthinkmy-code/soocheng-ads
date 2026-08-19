# -*- coding: utf-8 -*-
"""Owner 2026-08-19 «帮我建 campaign 跑 1%-5%，用 top 3 转化最多的广告来测试»:

Per account, ONE ladder-test campaign:

  {prefix} | PURCHASE LAL 1-5% | 1-5-3     CBO RM100/day · PAUSED
    ├─ AdSet (Purchase LAL 1%   | {L} 25+)  audience = PURCHASE 1% LAL
    ├─ AdSet (Purchase LAL 1-2% | {L} 25+)  audience = PURCHASE 1-2% LAL
    ├─ AdSet (Purchase LAL 2-3% | {L} 25+)  …
    ├─ AdSet (Purchase LAL 3-4% | {L} 25+)  …
    └─ AdSet (Purchase LAL 4-5% | {L} 25+)  …
  each ad set carries the SAME top-3 converting creatives of that account
  (ranked from the Paid Student List, last 30 days, [SG]-prefix split; resolved to
  live post ids so social proof carries over and nothing re-enters review).

Scaffold (geo/age/promoted_object …) cloned from the account's existing
PURCHASE LAL 5% ad set; custom_audiences swapped per band. SG ad sets carry the
Singapore regulated-category binding. Idempotent at every level (campaign, ad set,
ad). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy as _copy
import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.graph import GraphError
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 10000            # RM100/day CBO
TODAY = dt.date(2026, 8, 19)
D30 = TODAY - dt.timedelta(days=30)
D60 = TODAY - dt.timedelta(days=60)

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

BANDS = ["1%", "1-2%", "2-3%", "3-4%", "4-5%"]
LALS = {
    "MY": {"1%": "120248446170570575", "1-2%": "120248446174840575",
           "2-3%": "120248446178710575", "3-4%": "120248446183420575",
           "4-5%": "120248446186250575"},
    "SG": {"1%": "120249026332760521", "1-2%": "120249026333230521",
           "2-3%": "120249026333650521", "3-4%": "120249026334070521",
           "4-5%": "120249026335050521"},
}

ACCTS = [
    {"label": "MY", "cfg": "config.yaml", "sg": False, "prefix": "STOCKBLOOM"},
    {"label": "SG", "cfg": "config.sg.yaml", "sg": True, "prefix": "[SG] STOCKBLOOM"},
]


def rank_top_ads(sales, label: str):
    """Per-account (by [sg] campaign prefix) sale counts by normalised ad name."""
    d30, d60 = {}, {}
    for s in sales:
        if not s.date or s.date <= D60 or not s.ad:
            continue
        acct = "SG" if s.campaign.startswith("[sg]") else "MY"
        if acct != label:
            continue
        d60[s.ad] = d60.get(s.ad, 0) + 1
        if s.date > D30:
            d30[s.ad] = d30.get(s.ad, 0) + 1
    return sorted(d60, key=lambda k: (-d30.get(k, 0), -d60[k]))


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"PURCHASE LAL 1-5% ladder campaigns × MY + SG · 1-5-3 · RM{DAILY/100:.0f}/day "
          f"PAUSED — {mode}\n")

    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    # post pool from BOTH accounts (posts are page-level, so they work cross-account)
    pools = []
    for cfg in ("config.yaml", "config.sg.yaml"):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        pools.append(g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
             "limit": "300"}))
        time.sleep(1)

    def resolve_post(ad_key: str):
        cands = []
        for ads in pools:
            for a in ads:
                if cpa.norm(a.get("name") or "") != ad_key:
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    cands.append((0 if a.get("effective_status") == "ACTIVE" else 1,
                                  post, a.get("name")))
        if not cands:
            return None, None
        cands.sort()
        return cands[0][1], cands[0][2]

    for ac in ACCTS:
        label = ac["label"]
        s = load_settings(REPO_ROOT / "config" / ac["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"══ {label}  {acct} ══")

        top3 = []
        for ad_key in rank_top_ads(sales, label):
            post, disp = resolve_post(ad_key)
            if post:
                top3.append({"key": ad_key, "post": post, "name": disp})
                print(f"  TOP{len(top3)}: «{disp}»  post={post}")
            else:
                print(f"  (skip «{ad_key[:40]}» — no live post found)")
            if len(top3) == 3:
                break
        if len(top3) < 3:
            print(f"  ⛔ only {len(top3)} resolvable top ads — skipping account")
            continue

        try:
            scaffold_name = cpa.norm(f"AdSet (Purchase LAL 5% | {label} 25+)")
            src = None
            for a in g._get_all(f"{acct}/adsets",
                                {"fields": "id,name,targeting,promoted_object", "limit": "500"}):
                if cpa.norm(a.get("name") or "") == scaffold_name:
                    src = a
                    break
            if not src:
                print(f"  ⛔ scaffold ad set not found — skipping account")
                continue
            base_tgt = _copy.deepcopy(src.get("targeting") or {})
            base_tgt.pop("flexible_spec", None)
            promo = src.get("promoted_object") or {}
            print(f"  scaffold: «{src.get('name')}» ({src['id']})")

            camp_name = f"{ac['prefix']} | PURCHASE LAL 1-5% | 1-5-3"
            existing = {c.get("name"): c.get("id") for c in
                        g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
            camp_id = existing.get(camp_name)
            if camp_id:
                print(f"  · campaign exists ({camp_id}) — filling gaps")
            elif not CONFIRM:
                print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO PAUSED")
                for band in BANDS:
                    print(f"     adset {band}: LAL {LALS[label][band]}"
                          + ("  · SG binding" if ac["sg"] else ""))
                print(f"     ads × 3 in each: {[t['name'] for t in top3]}")
                print()
                continue
            else:
                camp = g.create_campaign(
                    acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                    daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    special_ad_categories=s.meta.special_ad_categories,
                    special_ad_category_country=[label], status="PAUSED")
                camp_id = camp["id"]
                print(f"  ✓ campaign {camp_id}")
                time.sleep(PACE)

            if not CONFIRM:
                print()
                continue

            have_asets = {cpa.norm(a.get("name") or ""): a["id"] for a in g._get_all(
                f"{camp_id}/adsets", {"fields": "id,name", "limit": "20"})}
            for band in BANDS:
                aset_name = f"AdSet (Purchase LAL {band} | {label} 25+)"
                try:
                    aset_id = have_asets.get(cpa.norm(aset_name))
                    if not aset_id:
                        tgt = _copy.deepcopy(base_tgt)
                        tgt["custom_audiences"] = [{"id": LALS[label][band]}]
                        kw = dict(name=aset_name, campaign_id=camp_id,
                                  optimization_goal="OFFSITE_CONVERSIONS",
                                  billing_event="IMPRESSIONS", promoted_object=promo,
                                  targeting=tgt, status="PAUSED")
                        if ac["sg"]:
                            kw.update(regional_regulated_categories=REGIONAL,
                                      regional_regulation_identities=REG_IDENTITIES)
                        aset = g.create_adset(acct, **kw)
                        aset_id = aset["id"]
                        print(f"   ✓ adset {band}  {aset_id}")
                        time.sleep(PACE)
                    else:
                        print(f"   · adset {band} exists")
                    have_ads = {a.get("name") for a in g._get_all(
                        f"{aset_id}/ads", {"fields": "name", "limit": "20"})}
                    for t in top3:
                        if t["name"] in have_ads:
                            print(f"      ✓ «{t['name']}» present — skip")
                            continue
                        spec = {"name": f"{label} | LAL {band} | {t['name']}",
                                "object_story_id": t["post"]}
                        if s.meta.url_tags:
                            spec["url_tags"] = s.meta.url_tags
                        cr = g.create_adcreative(acct, **spec)
                        ad = g.create_ad(acct, name=t["name"], adset_id=aset_id,
                                         creative={"creative_id": cr["id"]}, status="PAUSED",
                                         conversion_domain=conv)
                        print(f"      ✓ ad {ad['id']}  «{t['name']}»")
                        time.sleep(PACE)
                except Exception as e:  # throttle etc. — next band survives
                    print(f"   ❌ {band}: {str(e)[:130]} — continuing")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()

    print("DONE — ladder campaigns PAUSED; owner reviews & activates."
          if CONFIRM else "DRY-RUN — set confirm=true to build.")


if __name__ == "__main__":
    main()
