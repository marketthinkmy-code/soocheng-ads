# -*- coding: utf-8 -*-
"""owner 2026-11-19「两个 1-1-3：在 MY 5.0 开两个 campaign，放 3 支 Webinarkit ad，受众 Broad MY 28+，预算 RM100/天，建好后是 PAUSED，
等你看过再开」+ 分组「按成绩分」:
  ① (Webinarkit) STOCKBLOOM | BEST CPA · Broad | 1-1-3 | 1120 — V4 决定变少 · 年纪大（MY BO post）· 盖电脑
  ② (Webinarkit) STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120  — korea · V2 炒了五年 · 用我的方法（SG post, 2 sales）
Each: CBO RM100/day, campaign PAUSED (owner switches it on), 1 ad set «Broad | MY 28+» (Advantage+ on, age_range 28–65, geo/locales,
Webinarkit custom conversion, optimization, attribution and MY regional-regulation fields copied from the BROAD MY 1017 ad set), ad set + ads
ACTIVE so only the campaign switch is left. Ads reuse the exact creative of the source ad (same Webinarkit post, url_tags, IG); the SG-only
post gets a new MY creative with object_story_id + the same url_tags/IG. Every post is asserted to link to webinarkit-register-wed.
Ban gate. Idempotent by name. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
TEMPLATE_SET = "120251454705570329"     # (Webinarkit) STOCKBLOOM | BROAD MY | 1-1-5 | 1017 › Broad | MY 28+
BUDGET = 10000                          # RM100/day per campaign (CBO)
# (account, source ad id, expected post id)
SRC = {
    "V4": ("MY", "120251840059300329", "1001334883061622_122128786599286543"),
    "年纪大": ("MY", "120251454702680329", "1001334883061622_122126499129286543"),
    "盖电脑": ("MY", "120251454701640329", "1001334883061622_122126499021286543"),
    "korea": ("MY", "120251456191090329", "1001334883061622_122126499027286543"),
    "V2": ("MY", "120251840432100329", "1001334883061622_122128786629286543"),
    "用我的方法": ("SG", "120250144813920521", "1001334883061622_122126501961286543"),
}
CAMPS = [("(Webinarkit) STOCKBLOOM | BEST CPA · Broad | 1-1-3 | 1120", ["V4", "年纪大", "盖电脑"]),
         ("(Webinarkit) STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120", ["korea", "V2", "用我的方法"])]
ASET = "Broad | MY 28+"


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
gsg = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")

src = {}
for k, (where, aid, post) in SRC.items():
    gg = g if where == "MY" else gsg
    a = gg.get_object(aid, "name,campaign{name},adset{name},creative{id,effective_object_story_id,object_story_spec,url_tags}")
    cr = a["creative"]
    assert cr.get("effective_object_story_id") == post, (k, cr.get("effective_object_story_id"))
    assert link_of(cr) == LINK, (k, link_of(cr))
    assert a["campaign"]["name"].lower().startswith("(webinarkit)"), (k, a["campaign"]["name"])
    assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], (k, a["name"])
    src[k] = (where, a, cr)
    print(f"  {k}: 来源 {where} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · creative {cr['id']} · post {post} · → {LINK} ✅")

ref_oss = src["V4"][2]["object_story_spec"]
ig, url_tags = ref_oss.get("instagram_user_id"), src["V4"][2].get("url_tags")
bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,rule,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
bt = bs["targeting"]
targeting = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
targeting.update(age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
print(f"  模板 ad set «{bs['campaign']['name']}» › «{bs['name']}» {TEMPLATE_SET} · 转化 «{ccv['name']}» {po['custom_conversion_id']} · "
      f"opt {bs['optimization_goal']} · geo {targeting['geo_locations'].get('countries')} · locales {targeting.get('locales')} · Advantage+ 开 · 建议 28–65")
print(f"  url_tags {url_tags} · ig {ig}")

existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,status", "limit": "500"})}
for cname, keys in CAMPS:
    print(f"  ▶ «{cname}» · CBO RM{BUDGET // 100}/天 · campaign PAUSED · 已存在 {cname in existing}")
    print(f"      › «{ASET}» ACTIVE · ads: " + " · ".join(f"{src[k][1]['name']}" for k in keys))
if not CONFIRM:
    print("BUILD 1-1-3 DONE (dry-run)")
    raise SystemExit(0)

# creative for the SG-only post first — if Meta refuses it, nothing else gets built
crid = {k: src[k][2]["id"] for k in SRC if src[k][0] == "MY"}
mine = {c.get("name"): c for c in g._get_all(acct + "/adcreatives", {"fields": "id,name,effective_object_story_id", "limit": "3000"})}
nm = "用我的方法 · post 122126501961286543 · MY"
if nm in mine and mine[nm].get("effective_object_story_id") == SRC["用我的方法"][2]:
    crid["用我的方法"] = mine[nm]["id"]
else:
    fields = dict(name=nm, object_story_id=SRC["用我的方法"][2], url_tags=url_tags)
    try:
        crid["用我的方法"] = g.create_adcreative(acct, instagram_user_id=ig, **fields)["id"] if ig else g.create_adcreative(acct, **fields)["id"]
    except Exception as exc:  # noqa: BLE001
        print(f"  (带 IG 建素材失败：{str(exc)[:120]} — 改不带 IG 再试)")
        crid["用我的方法"] = g.create_adcreative(acct, **fields)["id"]
    time.sleep(3)
chk = g.get_object(crid["用我的方法"], "effective_object_story_id,url_tags")
assert chk.get("effective_object_story_id") == SRC["用我的方法"][2], chk
print(f"  ✅ 用我的方法 MY creative {crid['用我的方法']} · post {chk['effective_object_story_id']}")

for cname, keys in CAMPS:
    if cname in existing:
        cid = existing[cname]["id"]
        print(f"  = «{cname}» 已存在 {cid}")
    else:
        cid = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                                buying_type="AUCTION", daily_budget=BUDGET, bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        time.sleep(4)
    sets = {x["name"]: x["id"] for x in g._get_all(cid + "/adsets", {"fields": "name", "limit": "20"})}
    if ASET in sets:
        sid = sets[ASET]
    else:
        sid = g.create_adset(acct, name=ASET, campaign_id=cid, status="ACTIVE", optimization_goal=bs["optimization_goal"],
                             billing_event=bs["billing_event"], targeting=targeting, promoted_object=po,
                             attribution_spec=bs.get("attribution_spec"),
                             regional_regulated_categories=bs.get("regional_regulated_categories") or [],
                             regional_regulation_identities=bs.get("regional_regulation_identities") or {})["id"]
        time.sleep(4)
    have = {x["name"] for x in g._get_all(sid + "/ads", {"fields": "name", "limit": "20"})}
    for k in keys:
        an = src[k][1]["name"]
        if an not in have:
            g.create_ad(acct, name=an, adset_id=sid, creative={"creative_id": crid[k]}, status="ACTIVE")
            time.sleep(4)
    c = g.get_object(cid, "name,status,effective_status,daily_budget")
    print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
    for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status},creative{effective_object_story_id}", "limit": "20"}):
        print(f"      › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}"
              f" · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD 1-1-3 DONE")
