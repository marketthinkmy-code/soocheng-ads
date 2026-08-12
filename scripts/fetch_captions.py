# -*- coding: utf-8 -*-
"""READ-ONLY: print the live captions (creative message) of the winning parent ads,
so the owner can reuse the 原版 copy on the new re-cut videos.

Targets: freestyle 1 · 盖电脑 · 你敢吗 (and 我跟你讲 if any live instance exists).
Resolution order per ad: creative.body -> object_story_spec message ->
effective_object_story_id post message.
"""
from __future__ import annotations

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

WANT = ("freestyle 1", "盖电脑", "你敢吗", "我跟你讲")
ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))
FIELDS = ("name,effective_status,creative{body,object_story_spec,"
          "effective_object_story_id,object_story_id}")


def caption_of(g, ad) -> str:
    cr = ad.get("creative") or {}
    oss = cr.get("object_story_spec") or {}
    vd = (oss.get("video_data") or {})
    for cand in (vd.get("message"), (oss.get("link_data") or {}).get("message"), cr.get("body")):
        if cand and len(cand.strip()) > 40:
            return cand
    post = cr.get("effective_object_story_id") or cr.get("object_story_id")
    if post:
        msg = (g._request("GET", post, params={"fields": "message"}) or {}).get("message")
        if msg:
            return msg
    return ""


def main() -> None:
    seen: set = set()
    for label, cfg in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        ads = g._get_all(f"{s.meta.account_path}/ads", {"fields": FIELDS, "limit": "200"})
        for key in WANT:
            if key in seen:
                continue
            hits = [a for a in ads if cpa.norm(key) in cpa.norm(a.get("name") or "")]
            hits.sort(key=lambda a: 0 if a.get("effective_status") == "ACTIVE" else 1)
            for a in hits:
                # skip the NEW HOOK ads we just built (their copy is the rewrite, not 原版)
                if "extra" in cpa.norm(a.get("name") or "") or "60秒" in (a.get("name") or ""):
                    continue
                txt = caption_of(g, a)
                if txt:
                    seen.add(key)
                    print(f"■■■■■ {key}  ←  [{label}] «{a.get('name')}» "
                          f"({a.get('effective_status')}) ■■■■■")
                    print(txt)
                    print("■■■■■ END ■■■■■\n")
                    break
    missing = [k for k in WANT if k not in seen]
    if missing:
        print(f"NOT FOUND live: {missing}")


if __name__ == "__main__":
    main()
