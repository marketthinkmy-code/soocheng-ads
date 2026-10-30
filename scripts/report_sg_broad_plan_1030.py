# -*- coding: utf-8 -*-
"""READ-ONLY planning for the owner's 10/30 SG broad build (「跑 broad，ALL LANG 关，确保建的广告都是 direct 去 webinarkit-wed 的 url」).
1) Destination audit: every SG creative we'd reuse + every LIVE SG ad → its link (CTA / link_data) and url_tags.
2) 年纪大 source: the MY 5.0 Webinarkit 年纪大 ads → video_id, CTA link, caption length; is the video readable (source) for an SG copy.
3) SG history of 年纪大 (any ad ever, incl. statuses — rejected?).
4) SG broad history: BROAD SG (中文) / BROAD SG · ALL LANG lifetime spend · reg · CPL, ad set targeting locales.
5) ALL LANG campaign to close: name + status (asserted at execute time)."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

WED = "webinarkit-register-wed"
SG_CR = {"Video：用我的方法": "1473832997895184", "Video：不选 forex 不选黄金": "1644593024032530",
         "Video：我跟你讲！": "1104962755787873", "Video：盖电脑，喂！": "1783486816241364"}
CR_F = "name,url_tags,object_story_id,effective_object_story_id,object_story_spec,asset_feed_spec"


def link_of(cr: dict) -> str:
    oss = cr.get("object_story_spec") or {}
    vd, ld = oss.get("video_data") or {}, oss.get("link_data") or {}
    l = ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or ld.get("link") \
        or ((ld.get("call_to_action") or {}).get("value") or {}).get("link")
    if not l and cr.get("asset_feed_spec"):
        l = ",".join(x.get("website_url", "") for x in cr["asset_feed_spec"].get("link_urls") or [])
    return l or f"(无 spec — post 复用 {cr.get('effective_object_story_id') or cr.get('object_story_id')})"


sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
gs, gm = graph_client(sg), graph_client(my)

print("① 目的地检查")
for n, cid in SG_CR.items():
    cr = gs.get_object(cid, CR_F)
    l = link_of(cr)
    print(f"   SG creative {cid} «{n}» → {l} {'✅' if WED in l else '❌'} · url_tags {'有' if cr.get('url_tags') else '无'}")
for a in gs._get_all(sg.meta.account_path + "/ads", {"fields": "name,effective_status,campaign{name},adset{name},creative{" + CR_F + "}", "limit": "1000"}):
    if a.get("effective_status") != "ACTIVE":
        continue
    l = link_of(a.get("creative") or {})
    print(f"   在跑 {a['campaign']['name'][:45]} › {a['adset']['name'][:28]} · {a['name']} · ad {a['id']} → {l[:70]} {'✅' if WED in l else '❌'}")

print("\n② MY 5.0 的 年纪大（来源）")
for a in gm._get_all(my.meta.account_path + "/ads", {"fields": "name,effective_status,campaign{name},creative{" + CR_F + "}", "limit": "1000"}):
    if "年纪大" not in a["name"]:
        continue
    cr = a.get("creative") or {}
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    print(f"   {a['campaign']['name'][:45]} · ad {a['id']} · {a['effective_status']} · creative {cr.get('id')} · video {vd.get('video_id')} · "
          f"caption {len(vd.get('message') or '')} 字 · → {link_of(cr)[:70]} · url_tags {'有' if cr.get('url_tags') else '无'}")
    if vd.get("video_id"):
        try:
            v = gm.get_object(vd["video_id"], "source,length,title")
            print(f"      video {vd['video_id']} 可读 source={'有' if v.get('source') else '无'} · {v.get('length')}s")
        except Exception as e:                                           # noqa: BLE001
            print(f"      video {vd['video_id']} 读不到: {str(e)[:80]}")

print("\n③ SG 历史上的 年纪大")
hits = [a for a in gs._get_all(sg.meta.account_path + "/ads", {"fields": "name,effective_status,created_time,campaign{name}", "limit": "2000"}) if "年纪大" in a["name"]]
for a in hits:
    print(f"   {a['campaign']['name'][:45]} · {a['name']} · ad {a['id']} · {a['effective_status']} · 建于 {a['created_time'][:10]}")
print(f"   共 {len(hits)} 支")
tok = "offsite_conversion.custom.1614065190214320"
lt = json.dumps({"since": "2026-10-16", "until": "2026-10-30"})
print("\n④ SG broad 历史（10/16 起）")
for r in gs._get_all(sg.meta.account_path + "/insights", {"fields": "campaign_id,campaign_name,spend,actions,reach,cpm", "level": "campaign", "time_range": lt, "limit": "200"}):
    if "BROAD" in r["campaign_name"] or "ALL LANG" in r["campaign_name"]:
        sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
        print(f"   «{r['campaign_name']}» · campaign {r['campaign_id']} · RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "") + f" · reach {r.get('reach')} · CPM {float(r.get('cpm') or 0):.0f}")
for sid in ("120249918193310521",):
    t = gs.get_object(sid, "name,effective_status,targeting")
    tt = t["targeting"]
    print(f"   adset {sid} «{t['name']}» {t['effective_status']} · locales {tt.get('locales')} · adv+ {(tt.get('targeting_automation') or {}).get('advantage_audience')} · age {tt.get('age_min')}-{tt.get('age_max')} range {tt.get('age_range')}")
c = gs.get_object("120250072526350521", "name,effective_status,daily_budget")
print(f"\n⑤ 要关的 ALL LANG: «{c['name']}» · campaign 120250072526350521 · {c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100}")
print("\nSG BROAD PLAN DONE (read-only)")
