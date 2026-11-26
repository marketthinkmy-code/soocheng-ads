# -*- coding: utf-8 -*-
"""owner 2026-11-26「winning ad set try different ads」→ 选「① ② 都建」· ② = winning ad set × different ads. SG account:
(Webinarkit) [SG] STOCKBLOOM | BROAD · NEW ADS | 1-1-3 | 1126 — CBO RM100/day, campaign PAUSED (owner reviews + switches it on),
1 ad set «Broad | SG 28+» (Advantage+ on, suggested age 28–65; conversion / optimization / attribution / regional fields + geo / locales
from SG BROAD SG 1030 › Broad | SG 28+). Ads reuse the existing SG creative (same post, same url_tags) of:
korea = SG LOW CPL 1-1-3 ad 120250706569340521 · 盖电脑 = SG LOW CPL 1-1-3 ad 120250706571120521 (7 real regs) ·
V5 不适合你 = SG NEW VIDEO · Broad V5 ad 120250544549430521. Placements NOT written (owner sets them in Ads Manager).
Gates: source ad not banned / 🚫 / DISAPPROVED / WITH_ISSUES; creative link → webinarkit-register-wed; Webinarkit conversion.
Idempotent. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120250144811110521"            # SG BROAD SG 1030 › Broad | SG 28+
CNAME = "(Webinarkit) [SG] STOCKBLOOM | BROAD · NEW ADS | 1-1-3 | 1126"
ASET = "Broad | SG 28+"
BUDGET = 10000
SRC_ADS = ["120250706569340521", "120250706571120521", "120250544549430521"]   # korea · 盖电脑 · V5
BAD = ("DISAPPROVED", "WITH_ISSUES")
# SG creatives made from a post id (11/20 SG LOW CPL build) carry no object_story_spec; their link was proven on the MY ad of the same post
MY_PROOF = {"1001334883061622_122126499027286543": "120251456191090329",   # korea · MY BROAD MY 1017
            "1001334883061622_122126499021286543": "120251454701640329"}   # 盖电脑 · MY BUSINESS OWNER 1017


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
gmy = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
ads = []
for aid in SRC_ADS:
    a = g.get_object(aid, "name,effective_status,campaign{name},adset{name},creative{id}")
    cr = g.get_object(a["creative"]["id"], "effective_object_story_id,object_story_spec,url_tags")
    nm = a["name"]
    assert not compliance.is_banned(nm, s.compliance.banned_creatives) and "🚫" not in nm, nm
    assert a["effective_status"] not in BAD, (nm, a["effective_status"])
    lk, how = link_of(cr), "SG creative"
    post = cr.get("effective_object_story_id")
    if not lk and post in MY_PROOF:
        m = gmy.get_object(MY_PROOF[post], "creative{effective_object_story_id,object_story_spec}")["creative"]
        assert m.get("effective_object_story_id") == post, (nm, m)
        lk, how = link_of(m), f"同 post 的 MY ad {MY_PROOF[post]}"
    assert lk == LINK, (nm, lk)
    ads.append((nm, a["creative"]["id"]))
    print(f"  ad «{nm}» · 来源 {a['campaign']['name']} › {a['adset']['name']} · ad {aid} ({a['effective_status']}) · SG creative {a['creative']['id']}"
          f" · post {cr.get('effective_object_story_id')} · → Webinarkit ✅（{how}）· url_tags {'有' if cr.get('url_tags') else '无'}")
bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
bt = bs["targeting"]
targeting = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
targeting.update(age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
print(f"  模板 «{bs['campaign']['name']}» › «{bs['name']}» · 转化 «{ccv['name']}» · geo {targeting['geo_locations'].get('countries')} · "
      f"locales {targeting.get('locales')} · Advantage+ 开 · 建议 28–65")
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}\n      › «{ASET}» ACTIVE · ads: " + " · ".join(n for n, _ in ads))
if not CONFIRM:
    print("BUILD SG BROAD NEW ADS DONE (dry-run)")
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
for nm, crid in ads:
    if nm not in got:
        g.create_ad(acct, name=nm, adset_id=sid, creative={"creative_id": crid}, status="ACTIVE")
        time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
assert c["status"] == "PAUSED", c
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
x = g.get_object(sid, "name,status,targeting")
print(f"      ad set «{x['name']}» · adset {sid} · {x['status']} · age_range {x['targeting'].get('age_range')} · "
      f"Advantage+ {(x['targeting'].get('targeting_automation') or {}).get('advantage_audience')}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name},creative{effective_object_story_id}", "limit": "20"}):
    print(f"      › {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']} · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD SG BROAD NEW ADS DONE")
