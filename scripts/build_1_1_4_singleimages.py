# -*- coding: utf-8 -*-
"""Build the TOP-3-targeting 1-1-4 single-image campaigns on BOTH accounts.

TOP 3 ad-set targeting by paid conversions (Paid Student List, last 30d):
    Broad/Advantage+ (41)  ·  Travel (11)  ·  Luxury Goods (10)

For each account — MY 3.0 (act_759339046918885) and SG (act_893025326577600) — build 3
campaigns (Broad · Travel · Luxury Goods), each **1-1-4**:
    1 CBO campaign   OUTCOME_SALES, RM100/day, PAUSED
    1 ad set         Broad = Advantage+ (advantage_audience=1, no interests)
                     Travel / Luxury = hard interest flexible_spec
                     SG adds the Singapore verified-advertiser binding
    4 NEW single-image ads   copy pulled live from Notion (Image 23..34, split per targeting)

Self-calibrating so this build matches what is actually converting (and sidesteps the
config-vs-plan2 pixel question): the promoted_object (pixel + event) and the exact Travel /
Luxury interest specs are READ LIVE from the reference converting ad sets, not guessed.

image_hash is per-ad-account, so every image is uploaded to EACH account (cached in state,
namespaced by account so MY's hash is never reused for SG).

Everything is PAUSED — the owner reviews + activates in Ads Manager. Dry-run unless CONFIRM=true.

⚠️ Images 27 / 28 / 31 are Traditional-Chinese image files (captions are Simplified) — flagged
   for the owner to swap-or-accept before activating. The copy↔image pairing (content_id ↔
   file_id) is the one derived by reading each image; it is NOT re-guessed here.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from adbot.build_1_1_10 import display_ad_name
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client, notion_client
from adbot.notion_captions import fetch_captions
from adbot.settings import REPO_ROOT, load_settings
from adbot import state

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

DAILY = 10000                       # RM100/day CBO (cents)
PACE = 2.5                          # seconds between write calls (rate-limit hygiene)
CAMP_GAP = 12.0                     # extra gap between campaigns on one account
DL_DIR = Path(REPO_ROOT) / "build_downloads"
MEDIA_KEY = "media_cache_1_1_4"    # {f"{acct}:{file_id}": image_hash}

# ── reference LIVE ad sets to calibrate from (proven converting; interest ids are global) ──
REF_LUX_ADSET = "120247585341010575"     # MY LUXURY GOODS interest ad set (pixel + Luxury interests)
REF_TRAVEL_CAMP = "120248220646980521"   # SG TRAVEL campaign -> its ad set carries the Travel interests

# Fallback Luxury interests (owner-approved, from plan2_build) if the live read comes back empty.
LUXURY_INT_FALLBACK = [
    {"id": "6007828099136", "name": "Luxury goods"},
    {"id": "6002893385022", "name": "Luxury watches"},
    {"id": "6003587678073", "name": "Rolex"},
    {"id": "6003266225248", "name": "Jewellery"},
    {"id": "6003715005316", "name": "Luxury yacht"},
    {"id": "6003484864669", "name": "Wealth management"},
    {"id": "6003102546240", "name": "Private banking"},
]

# Singapore verified-advertiser binding (adset-level; MY needs none).
REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

# ── the 12 approved single images: content_id N -> Drive file_id (pairing derived by reading
#    each image's on-image text; DO NOT re-guess). 繁体 = Traditional-Chinese image file. ──
FILE_IDS = {
    23: "1GcILlSWbQEi_GRvHyKcM39CHgvhtiGsI",
    24: "1daNTZfmYRUTasAAaX7SzprftkeYb8rC2",
    25: "19LYQDfjXB9aZAnynP6uX2nAQS-vCQmKh",
    26: "1FBOFZXR5OPpNYxUdTKFKLgIoAUjBL5YL",
    27: "1paf85o8bCcuLYpN83Lv_SjLu8Rkf4Sb_",   # 繁体
    28: "1BotBkgp3S2mwIC1nZriPSmY7CYCu4lrz",   # 繁体
    29: "1qs0eG08lEF5kW5iEcG-RL01C9WpZ2F8G",
    30: "119aPcyl1YmsldrQ0Fj43c5QYqMyfXiFx",
    31: "1r0Y3o5JSXDSlkUHTdHB1qb1Lpaw6BuLv",   # 繁体
    32: "1i9YiUnt2cU9vIP5KkKTUt-180xzWLXm9",
    33: "1o9lCtrWPyHPEJR0OJbp1x2TYmObm-z2t",
    34: "1PLM2otGMNjWAaT3_uNqGVuOUE57lteG9",
}
TRAD = {27, 28, 31}

# ── image split per targeting (4 each). Copy self-selects (Andromeda broad retrieval); the
#    split is a pool assignment, adjustable in Ads Manager. ──
SPLIT = {
    "BROAD":        [23, 30, 33, 34],
    "TRAVEL":       [25, 27, 31, 24],
    "LUXURY GOODS": [26, 28, 29, 32],
}

ACCTS = [
    {"label": "MY", "acct": "act_759339046918885", "sg": False,
     "prefix": "STOCKBLOOM", "special_country": ["MY"]},
    {"label": "SG", "acct": "act_893025326577600", "sg": True,
     "prefix": "[SG] STOCKBLOOM", "special_country": ["SG"]},
]


# ── calibration reads ────────────────────────────────────────────────────────
def _interests_from_targeting(tgt: dict) -> list:
    for blk in (tgt or {}).get("flexible_spec") or []:
        if blk.get("interests"):
            return [{"id": str(i["id"]), "name": i.get("name", "")} for i in blk["interests"]]
    ints = (tgt or {}).get("interests")
    if ints:
        return [{"id": str(i["id"]), "name": i.get("name", "")} for i in ints]
    return []


def calibrate(g) -> dict:
    """Read pixel + Luxury interests off the MY Luxury ad set, Travel interests off the SG
    Travel ad set, and the live interest-targeting scaffold (locales / age / advantage flag)."""
    lux = g.get_object(REF_LUX_ADSET, "name,promoted_object,targeting")
    promo = lux.get("promoted_object") or {}
    lux_tgt = lux.get("targeting") or {}
    lux_int = _interests_from_targeting(lux_tgt) or LUXURY_INT_FALLBACK

    scaffold = {
        "age_min": lux_tgt.get("age_min", 25),
        "age_max": lux_tgt.get("age_max", 65),
        "locales": lux_tgt.get("locales") or [1004],
        "advantage": ((lux_tgt.get("targeting_automation") or {}).get("advantage_audience", 0)),
    }

    adsets = g._get_all(f"{REF_TRAVEL_CAMP}/adsets", {"fields": "id,name,targeting", "limit": "50"})
    travel_int = []
    for a in adsets:
        travel_int = _interests_from_targeting(a.get("targeting") or {})
        if travel_int:
            break

    return {"promoted": promo, "lux_int": lux_int, "travel_int": travel_int, "scaffold": scaffold}


def targeting_for(geo: str, group: str, cal: dict) -> dict:
    sc = cal["scaffold"]
    t = {
        "geo_locations": {"countries": [geo]},
        "age_min": sc["age_min"], "age_max": sc["age_max"],
        "locales": sc["locales"],
    }
    if group == "BROAD":
        t["targeting_automation"] = {"advantage_audience": 1}
        return t
    interests = cal["lux_int"] if group == "LUXURY GOODS" else cal["travel_int"]
    t["flexible_spec"] = [{"interests": interests}]
    t["targeting_automation"] = {"advantage_audience": sc["advantage"]}
    return t


# ── media (per-account image_hash, cached) ───────────────────────────────────
def ensure_local(drive, n: int) -> str:
    dest = DL_DIR / f"image_{n}.png"
    if not dest.exists():
        drive.download_file(FILE_IDS[n], dest)
    return str(dest)


def image_hash_for(g, drive, cache: dict, acct: str, n: int) -> str:
    key = f"{acct}:{FILE_IDS[n]}"
    if cache.get(key):
        return cache[key]
    path = ensure_local(drive, n)
    h = g.upload_image(acct, path)
    cache[key] = h
    state.save(MEDIA_KEY, cache)
    print(f"     [uploaded] image_{n} -> {acct} hash {h}")
    time.sleep(PACE)
    return h


# ── creative spec (single image) — mirrors adbot.build_1_1_10.creative_spec ───
def creative_spec(s, content_id: str, headline: str, caption: str, image_hash: str) -> dict:
    link = s.meta.lead_destination.link_url
    cta = {"type": s.meta.call_to_action, "value": {"link": link}}
    story = {"page_id": s.meta.page_id, "link_data": {
        "link": link, "image_hash": image_hash,
        "message": caption, "name": headline, "call_to_action": cta}}
    spec = {"name": f"{s.naming.prefix} | {content_id}", "object_story_spec": story}
    if s.meta.instagram_user_id:
        spec["instagram_user_id"] = s.meta.instagram_user_id
    if s.meta.url_tags:
        spec["url_tags"] = s.meta.url_tags
    return spec


def build_campaign(g, s, drive, cache, ac, group, caps, cal) -> None:
    acct, prefix = ac["acct"], ac["prefix"]
    camp_name = f"{prefix} | {group} | 1-1-4"
    aset_name = f"AdSet ({group} | {ac['label']} 25+)"
    tgt = targeting_for("SG" if ac["sg"] else "MY", group, cal)

    existing = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    if any(c.get("name") == camp_name for c in existing):
        print(f"  · '{camp_name}' already exists — skip")
        return

    imgs = SPLIT[group]
    if not CONFIRM:
        interests = tgt.get("flexible_spec", [{}])[0].get("interests", [])
        idesc = "Advantage+ (broad)" if group == "BROAD" else \
            f"{len(interests)} interests: " + ", ".join(i["name"] for i in interests)
        print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO OUTCOME_SALES PAUSED")
        print(f"     adset '{aset_name}'  {idesc}"
              + ("  · SG advertiser binding" if ac["sg"] else ""))
        for n in imgs:
            cid = f"image_{n}"
            cap = caps.get(cid, {})
            flag = "  ⚠️繁体图" if n in TRAD else ""
            print(f"       ad  {display_ad_name(cap.get('name') or cid)}"
                  f"   [{cid} ↔ {FILE_IDS[n]}]  hook={cap.get('headline','')[:16]}…"
                  f"  cap={len(cap.get('caption',''))}c{flag}")
        return

    camp = g.create_campaign(
        acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
        daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
        special_ad_categories=s.meta.special_ad_categories,
        special_ad_category_country=ac["special_country"], status="PAUSED")
    print(f"  ✓ campaign {camp['id']}  {camp_name}")
    time.sleep(PACE)

    aset_kwargs = dict(
        name=aset_name, campaign_id=camp["id"], optimization_goal="OFFSITE_CONVERSIONS",
        billing_event="IMPRESSIONS", promoted_object=cal["promoted"], targeting=tgt,
        status="PAUSED")
    if ac["sg"]:
        aset_kwargs.update(regional_regulated_categories=REGIONAL,
                           regional_regulation_identities=REG_IDENTITIES)
    aset = g.create_adset(acct, **aset_kwargs)
    print(f"  ✓ adset {aset['id']}  ({group})")
    time.sleep(PACE)

    conv = s.meta.conversion_domain_bare or None
    for n in imgs:
        cid = f"image_{n}"
        cap = caps.get(cid, {})
        h = image_hash_for(g, drive, cache, acct, n)
        spec = creative_spec(s, cid, cap.get("headline", ""), cap.get("caption", ""), h)
        cr = g.create_adcreative(acct, **spec)
        ad_name = display_ad_name(cap.get("name") or cid)
        ad = g.create_ad(acct, name=ad_name, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"       ✓ ad {ad['id']}  {ad_name}  [{cid}]")
        time.sleep(PACE)


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    drive = DriveClient(s.secrets.google_sa_json)
    caps = fetch_captions(notion_client(s), s.notion.database_id)
    cache = state.load(MEDIA_KEY)
    DL_DIR.mkdir(parents=True, exist_ok=True)

    # preflight: every planned content_id must have non-empty headline + caption in Notion
    need = [f"image_{n}" for n in FILE_IDS]
    missing = [cid for cid in need
               if not caps.get(cid, {}).get("caption") or not caps.get(cid, {}).get("headline")]
    if missing:
        raise SystemExit(f"Notion copy missing/empty (headline+caption) for: {missing} — seed first.")

    cal = calibrate(g)
    pixel = (cal["promoted"] or {}).get("pixel_id", "(none)")
    print(f"CONFIRM={CONFIRM}  ·  6 campaigns (Broad·Travel·Luxury × MY+SG)  ·  RM{DAILY/100:.0f}/day CBO  ·  PAUSED")
    print(f"calibrated  pixel={pixel}  event={(cal['promoted'] or {}).get('custom_event_type')}  "
          f"advantage(interest)={cal['scaffold']['advantage']}  locales={cal['scaffold']['locales']}")
    print(f"            Travel interests={[i['name'] for i in cal['travel_int']] or '‼️EMPTY'}")
    print(f"            Luxury interests={[i['name'] for i in cal['lux_int']]}\n")
    if not cal["travel_int"]:
        raise SystemExit("Travel interests came back EMPTY from the reference ad set — aborting "
                         "rather than shipping a mis-targeted Travel campaign.")

    for ac in ACCTS:
        print(f"══ {ac['label']}  {ac['acct']}" + ("  (SG binding)" if ac["sg"] else "") + " ══")
        for i, group in enumerate(("BROAD", "TRAVEL", "LUXURY GOODS")):
            build_campaign(g, s, drive, cache, ac, group, caps, cal)
            if CONFIRM and i < 2:
                time.sleep(CAMP_GAP)
        print()

    print("DONE — 6 campaigns built PAUSED; owner activates in Ads Manager."
          if CONFIRM else "DRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
