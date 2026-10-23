# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-23: source assets for MY WINNERS +3 — every ad (MY 3.0 / SG / MY 5.0) whose creative_key
matches 我跟你讲 / 用我的方法，你也可以有将多 / 赚美金 = 求人: status, review feedback, video_id, headline, full caption."""
from __future__ import annotations

import json

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

WANT = ["我跟你讲", "你也可以有将多", "赚美金 = 求人"]
seen = set()
for cfg in ("config.yaml", "config.sg.yaml", "config.my5.yaml"):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,ad_review_feedback,created_time,creative{object_story_spec,asset_feed_spec,effective_object_story_id}", "limit": "500"})
    print(f"\n######## {cfg}")
    for a in ads:
        k = cpa.creative_key(a.get("name"))
        if not any(w in k for w in WANT):
            continue
        cr = a.get("creative") or {}
        vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
        fb = a.get("ad_review_feedback")
        print(f"\n▶ «{a['name']}» {a['effective_status']} {a['created_time'][:10]} · video {vd.get('video_id')} · story {cr.get('effective_object_story_id')}"
              + (f"\n   ⚠️ REVIEW {json.dumps(fb, ensure_ascii=False)[:300]}" if fb else ""))
        key = (vd.get("video_id"), vd.get("message"))
        if vd and key not in seen:
            seen.add(key)
            print(f"   headline: {vd.get('title')}\n   caption:\n" + "\n".join("   | " + l for l in (vd.get("message") or "").split("\n")))
        elif not vd:
            print(f"   (no video_data; asset_feed_spec keys {list((cr.get('asset_feed_spec') or {}).keys())})")
print("\nSOURCES DONE (read-only)")
