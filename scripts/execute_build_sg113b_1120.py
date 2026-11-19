# -*- coding: utf-8 -*-
"""owner 2026-11-19「SG 1-1-3 应该还有一个才对呀」→「建」. SG account, mirror of MY LOW CPL:
(Webinarkit) [SG] STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120 — CBO RM100/day, campaign PAUSED (owner switches it on), 1 ad set
«Broad | SG 28+» (Advantage+ on, age_range 28–65; conversion / optimization / attribution / regional fields from SG BROAD SG 1030),
ad set + ads ACTIVE. Ads: korea · 炒了五年 · 盖电脑 — the same Webinarkit posts as the MY 1-1-3 (MY ads' posts), each through a new SG
creative (object_story_id + the SG url_tags / IG). Every post asserted → webinarkit-register-wed. Ban gate. Idempotent.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120250144811110521"
CNAME = "(Webinarkit) [SG] STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120"
ASET = "Broad | SG 28+"
BUDGET = 10000
SRC = {"korea": ("120251456191090329", "1001334883061622_122126499027286543"),
       "炒了五年": ("120251840432100329", "1001334883061622_122128786629286543"),
       "盖电脑": ("120251454701640329", "1001334883061622_122126499021286543")}


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
gmy = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
src = {}
for k, (aid, post) in SRC.items():
    a = gmy.get_object(aid, "name,creative{effective_object_story_id,object_story_spec}")
    assert a["creative"].get("effective_object_story_id") == post and link_of(a["creative"]) == LINK, (k, a)
    assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], (k, a["name"])
    src[k] = a["name"]
    print(f"  {k}: «{a['name']}» · post {post} · → Webinarkit ✅ (MY ad {aid})")
ref = g.get_object("120250144813480521", "creative{object_story_spec,url_tags}")["creative"]
ig, url_tags = (ref.get("object_story_spec") or {}).get("instagram_user_id"), ref.get("url_tags")
bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
bt = bs["targeting"]
targeting = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
targeting.update(age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
print(f"  模板 «{bs['campaign']['name']}» › «{bs['name']}» · 转化 «{ccv['name']}» · geo {targeting['geo_locations'].get('countries')} · "
      f"locales {targeting.get('locales')} · Advantage+ 开 · 建议 28–65 · url_tags/ig 照 SG 现有素材")
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}\n      › «{ASET}» ACTIVE · ads: " + " · ".join(src.values()))
if not CONFIRM:
    print("BUILD SG 1-1-3 #2 DONE (dry-run)")
    raise SystemExit(0)

mine = {c.get("name"): c for c in g._get_all(acct + "/adcreatives", {"fields": "id,name,effective_object_story_id", "limit": "3000"})}
crid = {}
for k, (aid, post) in SRC.items():
    nm = f"{k} · post {post.split('_')[1]} · SG"
    if nm in mine and mine[nm].get("effective_object_story_id") == post:
        crid[k] = mine[nm]["id"]
        continue
    f = dict(name=nm, object_story_id=post, url_tags=url_tags)
    try:
        crid[k] = g.create_adcreative(acct, instagram_user_id=ig, **f)["id"] if ig else g.create_adcreative(acct, **f)["id"]
    except Exception as exc:  # noqa: BLE001
        print(f"  ({k} 带 IG 建素材失败：{str(exc)[:100]} — 改不带 IG)")
        crid[k] = g.create_adcreative(acct, **f)["id"]
    time.sleep(3)
    assert g.get_object(crid[k], "effective_object_story_id").get("effective_object_story_id") == post, k
    print(f"  ✅ {k} SG creative {crid[k]}")
cid = existing[CNAME]["id"] if CNAME in existing else g.create_campaign(
    acct, name=CNAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[], buying_type="AUCTION",
    daily_budget=BUDGET, bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
time.sleep(4)
have = {x["name"]: x["id"] for x in g._get_all(cid + "/adsets", {"fields": "name", "limit": "20"})}
sid = have.get(ASET) or g.create_adset(
    acct, name=ASET, campaign_id=cid, status="ACTIVE", optimization_goal=bs["optimization_goal"], billing_event=bs["billing_event"],
    targeting=targeting, promoted_object=po, attribution_spec=bs.get("attribution_spec"),
    regional_regulated_categories=bs.get("regional_regulated_categories") or [],
    regional_regulation_identities=bs.get("regional_regulation_identities") or {})["id"]
time.sleep(4)
got = {x["name"] for x in g._get_all(sid + "/ads", {"fields": "name", "limit": "20"})}
for k in SRC:
    if src[k] not in got:
        g.create_ad(acct, name=src[k], adset_id=sid, creative={"creative_id": crid[k]}, status="ACTIVE")
        time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status},creative{effective_object_story_id}", "limit": "20"}):
    print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}"
          f" · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD SG 1-1-3 #2 DONE")
