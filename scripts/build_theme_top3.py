# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-30): 4 new interest campaigns — BEER ALCOHOL + DAY TRADING,
each on SG and MY, each 1-1-3 with the proven TOP3 winner posts.

Basis: historical Paid Student List buyers on themes not yet running on the new accounts —
beer/alcohol/distilled/wine/coffee (24 buyers) and day trading (31 buyers).

- Interests are resolved LIVE via Meta's adinterest search (ids never guessed); the theme's
  term list mirrors the old converting campaign names.
- Targeting scaffold (geo/age/locales/advantage) is copied verbatim from each account's
  converting Travel ad set; only flexible_spec is swapped for the new theme's interests.
- 3 ads reuse the winner posts (freestyle 1 · video 12 炒过那么多 · video 5 trading — all
  currently Meta-approved; owner policy 2026-07-30: review status + CPL/CPA govern).
- RM100/day CBO · OUTCOME_SALES · everything PAUSED; owner activates. Idempotent per
  campaign name. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy
import os
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
CAMP_GAP = 10.0
DAILY = 10000   # RM100/day (cents)

SG = "act_893025326577600"
MY = "act_759339046918885"

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

ACCTS = [
    {"label": "SG", "acct": SG, "sg": True, "prefix": "[SG] STOCKBLOOM",
     "ref_camp": "120248220646980521", "geo": ["SG"]},   # converting SG Travel 1-1-3
    {"label": "MY", "acct": MY, "sg": False, "prefix": "STOCKBLOOM",
     "ref_camp": "120247524817830575", "geo": ["MY"]},   # converting MY Travel 1-1-3 (CPA≈RM263)
]

# theme -> search terms (mirrors the old converting campaign names)
THEMES = [
    ("BEER ALCOHOL", ["Beer", "Alcoholic beverages", "Distilled beverage", "Wine", "Coffee"]),
    ("DAY TRADING",  ["Day trading", "Swing trading", "Technical analysis"]),
]


def _norm(s: str) -> str:
    return " ".join((s or "").replace("：", ":").split()).casefold()


WINNERS = [
    ("freestyle 1",                        lambda n: n == "freestyle 1"),
    ("video 12：炒过那么多，累而且不稳定",   lambda n: "炒过那么多" in n),
    ("video 5：trading 早就不是这样了！",    lambda n: "早就不是这样" in n),
]


def resolve_posts(g) -> dict:
    pools = []
    for acct in (SG, MY):
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
                          "limit": "200"})
        pools.append((acct, ads))
    out = {}
    for disp, match in WINNERS:
        cands = []
        for acct, ads in pools:
            for a in ads:
                if not match(_norm(a.get("name") or "")):
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    cands.append((0 if a.get("effective_status") == "ACTIVE" else 1, post))
        if not cands:
            raise SystemExit(f"‼️ no live ad found matching «{disp}»")
        cands.sort()
        out[disp] = cands[0][1]
        print(f"  «{disp}»  post={cands[0][1]}")
    return out


def resolve_interests(g, terms) -> list:
    """Meta adinterest search: exact name match preferred, else biggest audience containing
    the term. Dedup by id; every pick is printed for the dry-run eyeball."""
    out, seen = [], set()
    for t in terms:
        rows = g._request("GET", "search",
                          params={"type": "adinterest", "q": t, "limit": "25"}).get("data", [])
        exact = [r for r in rows if (r.get("name") or "").casefold() == t.casefold()]
        pool = exact or [r for r in rows if t.casefold() in (r.get("name") or "").casefold()]
        if not pool:
            print(f"    ⚠️ «{t}» — no interest found, skipped")
            continue
        best = max(pool, key=lambda r: r.get("audience_size_lower_bound") or 0)
        if best["id"] in seen:
            continue
        seen.add(best["id"])
        size = best.get("audience_size_lower_bound") or 0
        print(f"    «{t}» -> {best.get('name')}  id={best['id']}  audience≈{size:,}")
        out.append({"id": str(best["id"]), "name": best.get("name", t)})
    return out


def ref_targeting(g, ac) -> tuple:
    adsets = g._get_all(f"{ac['ref_camp']}/adsets",
                        {"fields": "id,name,targeting,promoted_object", "limit": "20"})
    if not adsets:
        raise SystemExit(f"‼️ {ac['label']} reference campaign has no ad sets")
    ref = adsets[0]
    tgt = ref.get("targeting") or {}
    promo = ref.get("promoted_object") or {}
    geo = (tgt.get("geo_locations") or {}).get("countries")
    if geo != ac["geo"]:
        raise SystemExit(f"‼️ {ac['label']} ref geo={geo}, expected {ac['geo']}")
    print(f"  [{ac['label']}] scaffold from adset {ref['id']}  geo={geo}  "
          f"promoted_object pixel={promo.get('pixel_id')}")
    return tgt, promo


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  BEER ALCOHOL + DAY TRADING × SG + MY  ·  1-1-3 × 4  ·  "
          f"RM{DAILY/100:.0f}/day CBO · PAUSED\n")

    print("== winner posts ==")
    posts = resolve_posts(g)

    print("\n== resolve theme interests (live adinterest search) ==")
    theme_interests = {}
    for theme, terms in THEMES:
        print(f"  {theme}:")
        ints = resolve_interests(g, terms)
        if not ints:
            raise SystemExit(f"‼️ {theme}: zero interests resolved — aborting")
        theme_interests[theme] = ints

    print("\n== targeting scaffolds ==")
    scaffolds = {ac["label"]: ref_targeting(g, ac) for ac in ACCTS}

    for ac in ACCTS:
        base_tgt, promo = scaffolds[ac["label"]]
        existing = {c.get("name") for c in
                    g._get_all(f"{ac['acct']}/campaigns", {"fields": "id,name", "limit": "500"})}
        print(f"\n══ {ac['label']}  {ac['acct']} ══")
        for theme, _terms in THEMES:
            camp_name = f"{ac['prefix']} | {theme} | 1-1-3"
            aset_name = f"AdSet ({theme.title()} | {ac['label']} 25+)"
            if camp_name in existing:
                print(f"  · '{camp_name}' already exists — skip")
                continue
            tgt = copy.deepcopy(base_tgt)
            tgt["flexible_spec"] = [{"interests": theme_interests[theme]}]

            if not CONFIRM:
                names = ", ".join(i["name"] for i in theme_interests[theme])
                print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO PAUSED")
                print(f"     adset '{aset_name}'  interests: {names}"
                      + ("  · SG binding" if ac["sg"] else ""))
                for disp in posts:
                    print(f"       ad  «{disp}»  (PAUSED)")
                continue

            camp = g.create_campaign(
                ac["acct"], name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                special_ad_categories=s.meta.special_ad_categories,
                special_ad_category_country=ac["geo"], status="PAUSED")
            print(f"  ✓ campaign {camp['id']}  {camp_name}")
            time.sleep(PACE)

            aset_kwargs = dict(
                name=aset_name, campaign_id=camp["id"],
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object=promo, targeting=tgt, status="PAUSED")
            if ac["sg"]:
                aset_kwargs.update(regional_regulated_categories=REGIONAL,
                                   regional_regulation_identities=REG_IDENTITIES)
            aset = g.create_adset(ac["acct"], **aset_kwargs)
            print(f"  ✓ adset {aset['id']}")
            time.sleep(PACE)

            conv = s.meta.conversion_domain_bare or None
            for disp, post in posts.items():
                spec = {"name": f"{ac['label']} | {disp}", "object_story_id": post}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(ac["acct"], **spec)
                ad = g.create_ad(ac["acct"], name=disp, adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"     ✓ ad {ad['id']}  «{disp}»")
                time.sleep(PACE)
            time.sleep(CAMP_GAP)

    print("\nDONE — 4 campaigns built PAUSED; owner activates in Ads Manager."
          if CONFIRM else "\nDRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
