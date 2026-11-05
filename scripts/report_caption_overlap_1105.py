# -*- coding: utf-8 -*-
"""READ-ONLY: do any LIVE ads (MY 5.0 + SG) carry the same caption as one of the SG ads rejected 11/05?
Compares the first 40 characters of the caption (whitespace stripped). Prints the live caption head for each."""
from __future__ import annotations

import re

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

F = "name,effective_status,campaign{name},adset{name},creative{body,object_story_spec}"
norm = lambda t: re.sub(r"\s+", "", t or "")[:40]


def cap(cr):
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    return vd.get("message") or cr.get("body") or ""


data = {}
for label, cfg in (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    data[label] = graph_client(s)._get_all(s.meta.account_path + "/ads", {"fields": F, "limit": "2000"})
rej = {norm(cap(a.get("creative") or {})): a["name"] for a in data["SG"] if a.get("effective_status") == "DISAPPROVED"}
for label, ads in data.items():
    print(f"\n## {label} 在跑的 ad")
    for a in ads:
        if a.get("effective_status") != "ACTIVE":
            continue
        c = cap(a.get("creative") or {})
        hit = rej.get(norm(c))
        print(f"  {'⚠️ 与被拒同文案 «' + hit + '»' if hit else 'ok'} · {a['campaign']['name'][:42]} › {a['adset']['name'][:20]} · {a['name']} · ad {a['id']}\n      «{c.replace(chr(10), ' ')[:70]}»")
print("\nCAPTION OVERLAP DONE (read-only)")
