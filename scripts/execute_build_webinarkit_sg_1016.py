# -*- coding: utf-8 -*-
"""owner 2026-10-16 (dataset shared to SG): rebuild SG on Webinarkit, run from 17 Oct 00:00 SGT.

Custom conversion «WED WEBINARKIT REGISTER (SG)» on dataset 1338380974889410 with the same rule as MY's
1048291251556714 (created once, reused on rerun). 4 campaigns «(Webinarkit) [SG] STOCKBLOOM | <X> | 1-1-N | 1017»,
OUTCOME_SALES, no special category, CBO, PAUSED; ad sets start 2026-10-17 00:00, SINGAPORE_UNIVERSAL verified
advertiser copied from the 0911 ad set; targeting cloned from the running chains, age 28-65.
Ads: NEW video creatives from the SG dark-post creatives (video + approved caption), link → -wed.
Ban gate first. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
PIXEL = "1338380974889410"
MY_CC = "1048291251556714"
CC_NAME = "WED WEBINARKIT REGISTER (SG)"
START = "2026-10-17T00:00:00+0800"
PAGE, IG = "1001334883061622", "17841480427751602"
# new ad name -> (SG source ad name, video id)
SOURCES = {
    "Video：盖电脑，喂！":        ("HOOK：Video 5：盖电脑，喂！", "1610130017181800"),
    "Video：用我的方法":          ("拼接：Video 1：用我的方法", "1084978400896889"),
    "Video：不选 forex 不选黄金":  ("HOOK：Video 12：不选 forex 不选黄金", "1607400890935670"),
    "Video：我跟你讲！":          ("重拍：Video 6：我跟你讲！", "2059836261562402"),
}
G, M, F, T = "Video：盖电脑，喂！", "Video：用我的方法", "Video：不选 forex 不选黄金", "Video：我跟你讲！"
# label, source campaign fragment, ad set name, mode, budget cents, ads
CHAINS = [
    ("BROAD SG",        "BROAD SG 25+ | 0911",  "Broad | SG 28+",        "broad",    15000, [G, M, F, T]),
    ("LUXURY GOODS",    "LUXURY GOODS | 1-1-3", "Luxury Goods | SG 28+", "interest", 10000, [G, M, F]),
    ("PURCHASE LAL 5%", "PURCHASE LAL 5%",      "Purchase LAL 5% | SG 28+", "audience", 10000, [G, F]),
    ("TRAVEL",          "| TRAVEL |",           "Travel | SG 28+",       "interest",  7500, [G]),
]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"Webinarkit SG build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    hits = compliance.filter_banned(list(SOURCES) + [v[0] for v in SOURCES.values()], s.compliance.banned_creatives)
    if hits:
        print(f"⛔ 禁跑命中，停：{hits}"); return
    info = g._request("GET", acct, params={"fields": "account_status"})
    assert info.get("account_status") == 1, f"account status {info}"
    px = g._get_all(acct + "/adspixels", {"fields": "id,name", "limit": "50"})
    print("  pixels visible on SG:", [(p["id"], p.get("name")) for p in px])
    assert any(p["id"] == PIXEL for p in px), "dataset 1338380974889410 still not shared to SG"
    rule = g.get_object(MY_CC, "rule")["rule"]
    ccs = g._get_all(acct + "/customconversions", {"fields": "id,name", "limit": "100"})
    cc_id = next((c["id"] for c in ccs if c.get("name") == CC_NAME), None)
    print(f"  custom conversion on SG: {cc_id or '(will create)'} · rule {rule[:90]}")

    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,created_time", "limit": "300"})
    time.sleep(1)
    rr = None
    for c in camps:
        if "BROAD SG 25+ | 0911" in c["name"]:
            for a in g._get_all(c["id"] + "/adsets", {"fields": "regional_regulated_categories,regional_regulation_identities", "limit": "5"}):
                if a.get("regional_regulated_categories"):
                    rr = (a["regional_regulated_categories"], a["regional_regulation_identities"]); break
        if rr:
            break
    print(f"  regional: {rr}")
    assert rr, "no SG regional fields found"

    ads_all = g._get_all(acct + "/ads", {"fields": "name,creative{object_story_spec,url_tags}", "limit": "500"})
    src, url_tags = {}, None
    for v, (old, vid) in SOURCES.items():
        a = next((x for x in ads_all if (x.get("name") or "").replace("🌟", "").strip() == old and
                  (((x.get("creative") or {}).get("object_story_spec") or {}).get("video_data") or {}).get("video_id") == vid), None)
        assert a, f"source «{old}» {vid} not found"
        vd = a["creative"]["object_story_spec"]["video_data"]
        url_tags = url_tags or a["creative"].get("url_tags")
        src[v] = vd
        print(f"  {v}: video {vid} · caption {len(vd.get('message') or '')} chars «{(vd.get('message') or '')[:24]}»")
    print(f"  url_tags: {url_tags}")

    plan = []
    for label, frag, aset_name, mode, budget, ads in CHAINS:
        cands = sorted([c for c in camps if frag in c["name"] and "webinar" not in c["name"].lower()],
                       key=lambda c: c.get("created_time") or "", reverse=True)
        t0 = None
        for c in cands:
            sets = g._get_all(c["id"] + "/adsets", {"fields": "targeting", "limit": "5"}); time.sleep(0.6)
            if sets:
                t0, src_name = sets[0]["targeting"], c["name"]; break
        assert t0, f"{label}: no source ad set"
        t = {k: t0[k] for k in ("geo_locations", "locales") if k in t0}
        if mode == "broad":
            t["age_min"], t["age_max"], t["age_range"] = 18, 65, [28, 65]
            t["targeting_automation"] = {"advantage_audience": 1}
        else:
            if mode == "interest":
                t["flexible_spec"] = t0.get("flexible_spec") or []
                assert t["flexible_spec"], f"{label}: no interests on source"
            else:
                t["custom_audiences"] = t0.get("custom_audiences") or []
                assert t["custom_audiences"], f"{label}: no audience on source"
            t["age_min"], t["age_max"] = 28, 65
            t["targeting_automation"] = {"advantage_audience": 0}
        n_int = sum(len(x.get("interests") or []) for x in (t.get("flexible_spec") or []))
        print(f"  {label}: from «{src_name}» · interests {n_int} · audiences {[a.get('name') for a in t.get('custom_audiences', [])]} · "
              f"age {t['age_min']}-{t['age_max']} {t.get('age_range', '')} · RM{budget // 100} · ads {len(ads)}")
        plan.append((label, aset_name, t, budget, ads))

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nBUILD DONE (dry-run)"); return

    if not cc_id:
        cc_id = g._request("POST", acct + "/customconversions", data={
            "name": CC_NAME, "pixel_id": PIXEL, "rule": rule, "custom_event_type": "OTHER"})["id"]
        print(f"  custom conversion created {cc_id}"); time.sleep(3)
    promoted = {"pixel_id": PIXEL, "custom_event_type": "OTHER", "pixel_rule": rule, "custom_conversion_id": cc_id}
    have_cr = {c.get("name"): c["id"] for c in g._get_all(acct + "/adcreatives", {"fields": "id,name", "limit": "500"})}
    have_c = {c["name"]: c["id"] for c in camps}
    cr = {}
    for v, vd0 in src.items():
        nm = f"{v} · webinarkit-wed"
        if nm in have_cr:
            cr[v] = have_cr[nm]; continue
        vd = {"video_id": vd0["video_id"], "message": vd0["message"],
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        for k in ("image_url", "image_hash", "title"):
            if vd0.get(k):
                vd[k] = vd0[k]
                if k in ("image_url", "image_hash"):
                    break
        cr[v] = g.create_adcreative(acct, name=nm, url_tags=url_tags,
                                    object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": vd})["id"]
        print(f"  creative {v} → {cr[v]}"); time.sleep(2)
    for label, aset_name, t, budget, ads in plan:
        n = len(ads)
        cname = f"(Webinarkit) [SG] STOCKBLOOM | {label} | 1-1-{n} | 1017"
        if cname in have_c:
            cid = have_c[cname]
            if g._get_all(cid + "/adsets", {"fields": "id", "limit": "5"}):
                print(f"  = {cname} already built — skip"); continue
        else:
            cid = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                                    daily_budget=budget, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")["id"]
            time.sleep(2)
        a = g.create_adset(acct, name=aset_name, campaign_id=cid, status="ACTIVE", optimization_goal="OFFSITE_CONVERSIONS",
                           billing_event="IMPRESSIONS", start_time=START, targeting=t, promoted_object=promoted,
                           attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                           regional_regulated_categories=rr[0], regional_regulation_identities=rr[1])
        time.sleep(2)
        ids = []
        for v in ads:
            ids.append(g.create_ad(acct, name=v, adset_id=a["id"], creative={"creative_id": cr[v]}, status="ACTIVE")["id"]); time.sleep(2)
        print(f"  ✅ {cname}: campaign {cid} (PAUSED) · adset {a['id']} · ads {ids}")
    print("BUILD DONE")


if __name__ == "__main__":
    main()
