# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「注意，我要的是带去 webinarkit 的 existing post id」). For each candidate post id: the ads/creatives that use it
(account · campaign › ad set · ad id), the creative's call-to-action link (object_story_spec) and url_tags, and the post's own
call_to_action link read from the page post when the token allows. ✅ = link goes to the Webinarkit register page."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

POSTS = {
    "年纪大 · SG": "1001334883061622_122127755757286543", "年纪大 · MY": "1001334883061622_122126499129286543",
    "用我的方法": "1001334883061622_122126501961286543", "V4 决定变少": "1001334883061622_122128786599286543",
    "盖电脑": "1001334883061622_122126499021286543", "korea": "1001334883061622_122126499027286543",
    "V2 炒了五年": "1001334883061622_122128786629286543",
}
WK = "webinarkit-register"
seen = {p: [] for p in POSTS.values()}
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,adset{name},campaign{name},"
                        "creative{id,effective_object_story_id,object_story_spec,url_tags,call_to_action_type}", "limit": "500"}):
        cr = a.get("creative") or {}
        pid = cr.get("effective_object_story_id")
        if pid in seen:
            oss = cr.get("object_story_spec") or {}
            vd = oss.get("video_data") or oss.get("link_data") or {}
            link = ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or vd.get("link") or ""
            seen[pid].append((label, a, cr.get("id"), link, cr.get("url_tags") or ""))
    g_any = g
for name, pid in POSTS.items():
    rows = seen[pid]
    post_link = ""
    try:
        po = g_any.get_object(pid, "call_to_action,permalink_url,created_time")
        post_link = ((po.get("call_to_action") or {}).get("value") or {}).get("link", "")
        extra = f" · post 建于 {po.get('created_time', '')[:10]} · {po.get('permalink_url', '')}"
    except Exception as exc:  # noqa: BLE001
        extra = f" · （读不到 post 本身：{str(exc)[:80]}）"
    links = {r[3] for r in rows if r[3]} | ({post_link} if post_link else set())
    ok = bool(links) and all(WK in l for l in links)
    print(f"\n{'✅' if ok else '❌'} {name} · post {pid}{extra}")
    print(f"   链接: {', '.join(sorted(links)) or '查不到'}")
    for label, a, cid, link, tags in rows:
        print(f"   - {label} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['effective_status']} · creative {cid}")
    tags = {r[4] for r in rows if r[4]}
    print(f"   url_tags: {' | '.join(sorted(tags)) or '—'}")
print("\nPOST LINKS DONE (read-only)")
