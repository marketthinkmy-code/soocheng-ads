# -*- coding: utf-8 -*-
"""owner 2026-10-30 — two NEW SG campaigns, created PAUSED (owner reviews + activates in Ads Manager). ALL LANG stays (owner「都留着」).
  A «(Webinarkit) [SG] STOCKBLOOM | BROAD SG | 1-1-5 | 1030» CBO RM100 — «Broad | SG 28+»: SG, locales from the SG Broad ad set,
     Advantage+ ON, age_range [28,65] suggestion. Ads: freestyle: korea · 不选 forex 不选黄金 · 年纪大的人做不了交易？ · 用我的方法 · 我跟你讲！
  B «(Webinarkit) [SG] STOCKBLOOM | TRAVEL SG | 1-1-2 | 1030» CBO RM50 (owner 10/30 RM40→50; separate campaign, owner「另外开 campaign，不要参在一起」) —
     «Travel | SG 28+»: interests cloned from the 10/17 Webinarkit TRAVEL ad set, age 28-65 hard, Advantage+ off.
     Ads: 盖电脑，喂！ · 年纪大的人做不了交易？
Why (Paid Student List, +65 phones): Broad SG = #1 source of SG students (22), TRAVEL SG = #2 (18, 盖电脑 ×8).
Every creative must link straight to https://soochenginvesting.com/webinarkit-register-wed (asserted). 年纪大 never had a
Webinarkit SG creative → its MY 5.0 Webinarkit video is copied into the SG ad account (file_url) and a new creative is made
with the same approved caption + SG url_tags. korea: an existing SG creative that links to -wed, else copied from MY the same way.
Ban gate. Idempotent by name. CONFIRM=true writes; dry-run prints the full plan."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
DT_SET, BROAD_SET = "120250027170880521", "120249918193310521"     # live DAY TRADING SG (promoted object etc.) · SG Broad 28+ (locales)
TRAVEL_CAMP = "(Webinarkit) [SG] STOCKBLOOM | TRAVEL | 1-1-5 | 1017"
SG_CR = {"Video：用我的方法": "1473832997895184", "Video：不选 forex 不选黄金": "1644593024032530",
         "Video：我跟你讲！": "1104962755787873", "Video：盖电脑，喂！": "1783486816241364"}
OLD = "Video：年纪大的人做不了交易？"
KOREA = "freestyle: korea"
MY_SRC = {OLD: "2167823877450518"}            # MY 5.0 Webinarkit creative (DAY TRADING, ACTIVE) — video + caption + link -wed
BUILDS = [("(Webinarkit) [SG] STOCKBLOOM | BROAD SG | 1-1-5 | 1030", "Broad | SG 28+", "broad", 10000,
           [KOREA, "Video：不选 forex 不选黄金", OLD, "Video：用我的方法", "Video：我跟你讲！"]),
          ("(Webinarkit) [SG] STOCKBLOOM | TRAVEL SG | 1-1-2 | 1030", "Travel | SG 28+", "travel", 5000,
           ["Video：盖电脑，喂！", OLD])]


def link_of(cr: dict) -> str:
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or ""


def main() -> None:
    sg, my = load_settings(REPO_ROOT / "config" / "config.sg.yaml"), load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g, gm = graph_client(sg), graph_client(my)
    acct = sg.meta.account_path
    assert acct.endswith("893025326577600")
    print(f"SG BROAD + TRAVEL build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    names = sorted({a for *_, ads in BUILDS for a in ads})
    hits = compliance.filter_banned(names, sg.compliance.banned_creatives)
    assert not hits, f"⛔ 禁跑命中: {hits}"
    print(f"  禁跑闸 ✅ {names}")

    # ── creatives ──
    cr, need_copy = {}, {}
    ref = g.get_object(SG_CR["Video：用我的方法"], "url_tags,object_story_spec")
    url_tags = ref["url_tags"]
    page, ig = ref["object_story_spec"]["page_id"], ref["object_story_spec"].get("instagram_user_id")
    for n, cid in SG_CR.items():
        l = link_of(g.get_object(cid, "object_story_spec"))
        assert l == LINK, f"{n} creative {cid} links to {l}"
        cr[n] = cid
        print(f"  {n}: SG creative {cid} → {l} ✅")
    ko = [a for a in g._get_all(acct + "/ads", {"fields": "name,effective_status,creative{id,object_story_spec,url_tags}", "limit": "2000"})
          if "korea" in a["name"].lower() and "🚫" not in a["name"]]
    ok = [a for a in ko if link_of(a.get("creative") or {}) == LINK and a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES")]
    print(f"  {KOREA}: SG 现有 korea ad {len(ko)} 支 · 其中直接连 -wed 且没被拒 {len(ok)} 支")
    for a in ko:
        print(f"      ad {a['id']} «{a['name']}» {a['effective_status']} · creative {a['creative']['id']} → {link_of(a['creative']) or '(post 复用/无链接)'}")
    if ok:
        cr[KOREA] = ok[0]["creative"]["id"]
        print(f"    → 用 SG creative {cr[KOREA]}")
    else:
        mk = [a for a in gm._get_all(my.meta.account_path + "/ads", {"fields": "name,effective_status,creative{id,object_story_spec}", "limit": "1000"})
              if "korea" in a["name"].lower() and link_of(a.get("creative") or {}) == LINK
              and ((a["creative"].get("object_story_spec") or {}).get("video_data") or {}).get("video_id")]
        assert mk, "no MY korea creative linking to -wed"
        MY_SRC[KOREA] = mk[0]["creative"]["id"]
        print(f"    → SG 没有干净的 -wed 版本，从 MY creative {MY_SRC[KOREA]}（ad {mk[0]['id']}）复制")
    for n, mcid in MY_SRC.items():
        c = gm.get_object(mcid, "object_story_spec,body")
        vd = c["object_story_spec"]["video_data"]
        msg = vd.get("message") or c.get("body") or ""      # korea keeps its caption in `body` (single approved text; no AI text variants)
        assert len(msg) > 100, f"MY {n} creative {mcid} has no caption"
        assert link_of(c) == LINK, f"MY {n} creative {mcid} links to {link_of(c)}"
        src = gm.get_object(vd["video_id"], "source,length")
        assert src.get("source"), f"MY video {vd['video_id']} source unreadable"
        need_copy[n] = {"video_id": vd["video_id"], "message": msg, "source": src["source"]}
        print(f"  {n}: 从 MY creative {mcid} 复制 · video {vd['video_id']} {src.get('length')}s · 文案 {len(msg)} 字 «{msg[:30]}…» · → {LINK} ✅")

    # ── targeting ──
    dt = g.get_object(DT_SET, "promoted_object,optimization_goal,billing_event,attribution_spec,regional_regulated_categories,regional_regulation_identities")
    bt = g.get_object(BROAD_SET, "targeting")["targeting"]
    broad_t = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
    broad_t.update({"age_min": bt.get("age_min", 25), "age_max": 65, "age_range": [28, 65], "targeting_automation": {"advantage_audience": 1}})
    camps = {c["name"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "300"})}
    tc = camps.get(TRAVEL_CAMP)
    assert tc, f"source «{TRAVEL_CAMP}» not found"
    ts = g._get_all(tc["id"] + "/adsets", {"fields": "name,targeting", "limit": "5"})[0]
    tt = ts["targeting"]
    travel_t = {k: tt[k] for k in ("geo_locations", "locales", "flexible_spec") if k in tt}
    assert travel_t.get("flexible_spec"), "travel source has no interests"
    travel_t.update({"age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}})
    ints = [i.get("name") for spec in travel_t["flexible_spec"] for i in (spec.get("interests") or [])]
    print(f"\n  Broad 受众: geo {broad_t['geo_locations'].get('countries')} · locales {broad_t.get('locales')} · Advantage+ 开 · age_range {broad_t['age_range']}")
    print(f"  Travel 受众（复制自 «{TRAVEL_CAMP}» › {ts['name']}，campaign {tc['id']} 现 {tc['effective_status']}）: "
          f"geo {travel_t['geo_locations'].get('countries')} · locales {travel_t.get('locales')} · age 28-65 硬锁 · Advantage+ 关 · 兴趣 {len(ints)}: {ints}")
    po = dt["promoted_object"]
    cc = g.get_object(po["custom_conversion_id"], "name,rule,custom_event_type,is_archived,pixel{id,name},last_fired_time")
    px = g.get_object(po["pixel_id"], "name,last_fired_time")
    print(f"  转化（owner「check 好 pixel 都是 webinarkit 的」）: pixel {po['pixel_id']} «{px.get('name')}» 最后触发 {px.get('last_fired_time')} · "
          f"custom conversion {po['custom_conversion_id']} «{cc.get('name')}» · 归档 {cc.get('is_archived')} · 最后触发 {cc.get('last_fired_time')}\n"
          f"      规则 {cc.get('rule')}")
    assert "webinarkit" in (cc.get("name") or "").lower() and "webinarkit-thankyou" in (cc.get("rule") or ""), "conversion is not the Webinarkit one"
    assert (cc.get("pixel") or {}).get("id") in (None, po["pixel_id"]) and not cc.get("is_archived"), "conversion pixel mismatch / archived"
    print(f"      ✅ Webinarkit 报名转化 · regional {dt.get('regional_regulated_categories')}")

    tmap = {"broad": broad_t, "travel": travel_t}
    for cname, sname, mode, cents, ads in BUILDS:
        print(f"\n  ▶ «{cname}» CBO RM{cents // 100} · PAUSED · 已存在 {cname in camps}\n    › «{sname}»\n" + "".join(f"        · {a}\n" for a in ads), end="")
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nBUILD DONE (dry-run)"); return

    have_cr = {c.get("name"): c["id"] for c in g._get_all(acct + "/adcreatives", {"fields": "id,name", "limit": "1000"})}
    for n, d in need_copy.items():
        nm = f"{n} · webinarkit-wed · SG"
        if nm in have_cr:
            cr[n] = have_cr[nm]; continue
        vid = g._request("POST", acct + "/advideos", data={"file_url": d["source"], "name": n})["id"]
        g._wait_video_ready(vid, 5, 900)
        thumb = g.get_video_thumbnail(vid)
        vd = {"video_id": vid, "message": d["message"], "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        if thumb:
            vd["image_url"] = thumb
        oss = {"page_id": page, "video_data": vd}
        if ig:
            oss["instagram_user_id"] = ig
        cr[n] = g.create_adcreative(acct, name=nm, url_tags=url_tags, object_story_spec=oss)["id"]
        assert link_of(g.get_object(cr[n], "object_story_spec")) == LINK
        print(f"  ✅ {n}: SG video {vid} · creative {cr[n]} → {LINK}"); time.sleep(2)
    for cname, sname, mode, cents, ads in BUILDS:
        if cname in camps:
            print(f"  = «{cname}» 已存在 — skip"); continue
        cid = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                                daily_budget=cents, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")["id"]
        time.sleep(2)
        a = g.create_adset(acct, name=sname, campaign_id=cid, status="ACTIVE", optimization_goal=dt["optimization_goal"],
                           billing_event=dt["billing_event"], targeting=tmap[mode], promoted_object=dt["promoted_object"],
                           attribution_spec=dt.get("attribution_spec"),
                           regional_regulated_categories=dt["regional_regulated_categories"],
                           regional_regulation_identities=dt["regional_regulation_identities"])["id"]
        time.sleep(2)
        ids = []
        for n in ads:
            ids.append(g.create_ad(acct, name=n, adset_id=a, creative={"creative_id": cr[n]}, status="ACTIVE")["id"]); time.sleep(2)
        print(f"  ✅ «{cname}» campaign {cid} (PAUSED, RM{cents // 100}) · adset {a} · ads {dict(zip(ads, ids))}")
    print("BUILD DONE")


if __name__ == "__main__":
    main()
