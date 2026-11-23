# -*- coding: utf-8 -*-
"""owner 2026-11-23「SG 那边我还可以怎么搞？怎么建」→ AskUserQuestion 选「建好后今天就开」.
Evidence (report_audiences_1119 / report_top_creatives_1119, run 11/23 10:07, 10/29 起, 报名表真报名去机器人, 成交 = 买家买前最后一次广告报名的位置):
SG Broad = the only SG audience with volume + sales (RM4,596 · 57 真报名 · 2 单); SG interest audiences together 5 真报名 0 单.
SG creatives with sales / lowest CPL: 用我的方法 (2 单), 年纪大 (1 单), 决定变少 (真 CPL 76), 盖电脑 (this cycle CPL 44).

Builds ONE pool (Andromeda: distinct creatives together in one ad set):
  (Webinarkit) [SG] STOCKBLOOM | BROAD POOL | 1-1-4 | 1123 — CBO RM100/day, campaign PAUSED
  › «Broad | SG 28+» (Advantage+ on, age_range 28–65; geo / locales / conversion / attribution / regional fields from SG BROAD SG 1030)
  › 4 ads, each REUSING the existing SG creative (same post = same social proof, same url_tags) of:
      年纪大     ← [SG] BROAD SG › Broad | SG 28+ · ad 120250144813480521 (1 sale)
      用我的方法  ← [SG] BROAD SG › Broad | SG 28+ · ad 120250144813920521 (1 sale; that position was owner-closed 11/20 — new position)
      决定变少    ← [SG] NEW VIDEO · Broad › Broad | SG 28+ · V4 · ad 120250544546540521 (10 真报名)
      盖电脑     ← [SG] LOW CPL · Broad | 1-1-3 | 1120 › Broad | SG 28+ · ad 120250706571120521 (live, CPL 44)
Placements are NOT written (11/19 lesson: placements only by owner in Ads Manager) → the new ad set starts on automatic placements;
the campaign stays PAUSED until WK removes Audience Network in Ads Manager and it is read back (META MCP), then
execute_open_sgpool_1123.py opens the campaign layer. Gates: ban list / 🚫 / DISAPPROVED source, every post → webinarkit-register-wed,
(Webinarkit) prefix. Idempotent. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120250144811110521"
CNAME = "(Webinarkit) [SG] STOCKBLOOM | BROAD POOL | 1-1-4 | 1123"
ASET = "Broad | SG 28+"
BUDGET = 10000
SRC = {"年纪大": "120250144813480521", "用我的方法": "120250144813920521", "决定变少": "120250544546540521", "盖电脑": "120250706571120521"}
POST_VIA_MY = {"盖电脑": ("120251454701640329", "1001334883061622_122126499021286543")}   # same post as execute_build_sg113b_1120.py


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
for k, aid in SRC.items():
    a = g.get_object(aid, "name,effective_status,campaign{name},adset{name},"
                          "creative{id,effective_object_story_id,object_story_spec,url_tags}")
    cr = a["creative"]
    if not link_of(cr) and k in POST_VIA_MY:      # SG creative made from object_story_id → verify the link on the MY ad with the same post
        my_ad, post = POST_VIA_MY[k]
        assert cr.get("effective_object_story_id") == post, (k, cr.get("effective_object_story_id"))
        m = gmy.get_object(my_ad, "creative{effective_object_story_id,object_story_spec}")["creative"]
        assert m.get("effective_object_story_id") == post and link_of(m) == LINK, (k, m)
        print(f"  ({k}: 链接经 MY ad {my_ad} 同一个 post 核对)")
    else:
        assert link_of(cr) == LINK, (k, link_of(cr))
    assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], (k, a["name"])
    assert a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES"), (k, a["effective_status"])
    src[k] = (a["name"], cr["id"])
    print(f"  {k}: «{a['campaign']['name']}» › «{a['adset']['name']}» · «{a['name']}» · ad {aid} ({a['effective_status']})\n"
          f"      creative {cr['id']} · post {cr.get('effective_object_story_id')} · → Webinarkit ✅ · url_tags {cr.get('url_tags')}")
bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
bt = bs["targeting"]
targeting = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
targeting.update(age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
print(f"  模板 «{bs['campaign']['name']}» › «{bs['name']}» · 转化 «{ccv['name']}» · geo {targeting['geo_locations'].get('countries')} · "
      f"locales {targeting.get('locales')} · Advantage+ 开 · 建议 28–65 · 版位不写（自动 → owner 在 Ads Manager 拿掉 AN）")
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}\n      › «{ASET}» ACTIVE · ads: "
      + " · ".join(n for n, _ in src.values()))
if not CONFIRM:
    print("BUILD SG BROAD POOL DONE (dry-run)")
    raise SystemExit(0)

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
for k, (nm, crid) in src.items():
    if nm not in got:
        g.create_ad(acct, name=nm, adset_id=sid, creative={"creative_id": crid}, status="ACTIVE")
        time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
print(f"      ad set «{ASET}» · {sid}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status},creative{id,effective_object_story_id}", "limit": "20"}):
    print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}"
          f" · creative {(a.get('creative') or {}).get('id')} · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD SG BROAD POOL DONE")
