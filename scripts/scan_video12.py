# -*- coding: utf-8 -*-
"""READ-ONLY: every ad instance of video 12（炒过那么多）across MY+SG with its
review state and Meta's stated rejection reason (issues_info), plus which
creative/post each instance uses — so we know which posts are approved-and-safe
to reuse and which instances are burning policy strikes."""
from __future__ import annotations

import collections
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NEEDLE = "炒过那么多"


def main() -> None:
    posts = collections.defaultdict(list)
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,effective_status,created_time,"
                       "campaign{name},creative{effective_object_story_id,video_id},"
                       "issues_info", "limit": "500"})
        hits = [a for a in ads if NEEDLE in (a.get("name") or "")]
        hits.sort(key=lambda a: a.get("created_time") or "")
        for a in hits:
            camp = ((a.get("campaign") or {}).get("name") or "")[:42]
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or "?"
            vid = cr.get("video_id") or "-"
            est = a.get("effective_status")
            created = (a.get("created_time") or "")[:10]
            print(f"  [{est:>12}] {created}  post={post}  vid={vid}")
            print(f"      «{camp}»  (own status {a.get('status')})")
            for iss in (a.get("issues_info") or []):
                print(f"      ⛔ {iss.get('level')} {iss.get('error_code')}: "
                      f"{(iss.get('error_summary') or '')[:70]}")
                msg = (iss.get('error_message') or '')[:300]
                if msg:
                    print(f"         {msg}")
            posts[(post, vid)].append((label, est, camp))
        print()
        time.sleep(1)

    print("═══ 按 post/video 汇总 ═══")
    for (post, vid), uses in posts.items():
        ok = sum(1 for _, e, _ in uses if e == "ACTIVE")
        bad = sum(1 for _, e, _ in uses if e in ("DISAPPROVED", "WITH_ISSUES"))
        print(f"  post={post} vid={vid}: {len(uses)} 支 · ACTIVE {ok} · 被拒/问题 {bad}")
        for lab, e, camp in uses:
            print(f"     [{lab}] {e:>12}  «{camp}»")
    print("\nSCAN DONE (read-only)")


if __name__ == "__main__":
    main()
