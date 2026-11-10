# -*- coding: utf-8 -*-
"""READ-ONLY read-back of the 11/10 NEW VIDEO build: for each of the 6 campaigns — status/objective/ABO; each ad set — budget,
age/Advantage+/geo/interests, promoted_object; each ad — status, creative video's own name == ad name == ad-set V#'s spec,
caption == approved copy, title == approved headline, link == -wed, url_tags present."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

LINK = "https://soochenginvesting.com/webinarkit-register-wed"
SPECS = {f"V{s['video']}": s for s in json.load(open(REPO_ROOT / "scripts" / "specs_newvideo_1110.json", encoding="utf-8"))}
# video ids written by execute_build_newvideo_1110 (runs 42795285614 + 42797509154), uploaded from the frame-verified Drive copies
VIDS = {"MY": {"V1": {"2900671390333546", "1838780207383506"}, "V2": {"3723167407831193", "2323494928505126"},
               "V3": {"1134674549541719", "4593716314247786"}, "V4": {"1477105421207566", "1616205366189722"},
               "V5": {"2143382679616242", "2216314555896899"}},
        "SG": {"V1": {"1488486326476294"}, "V2": {"2201912637410682"}, "V3": {"4219294225027138"},
               "V4": {"1453281277009637"}, "V5": {"2192956807955105"}}}
bad = 0
# 2nd pass (11/10): MY ×3 and SG Broad were read back ✅ in run 1; only re-check what the SG throttle cut off.
DONE = ("STOCKBLOOM | NEW VIDEO · News", "STOCKBLOOM | NEW VIDEO · Luxury Goods", "STOCKBLOOM | NEW VIDEO · Broad")


def T(fn, *a, **k):
    import time
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "request limit" not in str(e).lower():
                raise
            print(f"      … 限流，等 90s（{i + 1}/10）"); time.sleep(90)
    raise RuntimeError("throttled")
for key, cfg in (("SG", "config.sg.yaml"),):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    camps = [c for c in T(g._get_all, acct + "/campaigns", {"fields": "name,status,effective_status,objective,daily_budget", "limit": "500"})
             if "NEW VIDEO" in c["name"] and not any(x in c["name"] for x in DONE)]
    print(f"\n################ {key} · NEW VIDEO campaigns {len(camps)}")
    for c in sorted(camps, key=lambda x: x["name"]):
        print(f"  «{c['name']}» · {c['id']} · {c['status']}/{c['effective_status']} · {c['objective']} · campaign budget {c.get('daily_budget') or '无 (ABO)'}")
        if c["status"] != "PAUSED" or c.get("daily_budget"):
            bad += 1; print("    ❌ 应为 PAUSED + ABO")
        sets = T(g._get_all, c["id"] + "/adsets", {"fields": "name,status,daily_budget,targeting,promoted_object", "limit": "50"})
        for a in sorted(sets, key=lambda x: x["name"]):
            t = a["targeting"]
            ints = sum(len(sp.get("interests") or []) for sp in t.get("flexible_spec") or [])
            adv = (t.get("targeting_automation") or {}).get("advantage_audience")
            v = a["name"].split("· ")[-1]
            sp = SPECS.get(v)
            ads = T(g._get_all, a["id"] + "/ads", {"fields": "name,status,effective_status,creative{id,url_tags,object_story_spec}", "limit": "10"})
            line = (f"    › «{a['name']}» {a['id']} · RM{int(a['daily_budget']) // 100} · age {t.get('age_min')}-{t.get('age_max')}"
                    f"{' 建议' + str(t.get('age_range')) if t.get('age_range') else ' 硬锁'} · Adv+ {adv} · geo {t['geo_locations'].get('countries')} · "
                    f"兴趣 {ints} · conv {a['promoted_object'].get('custom_conversion_id')}")
            print(line)
            for ad in ads:
                vd = ad["creative"]["object_story_spec"]["video_data"]
                vname = next((k for k, ids in VIDS[key].items() if vd["video_id"] in ids), "?")
                lk = ((vd.get("call_to_action") or {}).get("value") or {}).get("link")
                ok = (sp and ad["name"] == sp["ad_name"] and vname == v and vd.get("message") == sp["caption"]
                      and vd.get("title") == sp["headline"] and lk == LINK and ad["creative"].get("url_tags"))
                bad += 0 if ok else 1
                print(f"        · ad {ad['id']} «{ad['name']}» {ad['status']}/{ad['effective_status']} · video {vd['video_id']}（上传自 {vname} 的视频） · "
                      f"文案 {len(vd.get('message') or '')} 字 · 标题 {vd.get('title')} · {'✅' if ok else '❌'}")
            if a["status"] != "ACTIVE" or int(a["daily_budget"]) != 5000 or len(ads) != 1:
                bad += 1; print("        ❌ ad set 状态/预算/广告数不对")
print(f"\n问题数 {bad}\nVERIFY NEWVIDEO DONE (read-only)")
