# -*- coding: utf-8 -*-
"""READ-ONLY (11/5 morning watch found 6 SG ads DISAPPROVED at 11/05 04:16, all in OLD paused campaigns).
SG + MY 5.0 account status; each DISAPPROVED ad: position, status, review feedback, creative video id + caption head;
then every LIVE ad on both accounts: video id, and whether that video id / creative id equals a rejected one."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

F = "name,status,effective_status,updated_time,ad_review_feedback,campaign{name,status},adset{name},creative{id,body,effective_object_story_id,object_story_spec,video_id}"


def vid(cr):
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    return vd.get("video_id") or cr.get("video_id")


def cap(cr):
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    return (vd.get("message") or cr.get("body") or "").replace("\n", " ")


rej_vids, rej_posts = {}, {}
for label, cfg in (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    a = g._request("GET", s.meta.account_path, params={"fields": "account_status,disable_reason,name"})
    print(f"\n## {label} «{a.get('name')}» account_status={a.get('account_status')} disable_reason={a.get('disable_reason')}")
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": F, "limit": "2000"})
    for x in ads:
        if x.get("effective_status") in ("DISAPPROVED", "WITH_ISSUES"):
            cr = x.get("creative") or {}
            v = vid(cr)
            rej_vids[v] = x["name"]
            rej_posts[cr.get("effective_object_story_id")] = x["name"]
            print(f"  ✖ {x['effective_status']} {x['updated_time'][:16]} · {x['campaign']['name']}({x['campaign']['status']}) › {x['adset']['name']} · {x['name']} · ad {x['id']}\n"
                  f"     video {v} · post {cr.get('effective_object_story_id')} · 原因 {json.dumps(x.get('ad_review_feedback') or {}, ensure_ascii=False)[:300]}\n"
                  f"     文案开头 «{cap(cr)[:90]}»")
    print(f"  在跑的 ad:")
    for x in ads:
        if x.get("effective_status") != "ACTIVE":
            continue
        cr = x.get("creative") or {}
        v = vid(cr)
        same = rej_vids.get(v) or rej_posts.get(cr.get("effective_object_story_id"))
        print(f"   · {x['campaign']['name'][:45]} › {x['adset']['name'][:22]} · {x['name']} · ad {x['id']} · video {v}" + (f"  ⚠️ 同一支视频/post 被拒: «{same}»" if same else ""))
print("\nSG REJECTS DONE (read-only)")
