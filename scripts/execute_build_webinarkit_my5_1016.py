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
TEMPLATE_ADSET = "120251424979360329"          # team-built Webinarkit DT ad set (regional fields)
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
VIDEOS = ["Video：盖电脑，喂！", "Video：freestyle korea", "Video：年纪大的人做不了交易？", "Video：赚美金，一定要接美国客户？"]
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

    # ── source posts → video id, caption, thumbnail ─────────────────────────────
    src_camp = next(c for c in camps if "DAY TRADING | 1-1-5 | 1008" in c["name"] and "webinar" not in c["name"].lower())
    ads = g._get_all(src_camp["id"] + "/ads", {"fields": "name,creative{effective_object_story_id,url_tags}", "limit": "50"})
    src = {}
    url_tags = None
    for v in VIDEOS:
        a = next((x for x in ads if x.get("name") == v), None)
        assert a, f"source ad «{v}» not found in {src_camp['name']}"
        post = a["creative"]["effective_object_story_id"]
        url_tags = url_tags or a["creative"].get("url_tags")
        time.sleep(1)
        p = g.get_object(post, "message,full_picture,attachments{media_type,target{id},title,description}")
        att = ((p.get("attachments") or {}).get("data") or [{}])[0]
        vid = (att.get("target") or {}).get("id")
        src[v] = {"post": post, "video_id": vid, "message": p.get("message") or "", "picture": p.get("full_picture"),
                  "title": att.get("title"), "media": att.get("media_type")}
        print(f"  {v}: post {post} · {att.get('media_type')} video {vid} · msg {len(p.get('message') or '')} chars · "
              f"head «{(p.get('message') or '')[:40]}» · pic {'yes' if p.get('full_picture') else 'NO'}")
        assert vid and att.get("media_type", "").startswith("video"), f"{v}: no video on the post"
        assert p.get("message"), f"{v}: post has no caption"
    print(f"  url_tags: {url_tags}")

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
        vd = {"video_id": d["video_id"], "message": d["message"], "image_url": d["picture"],
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
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
