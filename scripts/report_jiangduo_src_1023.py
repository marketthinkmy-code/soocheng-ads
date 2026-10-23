# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-23: «video 1: 用我的方法，你也可以有将多» is a post-reuse creative (no video_data). Try the
creative's own fields (video_id/body/title/thumbnail) and the post's attachments to find the video id + caption."""
from __future__ import annotations

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

for cfg in ("config.yaml", "config.sg.yaml"):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,creative{id}", "limit": "500"})
    for a in ads:
        if "你也可以有将多" not in cpa.creative_key(a.get("name")):
            continue
        cid = a["creative"]["id"]
        try:
            c = g.get_object(cid, "name,object_type,video_id,body,title,thumbnail_url,image_url,object_story_id,effective_object_story_id,call_to_action_type,link_url")
        except Exception as exc:                                             # noqa: BLE001
            print(f"{cfg} {cid} err {str(exc)[:120]}"); continue
        print(f"\n{cfg} «{a['name']}» creative {cid}: type {c.get('object_type')} · video {c.get('video_id')} · title {c.get('title')} · link {c.get('link_url')}")
        print("  body:\n" + "\n".join("  | " + l for l in (c.get("body") or "").split("\n")))
        sid = c.get("effective_object_story_id")
        try:
            p = g.get_object(sid, "message,attachments{media_type,target,url}")
            print(f"  post attachments: {p.get('attachments')}")
        except Exception as exc:                                             # noqa: BLE001
            print(f"  post read err: {str(exc)[:100]}")
        break
print("JIANGDUO DONE")
