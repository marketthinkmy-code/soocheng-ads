"""Read-only: resolve everything needed to (A) prune dead SG ads, (B) rebuild the 3
rejected SG ads, (C) port 3 proven MY creatives into SG.

Prints: SG campaign→adset→ad tree with media ids + spend/reg since SG launch; the MY
source creatives to port (video_id + copy); and the rejected SG ads' media + adset.
"""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

SG_SINCE = "2026-07-05"
PORT_NAMES = ["盖电脑", "街头突击", "你敢吗"]          # MY proven → port into SG
REJECTED_NAMES = ["不是怕交易", "moomoo", "厌倦了等待"]  # SG rejected → rebuild compliant


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()

    ins = {r.get("ad_id"): r for r in g._get_all(f"{acct}/insights", {
        "level": "ad", "fields": "ad_id,spend,actions",
        "time_range": json.dumps({"since": SG_SINCE, "until": today}), "limit": "500"})}

    allads = g._get_all(f"{acct}/ads", {
        "fields": "id,name,effective_status,adset_id,campaign{name},"
                  "creative{id,video_id,image_hash,body,title}", "limit": "400"})

    def spend_reg(ad_id):
        r = ins.get(ad_id, {})
        return float(r.get("spend") or 0), extract_results(r.get("actions"), token)

    # ── SG tree ────────────────────────────────────────────────────────────────
    print("=" * 80)
    print(f"SG STRUCTURE + spend/reg since {SG_SINCE}")
    print("=" * 80)
    for camp in g.list_campaigns(acct):
        cn = camp.get("name", "")
        if "[SG]" not in cn.upper():
            continue
        print(f"\nCAMPAIGN {camp['id']} [{camp.get('effective_status')}] {cn}")
        for a in g._get_all(f"{camp['id']}/adsets",
                            {"fields": "id,name,effective_status", "limit": "50"}):
            print(f"  ADSET {a['id']} [{a.get('effective_status')}] {a.get('name')}")
        for ad in [x for x in allads if "[SG]" in ((x.get('campaign') or {}).get('name') or '').upper()
                   and (x.get('campaign') or {}).get('name') == cn]:
            cr = ad.get("creative") or {}
            sp, rg = spend_reg(ad["id"])
            media = (f"vid={cr.get('video_id')}" if cr.get("video_id")
                     else f"img={cr.get('image_hash')}" if cr.get("image_hash") else "post")
            print(f"    AD {ad['id']} [{ad.get('effective_status')}] adset={ad.get('adset_id')} "
                  f"spendRM{sp:.0f} reg{rg:.0f} {media} | {ad.get('name')}")

    # ── MY port sources ──────────────────────────────────────────────────────────
    print("\n\n" + "=" * 80)
    print("PORT SOURCES (MY proven creatives → to add to SG)")
    print("=" * 80)
    for want in PORT_NAMES:
        matches = [ad for ad in allads if want in (ad.get("name") or "")
                   and "[SG]" not in ((ad.get("campaign") or {}).get("name") or "").upper()]
        print(f"\n### “{want}” — {len(matches)} MY match(es)")
        for ad in matches:
            cr = ad.get("creative") or {}
            print(f"  AD {ad['id']} [{ad.get('effective_status')}] {(ad.get('campaign') or {}).get('name')}")
            print(f"     name : {ad.get('name')}")
            print(f"     media: vid={cr.get('video_id')} img={cr.get('image_hash')}")
            print(f"     title: {cr.get('title')}")
            print(f"     body : {(cr.get('body') or '')[:900]}")

    # ── rejected SG ads (media + adset to reuse for the compliant rebuild) ────────
    print("\n\n" + "=" * 80)
    print("REJECTED SG ADS (media + adset for the compliant rebuild)")
    print("=" * 80)
    for want in REJECTED_NAMES:
        for ad in allads:
            nm = (ad.get("name") or "")
            camp = (ad.get("campaign") or {}).get("name", "")
            if want.lower() in nm.lower() and "[SG]" in camp.upper():
                cr = ad.get("creative") or {}
                print(f"\n[{want}] AD {ad['id']} [{ad.get('effective_status')}] {camp}")
                print(f"   adset={ad.get('adset_id')}  vid={cr.get('video_id')} img={cr.get('image_hash')}")
                print(f"   name: {nm}")
                break

    print("\nDONE.")


if __name__ == "__main__":
    main()
