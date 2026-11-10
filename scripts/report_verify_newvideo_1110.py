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
bad = 0
for key, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    camps = [c for c in g._get_all(acct + "/campaigns", {"fields": "name,status,effective_status,objective,daily_budget", "limit": "500"})
             if "NEW VIDEO" in c["name"]]
    print(f"\n################ {key} · NEW VIDEO campaigns {len(camps)}")
    for c in sorted(camps, key=lambda x: x["name"]):
        print(f"  «{c['name']}» · {c['id']} · {c['status']}/{c['effective_status']} · {c['objective']} · campaign budget {c.get('daily_budget') or '无 (ABO)'}")
        if c["status"] != "PAUSED" or c.get("daily_budget"):
            bad += 1; print("    ❌ 应为 PAUSED + ABO")
        sets = g._get_all(c["id"] + "/adsets", {"fields": "name,status,daily_budget,targeting,promoted_object", "limit": "50"})
        for a in sorted(sets, key=lambda x: x["name"]):
            t = a["targeting"]
            ints = sum(len(sp.get("interests") or []) for sp in t.get("flexible_spec") or [])
            adv = (t.get("targeting_automation") or {}).get("advantage_audience")
            v = a["name"].split("· ")[-1]
            sp = SPECS.get(v)
            ads = g._get_all(a["id"] + "/ads", {"fields": "name,status,effective_status,creative{id,url_tags,object_story_spec}", "limit": "10"})
            line = (f"    › «{a['name']}» {a['id']} · RM{int(a['daily_budget']) // 100} · age {t.get('age_min')}-{t.get('age_max')}"
                    f"{' 建议' + str(t.get('age_range')) if t.get('age_range') else ' 硬锁'} · Adv+ {adv} · geo {t['geo_locations'].get('countries')} · "
                    f"兴趣 {ints} · conv {a['promoted_object'].get('custom_conversion_id')}")
            print(line)
            for ad in ads:
                vd = ad["creative"]["object_story_spec"]["video_data"]
                vname = g.get_object(vd["video_id"], "title").get("title")
                lk = ((vd.get("call_to_action") or {}).get("value") or {}).get("link")
                ok = (sp and ad["name"] == sp["ad_name"] and vname == sp["ad_name"] and vd.get("message") == sp["caption"]
                      and vd.get("title") == sp["headline"] and lk == LINK and ad["creative"].get("url_tags"))
                bad += 0 if ok else 1
                print(f"        · ad {ad['id']} «{ad['name']}» {ad['status']}/{ad['effective_status']} · video {vd['video_id']} «{vname}» · "
                      f"文案 {len(vd.get('message') or '')} 字 · 标题 {vd.get('title')} · {'✅' if ok else '❌'}")
            if a["status"] != "ACTIVE" or int(a["daily_budget"]) != 5000 or len(ads) != 1:
                bad += 1; print("        ❌ ad set 状态/预算/广告数不对")
print(f"\n问题数 {bad}\nVERIFY NEWVIDEO DONE (read-only)")
