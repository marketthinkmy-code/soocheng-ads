# -*- coding: utf-8 -*-
"""owner 2026-11-19 第 2 个建法 CBO →「Luxury + Beer + Omakase」(after report_audiences_1119). MY 5.0:
(Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120 — CBO RM150/day, campaign PAUSED (owner switches it on), 3 ad sets
(Luxury Goods | MY 28+ · Beer | MY 28+ · Omakase | MY 28+; interests cloned from the newest past ad set of that audience; hard age 28–65,
Advantage+ off; geo/locales, Webinarkit custom conversion, optimization, attribution, MY regional fields from the BROAD MY 1017 ad set),
each with the 3 BEST CPA ads (V4 决定变少 · 年纪大 · 盖电脑) reusing their exact creatives (Webinarkit posts). Ad sets + ads ACTIVE.
Ban gate. Idempotent by name. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120251454705570329"
CNAME = "(Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120"
BUDGET = 15000
ADS = {"V4": ("120251840059300329", "1001334883061622_122128786599286543"),
       "年纪大": ("120251454702680329", "1001334883061622_122126499129286543"),
       "盖电脑": ("120251454701640329", "1001334883061622_122126499021286543")}
AUDS = [("Luxury Goods | MY 28+", ("luxury",)), ("Beer | MY 28+", ("beer", "alcohol")), ("Omakase | MY 28+", ("omakase", "wagyu"))]
SEARCH = ("act_2285351942292267", "act_759339046918885", "act_2282909119125229")


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
crid = {}
for k, (aid, post) in ADS.items():
    a = g.get_object(aid, "name,campaign{name},creative{id,effective_object_story_id,object_story_spec}")
    cr = a["creative"]
    assert cr.get("effective_object_story_id") == post and link_of(cr) == LINK, (k, cr)
    assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], (k, a["name"])
    crid[k] = (a["name"], cr["id"])
    print(f"  ad {k}: «{a['name']}» · creative {cr['id']} · post {post} · → Webinarkit ✅")
bs = g.get_object(TEMPLATE_SET, "name,targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
base = {k: bs["targeting"][k] for k in ("geo_locations", "locales") if k in bs["targeting"]}
print(f"  转化 «{ccv['name']}» {po['custom_conversion_id']} · geo {base['geo_locations'].get('countries')} · locales {base.get('locales')}")

sets_all = []
for ac in SEARCH:
    try:
        sets_all += [(ac, x) for x in g._get_all(ac + "/adsets", {"fields": "name,created_time,targeting,campaign{name}", "limit": "500"})]
    except Exception as exc:  # noqa: BLE001
        print(f"   (读不到 {ac}: {str(exc)[:70]})")
targets = {}
for sname, keys in AUDS:
    cands = [(ac, x) for ac, x in sets_all if any(k in x["name"].lower() or k in x["campaign"]["name"].lower() for k in keys)
             and (x.get("targeting") or {}).get("flexible_spec")]
    assert cands, f"⛔ 找不到 {sname} 的来源 ad set"
    ac, src = max(cands, key=lambda t: t[1]["created_time"])
    st = src["targeting"]
    t = dict(base, flexible_spec=st["flexible_spec"], age_min=28, age_max=65, targeting_automation={"advantage_audience": 0})
    if st.get("exclusions"):
        t["exclusions"] = st["exclusions"]
    targets[sname] = t
    ints = [i.get("name") for f in st["flexible_spec"] for i in (f.get("interests") or [])]
    beh = [i.get("name") for f in st["flexible_spec"] for i in (f.get("behaviors") or [])]
    print(f"  受众 {sname}: 复制自 {ac} «{src['campaign']['name']}» › «{src['name']}» ({src['id']}, {src['created_time'][:10]}) · 硬锁 28–65 · Advantage+ 关\n"
          f"      兴趣 {ints}" + (f" · 行为 {beh}" if beh else ""))

existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}")
for sname, _ in AUDS:
    print(f"      › «{sname}» ACTIVE · ads: " + " · ".join(v[0] for v in crid.values()))
if not CONFIRM:
    print("BUILD CBO DONE (dry-run)")
    raise SystemExit(0)

cid = existing[CNAME]["id"] if CNAME in existing else g.create_campaign(
    acct, name=CNAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[], buying_type="AUCTION",
    daily_budget=BUDGET, bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
time.sleep(4)
have = {x["name"]: x["id"] for x in g._get_all(cid + "/adsets", {"fields": "name", "limit": "20"})}
for sname, _ in AUDS:
    sid = have.get(sname) or g.create_adset(
        acct, name=sname, campaign_id=cid, status="ACTIVE", optimization_goal=bs["optimization_goal"], billing_event=bs["billing_event"],
        targeting=targets[sname], promoted_object=po, attribution_spec=bs.get("attribution_spec"),
        regional_regulated_categories=bs.get("regional_regulated_categories") or [],
        regional_regulation_identities=bs.get("regional_regulation_identities") or {})["id"]
    time.sleep(4)
    got = {x["name"] for x in g._get_all(sid + "/ads", {"fields": "name", "limit": "20"})}
    for name, cr in crid.values():
        if name not in got:
            g.create_ad(acct, name=name, adset_id=sid, creative={"creative_id": cr}, status="ACTIVE")
            time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "30"}):
    print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}")
print("BUILD CBO DONE")
