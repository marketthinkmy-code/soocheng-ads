"""Read-only, LEAN: resolve the SG structure + media ids for (A) pruning dead SG ads,
(B) rebuilding rejected SG ads, (C) porting proven MY creatives into SG. IDs only, no bodies.
"""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

SG_SINCE = "2026-07-05"
PORT_NAMES = ["盖电脑", "街头突击", "你敢吗"]   # MY proven → port into SG (want the VIDEO version)


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
                  "creative{id,video_id,image_hash}", "limit": "400"})

    def sr(ad_id):
        r = ins.get(ad_id, {})
        return float(r.get("spend") or 0), extract_results(r.get("actions"), token)

    def media(cr):
        return (f"vid={cr.get('video_id')}" if cr.get("video_id")
                else f"img={cr.get('image_hash')}" if cr.get("image_hash") else "post")

    print("=" * 78)
    print(f"SG TREE + spend/reg since {SG_SINCE}")
    print("=" * 78)
    for camp in g.list_campaigns(acct):
        cn = camp.get("name", "")
        if "[SG]" not in cn.upper():
            continue
        print(f"\nCAMP {camp['id']} [{camp.get('effective_status')}] {cn}")
        for a in g._get_all(f"{camp['id']}/adsets",
                            {"fields": "id,name,effective_status", "limit": "50"}):
            print(f"  ADSET {a['id']} [{a.get('effective_status')}] {a.get('name')}")
        for ad in [x for x in allads if (x.get('campaign') or {}).get('name') == cn]:
            sp, rg = sr(ad["id"])
            print(f"    AD {ad['id']} [{ad.get('effective_status'):11}] adset={ad.get('adset_id')} "
                  f"RM{sp:5.0f} reg{rg:.0f} {media(ad.get('creative') or {}):28} | {ad.get('name')}")

    print("\n\n" + "=" * 78)
    print("PORT SOURCES (MY video 5/6/2 → video_id to reuse in SG)")
    print("=" * 78)
    for want in PORT_NAMES:
        ms = [ad for ad in allads if want in (ad.get("name") or "")
              and "[SG]" not in ((ad.get("campaign") or {}).get("name") or "").upper()]
        # prefer a VIDEO creative, then ACTIVE
        ms.sort(key=lambda ad: (0 if (ad.get("creative") or {}).get("video_id") else 1,
                                0 if ad.get("effective_status") == "ACTIVE" else 1))
        print(f"\n### “{want}”")
        for ad in ms:
            print(f"  AD {ad['id']} [{ad.get('effective_status')}] "
                  f"{media(ad.get('creative') or {})} | {(ad.get('campaign') or {}).get('name')} | {ad.get('name')}")

    print("\n\n" + "=" * 78)
    print("REJECTED SG ADS (status WITH_ISSUES/DISAPPROVED — media + adset for rebuild)")
    print("=" * 78)
    for ad in allads:
        if ad.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED") \
                and "[SG]" in ((ad.get("campaign") or {}).get("name") or "").upper():
            cr = ad.get("creative") or {}
            print(f"\nAD {ad['id']} [{ad.get('effective_status')}] {(ad.get('campaign') or {}).get('name')}")
            print(f"   adset={ad.get('adset_id')}  {media(cr)}  | {ad.get('name')}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
