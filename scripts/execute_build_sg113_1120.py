# -*- coding: utf-8 -*-
"""owner 2026-11-19 SG 1-1-3 →「我觉得还是 broad 吧！让 meta 自己挑对的人报名」(replaces the Purchase LAL choice; nothing was built for it).
SG account: (Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120 — CBO RM80/day, campaign PAUSED (owner switches it on), 1 ad set
«Broad | SG 28+» (Advantage+ on, age_range 28–65; geo/locales, SG Webinarkit custom conversion, optimization, attribution, regional fields
copied from the SG BROAD SG 1030 ad set), ad set + ads ACTIVE. Ads: 年纪大 (SG post, 1 SG sale) and 用我的方法 (2 SG sales) reuse their SG
creatives; 决定变少 uses the MY News post that sold (new SG creative, object_story_id + same url_tags/IG), falling back to the SG V4
creative if Meta refuses. Every post asserted → webinarkit-register-wed. Ban gate. Idempotent. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120250144811110521"      # (Webinarkit) [SG] STOCKBLOOM | BROAD SG | 1-1-5 | 1030 › Broad | SG 28+
CNAME = "(Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120"
ASET = "Broad | SG 28+"
BUDGET = 8000
SG_ADS = {"年纪大": ("120250144813480521", "1001334883061622_122127755757286543"),
          "用我的方法": ("120250144813920521", "1001334883061622_122126501961286543")}
V4_POST, V4_SG_AD = "1001334883061622_122128786599286543", "120250544546540521"


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
ads = {}
for k, (aid, post) in SG_ADS.items():
    a = g.get_object(aid, "name,campaign{name},creative{id,effective_object_story_id,object_story_spec,url_tags}")
    cr = a["creative"]
    assert cr.get("effective_object_story_id") == post and link_of(cr) == LINK, (k, cr)
    assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], (k, a["name"])
    ads[k] = (a["name"], cr["id"])
    print(f"  {k}: «{a['name']}» · SG creative {cr['id']} · post {post} · → Webinarkit ✅")
ref = g.get_object(SG_ADS["年纪大"][0], "creative{object_story_spec,url_tags}")["creative"]
ig, url_tags = (ref.get("object_story_spec") or {}).get("instagram_user_id"), ref.get("url_tags")
v4sg = g.get_object(V4_SG_AD, "name,creative{id,effective_object_story_id,object_story_spec}")
assert link_of(v4sg["creative"]) == LINK
print(f"  决定变少: 用 MY News 有成交的 post {V4_POST}（新建 SG 素材）· 备用 SG V4 creative {v4sg['creative']['id']} · url_tags {url_tags} · ig {ig}")

bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
bt = bs["targeting"]
targeting = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
targeting.update(age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
print(f"  模板 «{bs['campaign']['name']}» › «{bs['name']}» {TEMPLATE_SET} · 转化 «{ccv['name']}» {po['custom_conversion_id']} · "
      f"geo {targeting['geo_locations'].get('countries')} · locales {targeting.get('locales')} · Advantage+ 开 · 建议 28–65 · regional {bs.get('regional_regulated_categories')}")
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}")
print(f"      › «{ASET}» ACTIVE · ads: Video：决定变少，成绩才稳 · {ads['年纪大'][0]} · {ads['用我的方法'][0]}")
if not CONFIRM:
    print("BUILD SG 1-1-3 DONE (dry-run)")
    raise SystemExit(0)

mine = {c.get("name"): c for c in g._get_all(acct + "/adcreatives", {"fields": "id,name,effective_object_story_id", "limit": "3000"})}
nm = "决定变少 · post 122128786599286543 · SG"
if nm in mine and mine[nm].get("effective_object_story_id") == V4_POST:
    v4 = mine[nm]["id"]
else:
    try:
        f = dict(name=nm, object_story_id=V4_POST, url_tags=url_tags)
        v4 = g.create_adcreative(acct, instagram_user_id=ig, **f)["id"] if ig else g.create_adcreative(acct, **f)["id"]
        time.sleep(3)
        assert g.get_object(v4, "effective_object_story_id").get("effective_object_story_id") == V4_POST
    except Exception as exc:  # noqa: BLE001
        print(f"  (用 MY post 建 SG 素材失败：{str(exc)[:120]} — 改用 SG V4 creative)")
        v4 = v4sg["creative"]["id"]
ads["V4"] = ("Video：决定变少，成绩才稳", v4)
print(f"  ✅ 决定变少 SG creative {v4}")

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
for k in ("V4", "年纪大", "用我的方法"):
    name, cr = ads[k]
    if name not in got:
        g.create_ad(acct, name=name, adset_id=sid, creative={"creative_id": cr}, status="ACTIVE")
        time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status},creative{effective_object_story_id}", "limit": "20"}):
    print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}"
          f" · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD SG 1-1-3 DONE")
