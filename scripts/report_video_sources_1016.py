# -*- coding: utf-8 -*-
"""READ-ONLY (+ validate_only) 2026-10-16: find a usable video_id + caption for each clean video so the
Webinarkit creatives can be built without page-read permission. Searches adcreatives in MY 5.0 / SG / MY 3.0
for video_data whose name matches; then asks Meta to VALIDATE (not create) a MY 5.0 creative with that
video_id (execution_options=validate_only). No PII."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

ACCTS = (("MY 5.0", "act_2285351942292267"), ("SG", "act_893025326577600"), ("MY 3.0", "act_759339046918885"))
KEYS = {"盖电脑": ["盖电脑"], "korea": ["korea"], "年纪大": ["年纪大"], "赚美金": ["赚美金", "赚 mj", "赚mj"],
        "用我的方法": ["用我的方法"], "不选 forex": ["不选 forex", "不选forex"], "我跟你讲": ["我跟你讲"]}
LINK = "https://soochenginvesting.com/webinarkit-register-wed"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    found = {}
    for label, acct in ACCTS:
        time.sleep(1.5)
        try:
            ads = g._get_all(acct + "/ads", {"fields": "name,created_time,creative{id,object_story_spec,effective_object_story_id}", "limit": "500"})
        except Exception as e:                                      # noqa: BLE001
            print(f"{label} ❌ {str(e)[:120]}"); continue
        for k, needles in KEYS.items():
            for a in sorted(ads, key=lambda x: x.get("created_time") or "", reverse=True):
                nm = (a.get("name") or "").lower()
                if "🚫" in nm or not any(n.lower() in nm for n in needles):
                    continue
                vd = ((a.get("creative") or {}).get("object_story_spec") or {}).get("video_data") or {}
                if vd.get("video_id") and vd.get("message"):
                    found.setdefault(k, []).append((label, a.get("name"), vd.get("video_id"), vd.get("image_url") or vd.get("image_hash"),
                                                    vd.get("message"), vd.get("title"), (a.get("creative") or {}).get("effective_object_story_id")))
                    break
    for k in KEYS:
        rows = found.get(k) or []
        print(f"\n== {k}: {len(rows)} source(s)")
        for label, name, vid, img, msg, title, post in rows:
            print(f"   {label} «{name}» video {vid} · post {post} · img {'url' if img and str(img).startswith('http') else img} · msg {len(msg)} chars «{msg[:50]}»")
    my5 = "act_2285351942292267"
    print("\n== validate_only on MY 5.0 ==")
    for k, rows in found.items():
        for label, name, vid, img, msg, title, post in rows:
            vd = {"video_id": vid, "message": msg, "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            if img and str(img).startswith("http"):
                vd["image_url"] = img
            elif img:
                vd["image_hash"] = img
            try:
                time.sleep(1.5)
                r = g._request("POST", my5 + "/adcreatives", data={
                    "name": "validate", "object_story_spec": json.dumps({"page_id": "1001334883061622", "video_data": vd}),
                    "execution_options": json.dumps(["validate_only"])})
                print(f"   ✅ {k} ← {label} video {vid}: {str(r)[:80]}")
            except Exception as e:                                  # noqa: BLE001
                print(f"   ❌ {k} ← {label} video {vid}: {str(e)[:160]}")
    print("\nVIDEO SOURCES DONE")


if __name__ == "__main__":
    main()
