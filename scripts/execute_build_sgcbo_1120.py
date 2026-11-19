# -*- coding: utf-8 -*-
"""owner 2026-11-19「SG 那边建 第二个建法」+「Purchase LAL + Investment + Luxury」. SG account:
(Webinarkit) [SG] STOCKBLOOM | CBO · LAL INVEST LUX | 1-3-3 | 1120 — CBO RM100/day, campaign PAUSED (owner switches it on), 3 ad sets
(Purchase LAL 5% | SG 28+ · Investment | SG 28+ · Luxury | SG 28+), targeting cloned from the newest past ad set of that audience
(lookalike: custom audiences copied as-is; interests: hard age 28–65, Advantage+ off; Advantage+ on → age_range 28–65), conversion /
optimization / attribution / regional fields from the SG BROAD SG 1030 ad set; each with 决定变少 · 年纪大 · 用我的方法 reusing the SG
creatives of the SG 1-1-3 (Webinarkit posts). Ad sets + ads ACTIVE. Ban gate. Idempotent. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120250144811110521"
CNAME = "(Webinarkit) [SG] STOCKBLOOM | CBO · LAL INVEST LUX | 1-3-3 | 1120"
BUDGET = 10000
CREATIVES = {"Video：决定变少，成绩才稳": ("2674375702989899", "1001334883061622_122128786599286543"),
             "Video：年纪大的人做不了交易？": ("1632992341032705", "1001334883061622_122127755757286543"),
             "Video：用我的方法": ("1473832997895184", "1001334883061622_122126501961286543")}
AUDS = [("Purchase LAL 5% | SG 28+", ("lal",), ("act_893025326577600",)),
        ("Investment | SG 28+", ("investment",), ("act_893025326577600",)),
        ("Luxury | SG 28+", ("luxury",), ("act_893025326577600", "act_759339046918885"))]
KEEP = ("custom_audiences", "excluded_custom_audiences", "flexible_spec", "exclusions", "targeting_automation", "age_min", "age_max", "age_range")


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
for name, (cid_, post) in CREATIVES.items():
    cr = g.get_object(cid_, "effective_object_story_id,object_story_spec,url_tags")
    assert cr.get("effective_object_story_id") == post, (name, cr)
    assert not compliance.is_banned(name, s.compliance.banned_creatives), name
    print(f"  ad «{name}» · SG creative {cid_} · post {post}")
bs = g.get_object(TEMPLATE_SET, "name,targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
base = {k: bs["targeting"][k] for k in ("geo_locations", "locales") if k in bs["targeting"]}
print(f"  转化 «{ccv['name']}» {po['custom_conversion_id']} · geo {base['geo_locations'].get('countries')} · locales {base.get('locales')} · regional {bs.get('regional_regulated_categories')}")

PIN = {"Purchase LAL 5% | SG 28+": g.get_object("120249918410030521", "adset{id}")["adset"]["id"]}   # the 1017 LAL set that sold (not the 10/26 ALL LANG test)
targets = {}
for sname, keys, accts in AUDS:
    if sname in PIN:
        x = g.get_object(PIN[sname], "name,created_time,targeting,campaign{name}")
        x["id"] = PIN[sname]
        cands = [("act_893025326577600", x)]
    else:
        cands = []
    for ac in (accts if sname not in PIN else ()):
        try:
            for x in g._get_all(ac + "/adsets", {"fields": "name,created_time,targeting,campaign{name}", "limit": "500"}):
                t = x.get("targeting") or {}
                if any(k in (x["name"] + " " + x["campaign"]["name"]).lower() for k in keys) and (t.get("flexible_spec") or t.get("custom_audiences")):
                    cands.append((ac, x))
        except Exception as exc:  # noqa: BLE001
            print(f"   (读不到 {ac}: {str(exc)[:70]})")
    assert cands, f"⛔ 找不到 {sname} 的来源"
    # prefer SG-account sources, then newest
    ac, src = max(cands, key=lambda c: (c[0] == "act_893025326577600", c[1]["created_time"]))
    st = src["targeting"]
    t = dict(base, **{k: st[k] for k in KEEP if k in st})
    adv = (t.get("targeting_automation") or {}).get("advantage_audience", 0)
    if adv:
        t.update(age_max=65, age_range=[28, 65])
    else:
        t.update(age_min=28, age_max=65, targeting_automation={"advantage_audience": 0})
        t.pop("age_range", None)
    targets[sname] = t
    ints = [i.get("name") for f in (st.get("flexible_spec") or []) for i in (f.get("interests") or [])]
    cas = [c.get("name") or c.get("id") for c in (st.get("custom_audiences") or [])]
    print(f"  受众 {sname}: 复制自 {ac} «{src['campaign']['name']}» › «{src['name']}» ({src['id']}, {src['created_time'][:10]}) · "
          f"Advantage+ {'开 · 建议 28–65' if adv else '关 · 硬锁 28–65'}\n      "
          + (f"受众包 {cas}" if cas else f"兴趣 {ints}"))
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}")
for sname, *_ in AUDS:
    print(f"      › «{sname}» ACTIVE · ads: " + " · ".join(CREATIVES))
if not CONFIRM:
    print("BUILD SG CBO DONE (dry-run)")
    raise SystemExit(0)

cid = existing[CNAME]["id"] if CNAME in existing else g.create_campaign(
    acct, name=CNAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[], buying_type="AUCTION",
    daily_budget=BUDGET, bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
time.sleep(4)
have = {x["name"]: x["id"] for x in g._get_all(cid + "/adsets", {"fields": "name", "limit": "20"})}
for sname, *_ in AUDS:
    sid = have.get(sname) or g.create_adset(
        acct, name=sname, campaign_id=cid, status="ACTIVE", optimization_goal=bs["optimization_goal"], billing_event=bs["billing_event"],
        targeting=targets[sname], promoted_object=po, attribution_spec=bs.get("attribution_spec"),
        regional_regulated_categories=bs.get("regional_regulated_categories") or [],
        regional_regulation_identities=bs.get("regional_regulation_identities") or {})["id"]
    time.sleep(4)
    got = {x["name"] for x in g._get_all(sid + "/ads", {"fields": "name", "limit": "20"})}
    for name, (crid, _) in CREATIVES.items():
        if name not in got:
            g.create_ad(acct, name=name, adset_id=sid, creative={"creative_id": crid}, status="ACTIVE")
            time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "30"}):
    print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}")
print("BUILD SG CBO DONE")
