# -*- coding: utf-8 -*-
"""owner 2026-11-26「winning ads try different ads set」→ 选「① ② 都建」· ① = winning ads × new audiences. SG account:
(Webinarkit) [SG] STOCKBLOOM | CBO · BO NEWS BEER | 1-3-3 | 1126 — CBO RM100/day, campaign PAUSED (owner reviews + switches it on),
3 ad sets (Business Owner | SG 28+ · News | SG 28+ · Beer | SG 28+), interests cloned from the SG source ad set of each audience, hard age
28–65, Advantage+ audience off; conversion / optimization / attribution / regional fields from SG BROAD SG 1030 › Broad | SG 28+.
Each ad set: 用我的方法 · 年纪大 · 决定变少, reusing the existing SG creative of the best SG position of each (same post, same url_tags):
年纪大 = SG BROAD SG 1030 ad 120250144813480521 (1 sale) · 用我的方法 = SG BROAD SG 1030 ad 120250144813920521 (1 sale) ·
决定变少 = SG NEW VIDEO · Broad V4 ad 120250544546540521 (10 real regs). Placements NOT written (owner sets them in Ads Manager).
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
CNAME = "(Webinarkit) [SG] STOCKBLOOM | CBO · BO NEWS BEER | 1-3-3 | 1126"
BUDGET = 10000
SRC_ADS = ["120250144813920521", "120250144813480521", "120250544546540521"]   # 用我的方法 · 年纪大 · 决定变少
AUDS = [("Business Owner | SG 28+", "120250027167510521"), ("News | SG 28+", "120248231209470521"), ("Beer | SG 28+", "120248577893780521")]
KEEP = ("flexible_spec", "exclusions", "excluded_custom_audiences")
BAD = ("DISAPPROVED", "WITH_ISSUES")


def link_of(cr):
    oss = cr.get("object_story_spec") or {}
    vd = oss.get("video_data") or oss.get("link_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN")
ads = []
for aid in SRC_ADS:
    a = g.get_object(aid, "name,effective_status,campaign{name},adset{name},creative{id,effective_object_story_id,object_story_spec,url_tags}")
    cr = a["creative"]
    cr = dict(cr, **g.get_object(cr["id"], "effective_object_story_id,object_story_spec,url_tags"))
    nm = a["name"]
    assert not compliance.is_banned(nm, s.compliance.banned_creatives) and "🚫" not in nm, nm
    assert a["effective_status"] not in BAD, (nm, a["effective_status"])
    lk = link_of(cr)
    assert lk == LINK, (nm, lk)
    ads.append((nm, cr["id"]))
    print(f"  ad «{nm}» · 来源 {a['campaign']['name']} › {a['adset']['name']} · ad {aid} ({a['effective_status']}) · SG creative {cr['id']}"
          f" · post {cr.get('effective_object_story_id')} · → Webinarkit ✅ · url_tags {'有' if cr.get('url_tags') else '无'}")
bs = g.get_object(TEMPLATE_SET, "name,campaign{name},targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
po = bs["promoted_object"]
ccv = g.get_object(po["custom_conversion_id"], "name,is_archived")
assert "webinarkit" in (ccv.get("name") or "").lower() and not ccv.get("is_archived"), ccv
base = {k: bs["targeting"][k] for k in ("geo_locations", "locales") if k in bs["targeting"]}
print(f"  模板 «{bs['campaign']['name']}» › «{bs['name']}» · 转化 «{ccv['name']}» · geo {base['geo_locations'].get('countries')} · locales {base.get('locales')}")
targets = {}
for sname, src_id in AUDS:
    src = g.get_object(src_id, "name,created_time,targeting,campaign{name}")
    st = src["targeting"]
    assert st.get("flexible_spec"), (sname, "no interests")
    t = dict(base, **{k: st[k] for k in KEEP if k in st})
    t.update(age_min=28, age_max=65, targeting_automation={"advantage_audience": 0})
    targets[sname] = t
    ints = [i.get("name") for f in st["flexible_spec"] for k in ("interests", "behaviors", "work_positions", "industries") for i in (f.get(k) or [])]
    print(f"  受众 {sname}: 复制自 «{src['campaign']['name']}» › «{src['name']}» ({src_id}, {src['created_time'][:10]}，原年龄 "
          f"{st.get('age_min')}–{st.get('age_max')}) → 硬锁 28–65 · Advantage+ 关 · 兴趣 {len(ints)}：{', '.join(ints[:8])}{' …' if len(ints) > 8 else ''}")
existing = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "500"})}
print(f"  ▶ «{CNAME}» · CBO RM{BUDGET // 100}/天 · PAUSED · 已存在 {CNAME in existing}")
for sname, _ in AUDS:
    print(f"      › «{sname}» ACTIVE · ads: " + " · ".join(n for n, _ in ads))
if not CONFIRM:
    print("BUILD SG NEW AUDIENCES DONE (dry-run)")
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
    for nm, crid in ads:
        if nm not in got:
            g.create_ad(acct, name=nm, adset_id=sid, creative={"creative_id": crid}, status="ACTIVE")
            time.sleep(4)
c = g.get_object(cid, "name,status,effective_status,daily_budget")
assert c["status"] == "PAUSED", c
print(f"  ✅ «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
for x in g._get_all(cid + "/adsets", {"fields": "name,status,targeting", "limit": "20"}):
    t = x["targeting"]
    print(f"      ad set «{x['name']}» · adset {x['id']} · {x['status']} · 年龄 {t.get('age_min')}–{t.get('age_max')} · "
          f"Advantage+ {(t.get('targeting_automation') or {}).get('advantage_audience')}")
for a in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name},creative{effective_object_story_id}", "limit": "30"}):
    print(f"      › {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']} · post {(a.get('creative') or {}).get('effective_object_story_id')}")
print("BUILD SG NEW AUDIENCES DONE")
