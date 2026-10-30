# -*- coding: utf-8 -*-
"""READ-ONLY: where is freestyle: korea's caption? MY 5.0 + SG korea creatives → video_data.message / body /
asset_feed_spec bodies / post id. Prints lengths + first 40 chars only."""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

F = "id,name,body,url_tags,object_story_id,effective_object_story_id,object_story_spec,asset_feed_spec"
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    seen = set()
    for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,campaign{name},creative{" + F + "}", "limit": "2000"}):
        if "korea" not in a["name"].lower():
            continue
        c = a.get("creative") or {}
        if c.get("id") in seen:
            continue
        seen.add(c.get("id"))
        vd = (c.get("object_story_spec") or {}).get("video_data") or {}
        bodies = [b.get("text", "") for b in ((c.get("asset_feed_spec") or {}).get("bodies") or [])]
        msg = vd.get("message") or c.get("body") or (bodies[0] if bodies else "")
        print(f"{label} {a['campaign']['name'][:40]} · ad {a['id']} {a['effective_status']} · creative {c.get('id')} · video {vd.get('video_id')} · "
              f"msg {len(vd.get('message') or '')} · body {len(c.get('body') or '')} · afs {len(bodies)} · post {c.get('effective_object_story_id')} · «{msg[:40]}»")
print("KOREA COPY DONE (read-only)")
