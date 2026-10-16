# -*- coding: utf-8 -*-
"""owner 2026-10-15/16: rebuild MY 5.0 on Webinarkit (new URL + new dataset), run from 17 Oct 00:00 MYT.

4 campaigns «(Webinarkit) STOCKBLOOM | <X> | 1-1-4 | 1017», OUTCOME_SALES, NO special ad category (owner 10/15),
CBO RM150, created PAUSED (owner reviews + activates; delivery starts at the ad-set start_time 2026-10-17 00:00).
Ad set optimizes the owner's custom conversion «WED WEBINARKIT REGISTER» 1048291251556714 on dataset
1338380974889410; regional MALAYSIA_UNIVERSAL fields copied from the team-built Webinarkit ad set; targeting
cloned from the running 1008/1012 chains (age 28-65: hard lock when Advantage+ off, age_range when on).
Ads: one NEW video creative per video (post reuse would keep the old link), built from the video + caption of the
post each MY 5.0 ad currently uses, link → https://soochenginvesting.com/webinarkit-register-wed, url_tags copied
from the old MY creative. Ban gate before anything. CONFIRM=true writes; otherwise dry-run (reads + prints)."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
PIXEL = "1338380974889410"
CC = "1048291251556714"
TEMPLATE_ADSET = "120251424979360329"          # ONLY its verified-advertiser identity is copied (owner: the rest of that build is wrong)
START = "2026-10-17T00:00:00+0800"
DAILY = 15000
PAGE = "1001334883061622"
IG = "17841480427751602"
# (new campaign label, source campaign-name fragment on MY 5.0, new ad set name, advantage+ on?)
CHAINS = [
    ("LUXURY MY",      "LUXURY MY | 1-1-4 | 1012",      "Luxury | MY 28+",         False),
    ("BUSINESS OWNER", "BUSINESS OWNER | 1-1-5 | 1008", "Business Owner | MY 28+", False),
    ("BROAD MY",       "BROAD MY 30+ | 1-1-5 | 1008",   "Broad | MY 28+",          True),
    ("DAY TRADING",    "DAY TRADING | 1-1-5 | 1008",    "Day Trading | MY 28+",    False),
]
OLD_MY = "act_759339046918885"
# new ad name -> (source ad name on MY 3.0, its video id; validated on MY 5.0 2026-10-16)
SOURCES = {
    "Video：盖电脑，喂！":              ("HOOK：Video 5：盖电脑，喂！", "1687663009590997"),
    "Video：年纪大的人做不了交易？":     ("Video 5：年纪大的人做不了交易？", "1841446977230767"),
    "Video：赚美金，一定要接美国客户？":  ("Video 6：马来西亚小白怎样赚美金？", "1105913068610488"),
}
VIDEOS = list(SOURCES)          # freestyle korea: no dark-post creative found — owner adds it in Ads Manager
KEEP_T = ("geo_locations", "locales", "flexible_spec", "exclusions", "targeting_automation", "age_min", "age_max")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"Webinarkit MY 5.0 build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    hits = compliance.filter_banned(VIDEOS, s.compliance.banned_creatives)
    if hits:
        print(f"⛔ 禁跑命中，停：{hits}"); return
    info = g._request("GET", acct, params={"fields": "name,account_status"})
    if info.get("account_status") != 1:
        print(f"⛔ 账户不是 ACTIVE（{info.get('account_status')}），停"); return
    tmpl = g.get_object(TEMPLATE_ADSET, "regional_regulated_categories,regional_regulation_identities,attribution_spec")
    rrc, rri = tmpl.get("regional_regulated_categories"), tmpl.get("regional_regulation_identities")
    print(f"regional: {rrc} {rri}")
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name", "limit": "200"})
    time.sleep(1)

    # ── sources: the original MY 3.0 dark-post creatives (video_id + caption + thumbnail) ──────
    #    (page posts can't be read without pages_read_engagement; these creatives validate on MY 5.0)
    old = g._get_all(OLD_MY + "/ads", {"fields": "name,creative{object_story_spec,url_tags}", "limit": "500"})
    src = {}
    for v, (old_name, vid_expect) in SOURCES.items():
        a = next((x for x in old if (x.get("name") or "").replace("🌟", "").strip() == old_name
                  and (((x.get("creative") or {}).get("object_story_spec") or {}).get("video_data") or {}).get("video_id") == vid_expect), None)
        assert a, f"source «{old_name}» video {vid_expect} not found on MY 3.0"
        vd = a["creative"]["object_story_spec"]["video_data"]
        src[v] = {"video_id": vd["video_id"], "message": vd.get("message") or "", "picture": vd.get("image_url"),
                  "image_hash": vd.get("image_hash"), "title": vd.get("title")}
        assert src[v]["message"], f"{v}: no caption"
        print(f"  {v}: video {vd['video_id']} · caption {len(src[v]['message'])} chars «{src[v]['message'][:30]}»")
    time.sleep(1)
    my_dt = next(c for c in camps if "DAY TRADING | 1-1-5 | 1008" in c["name"] and "webinar" not in c["name"].lower())
    cur = g._get_all(my_dt["id"] + "/ads", {"fields": "creative{url_tags}", "limit": "5"})
    url_tags = ((cur[0].get("creative") or {}).get("url_tags")) if cur else None
    print(f"  url_tags (from MY 5.0 DT 1008): {url_tags}")

    # ── targeting per chain ─────────────────────────────────────────────────────
    plan = []
    for label, frag, aset_name, adv in CHAINS:
        c = next(c for c in camps if frag in c["name"] and "webinar" not in c["name"].lower())
        time.sleep(1)
        sets = g._get_all(c["id"] + "/adsets", {"fields": "name,targeting", "limit": "10"})
        t0 = sets[0]["targeting"]
        t = {k: t0[k] for k in KEEP_T if k in t0}
        if adv:
            t.pop("age_min", None); t.pop("age_max", None)
            t["age_range"] = [28, 65]
            t["targeting_automation"] = {"advantage_audience": 1}
            t["age_min"], t["age_max"] = 18, 65
        else:
            t["age_min"], t["age_max"] = 28, 65
            t["targeting_automation"] = {"advantage_audience": 0}
        n_int = sum(len(x.get("interests") or []) for x in (t.get("flexible_spec") or []))
        print(f"  {label}: from «{c['name']}» · interests {n_int} · adv+ {adv} · age {t.get('age_min')}-{t.get('age_max')} {t.get('age_range', '')}")
        plan.append((label, aset_name, t))

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nBUILD DONE (dry-run)"); return

    # ── creatives (one per video, shared across chains) ─────────────────────────
    cr_ids = {}
    for v in VIDEOS:
        d = src[v]
        vd = {"video_id": d["video_id"], "message": d["message"],
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        if d.get("picture"):
            vd["image_url"] = d["picture"]
        elif d.get("image_hash"):
            vd["image_hash"] = d["image_hash"]
        if d.get("title"):
            vd["title"] = d["title"]
        r = g.create_adcreative(acct, name=f"{v} · webinarkit-wed", url_tags=url_tags,
                                object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": vd})
        cr_ids[v] = r["id"]; print(f"  creative {v} → {r['id']}"); time.sleep(2)

    built = []
    for label, aset_name, t in plan:
        cname = f"(Webinarkit) STOCKBLOOM | {label} | 1-1-4 | 1017"
        c = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                              daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")
        time.sleep(2)
        a = g.create_adset(acct, name=aset_name, campaign_id=c["id"], status="ACTIVE", optimization_goal="OFFSITE_CONVERSIONS",
                           billing_event="IMPRESSIONS", start_time=START, targeting=t,
                           promoted_object={"pixel_id": PIXEL, "custom_event_type": "OTHER", "custom_conversion_id": CC},
                           attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                           regional_regulated_categories=rrc, regional_regulation_identities=rri)
        time.sleep(2)
        ad_ids = []
        for v in VIDEOS:
            ad = g.create_ad(acct, name=v, adset_id=a["id"], creative={"creative_id": cr_ids[v]}, status="ACTIVE")
            ad_ids.append(ad["id"]); time.sleep(2)
        built.append((cname, c["id"], a["id"], ad_ids))
        print(f"  ✅ {cname}: campaign {c['id']} (PAUSED) · adset {a['id']} · ads {ad_ids}")
    print("\n完成。campaign 全部 PAUSED；owner 在 Ads Manager 审完开 campaign，ad set 17 Oct 00:00 开始投。")
    print("BUILD DONE")


if __name__ == "__main__":
    main()
