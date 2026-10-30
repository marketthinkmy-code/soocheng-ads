# -*- coding: utf-8 -*-
"""READ-ONLY: the two 10/30 SG builds after the owner activated them — campaign/ad set/ad status, review state,
budget, link, today's spend/reg. Plus SG live budget total."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CAMPS = ("120250144810670521", "120250144814410521")
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
tok = "offsite_conversion.custom.1614065190214320"
for cid in CAMPS:
    c = g.get_object(cid, "name,status,effective_status,daily_budget,start_time")
    print(f"«{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100}")
    for a in g._get_all(cid + "/adsets", {"fields": "name,status,effective_status,targeting", "limit": "10"}):
        t = a["targeting"]
        print(f"  › {a['name']} · adset {a['id']} · {a['status']}/{a['effective_status']} · age {t.get('age_min')}-{t.get('age_max')} range {t.get('age_range')} · adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')}")
    perf = {r["ad_id"]: r for r in g._get_all(cid + "/insights", {"fields": "ad_id,spend,impressions,actions", "level": "ad", "time_range": json.dumps({"since": today, "until": today})})}
    for x in g._get_all(cid + "/ads", {"fields": "name,status,effective_status,ad_review_feedback,issues_info,creative{object_story_spec}", "limit": "20"}):
        vd = ((x.get("creative") or {}).get("object_story_spec") or {}).get("video_data") or {}
        link = ((vd.get("call_to_action") or {}).get("value") or {}).get("link", "")
        r = perf.get(x["id"], {})
        fb = x.get("ad_review_feedback") or x.get("issues_info") or ""
        print(f"     · {x['name']} · ad {x['id']} · {x['status']}/{x['effective_status']} · {'wed ✅' if link.endswith('webinarkit-register-wed') else link} · "
              f"今天 RM{float(r.get('spend') or 0):.2f} / {r.get('impressions', 0)} 曝光 / {extract_results(r.get('actions'), tok):.0f} 报名" + (f" · ⚠️ {str(fb)[:120]}" if fb else ""))
tot = 0
for c in g._get_all(s.meta.account_path + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "300"}):
    if c["effective_status"] == "ACTIVE":
        tot += int(c.get("daily_budget") or 0) // 100
        print(f"  在跑 CBO RM{int(c.get('daily_budget') or 0) // 100:<4} «{c['name']}»")
print(f"SG 在跑 campaign 层日预算合计 RM{tot}（ABO 不计）")
print("SG NEW DONE (read-only)")
