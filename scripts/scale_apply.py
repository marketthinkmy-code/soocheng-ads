"""Owner-approved scale moves (option 2 + 3). Dry-run unless CONFIRM=true.

 2) INJECT champion creatives — freestyle 1 / 盖电脑 / 我跟你讲 — into the 3 MY interest
    ad sets (Luxury / Business Owner / Investment), PAUSED, reusing the page post id
    (keeps social proof). Owner activates in Ads Manager. Skips a creative already present.

 3) RAISE CBO +~25-30% on the low-CPL winner campaigns (LIVE budget change — takes effect
    immediately on the active campaign). Only campaigns comfortably under the RM50 CPL
    ceiling are raised; high-CPL campaigns (MY RUNNING/BUSINESS OWNER) are left alone.
"""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY = "act_759339046918885"

CHAMPS = [
    ("freestyle 1",        "1001334883061622_122097411579286543"),
    ("video 5：盖电脑，喂！",  "1001334883061622_1788611461813837"),
    ("video 6：我跟你讲！",    "1001334883061622_4377635152552494"),
]
MY_INTEREST_ADSETS = [
    ("LUXURY GOODS",   "120247585341010575"),
    ("BUSINESS OWNER", "120247585352830575"),
    ("INVESTMENT",     "120247585358270575"),
]

# campaign_id -> (label, new daily_budget cents).  +~25-30% on winners (7d CPL in comment)
CBO = [
    ("120248231846030521", "SG RUNNING",     32000),  # 250->320  CPL16.3
    ("120248220646980521", "SG TRAVEL",      32000),  # 250->320  CPL17.5
    ("120248220658080521", "SG BROAD A",     32000),  # 250->320  CPL21.9
    ("120248197444090521", "SG BROAD B",     26000),  # 200->260  CPL21.9
    ("120247522993770575", "MY BROAD B",     13000),  # 100->130  CPL27.1
    ("120247585340620575", "MY LUXURY GOODS", 32000), # 250->320  CPL29.9 (+champions)
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None
    print(f"CONFIRM={CONFIRM}\n")

    print("== (2) INJECT champions into MY interest ad sets (PAUSED) ==")
    for label, aset in MY_INTEREST_ADSETS:
        present = {(a.get("name") or "") for a in
                   g._get_all(f"{aset}/ads", {"fields": "name", "limit": "100"})}
        for nm, post in CHAMPS:
            if nm in present:
                print(f"  · {label}: «{nm}» already there — skip")
                continue
            if not CONFIRM:
                print(f"  WOULD ADD {label}: «{nm}»  (post {post})")
                continue
            spec = {"name": f"MY | {nm}", "object_story_id": post}
            if url_tags:
                spec["url_tags"] = url_tags
            cr = g.create_adcreative(MY, **spec)
            ad = g.create_ad(MY, name=nm, adset_id=aset,
                             creative={"creative_id": cr["id"]}, status="PAUSED",
                             conversion_domain=conv)
            print(f"  ✓ {label}: ad {ad['id']} «{nm}»")
            time.sleep(2.5)   # rate-limit hygiene between ad creations

    print("\n== (3) RAISE CBO (LIVE budget change) ==")
    for cid, label, newb in CBO:
        old = (g.get_object(cid, "daily_budget") or {}).get("daily_budget")
        try:
            olds = f"RM{int(old)/100:.0f}"
        except (TypeError, ValueError):
            olds = str(old)
        if not CONFIRM:
            print(f"  WOULD SET {label:16} {cid}: {olds} -> RM{newb/100:.0f}/day")
            continue
        g._request("POST", cid, data={"daily_budget": newb})
        print(f"  ✓ {label:16} {cid}: {olds} -> RM{newb/100:.0f}/day")

    print("\nDONE — champions PAUSED (owner activates); CBO raised live."
          if CONFIRM else "\nDRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
