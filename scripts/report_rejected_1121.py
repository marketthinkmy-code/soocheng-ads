# -*- coding: utf-8 -*-
"""READ-ONLY (2026-11-21 10:3x). report_live_budget_1120 flagged 2 SG ads DISAPPROVED:
  [SG] LOW CPL · Broad | 1-1-3 | 1120 › Broad | SG 28+ · 炒了五年 · ad 120250706569810521
  [SG] BROAD SG | 1-1-5 | 1030 › Broad | SG 28+ · 我跟你讲 · ad 120250144814180521
Print each one's review feedback + creative video id, then list EVERY copy (same name keyword OR same video id) in MY 5.0 + SG
with campaign › ad set · ad ID, status / effective_status and parent status — so the owner can decide (9/23 rule: rejected = 永久禁跑)."""
import datetime as dt
import json

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
REJ = {"120250706569810521": "炒了五年", "120250144814180521": "我跟你讲"}
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读")
gs = {}
for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    gs[lab] = (graph_client(s), s.meta.account_path)

g_sg = gs["SG"][0]
gs_banned = load_settings(REPO_ROOT / "config" / "config.sg.yaml").compliance.banned_creatives
vids = {}
for aid, kw in REJ.items():
    a = g_sg.get_object(aid, "name,status,effective_status,updated_time,ad_review_feedback,issues_info,"
                             "creative{id,video_id,object_story_id,effective_object_story_id,object_story_spec},"
                             "adset{name,status},campaign{name,status}")
    cr = a.get("creative") or {}
    vid = cr.get("video_id") or ((cr.get("object_story_spec") or {}).get("video_data") or {}).get("video_id")
    vids[kw] = vid
    print(f"\n=== {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid}")
    print(f"    status {a['status']} / effective {a['effective_status']} · updated {a.get('updated_time')}")
    print(f"    review_feedback: {json.dumps(a.get('ad_review_feedback'), ensure_ascii=False)}")
    if a.get("issues_info"):
        print(f"    issues_info: {json.dumps(a.get('issues_info'), ensure_ascii=False)[:600]}")
    print(f"    creative {cr.get('id')} · video {vid} · post {cr.get('effective_object_story_id')}")
    print(f"    is_banned(name) now: {compliance.is_banned(a['name'], gs_banned)}")

for kw, vid in vids.items():
    print(f"\n######## 所有副本：「{kw}」（名字含关键字，或同 video id {vid}）")
    for lab, (g, acct) in gs.items():
        rows = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,creative{video_id,object_story_spec},"
                                                    "adset{id,name,status},campaign{id,name,status}", "limit": "500"})
        hit = []
        for r in rows:
            cr = r.get("creative") or {}
            v = cr.get("video_id") or ((cr.get("object_story_spec") or {}).get("video_data") or {}).get("video_id")
            if kw in r["name"] or (vid and v == vid):
                hit.append((r, v))
        print(f"  [{lab}] {len(hit)} 支")
        for r, v in sorted(hit, key=lambda x: (x[0]["effective_status"] != "ACTIVE", x[0]["campaign"]["name"])):
            c, s_ = r["campaign"], r["adset"]
            live = "🟢在投放" if r["effective_status"] == "ACTIVE" else ""
            print(f"    {live}{c['name']} [{c['status']}] › {s_['name']} [{s_['status']}] · {r['name']} · ad {r['id']}"
                  f" · ad {r['status']}/{r['effective_status']} · video {v}{' (同母带)' if vid and v == vid else ''}")
print("\nREJECTED 1121 DONE (read-only)")
