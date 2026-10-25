# -*- coding: utf-8 -*-
"""READ-ONLY: every ad on MY 5.0 + SG whose effective_status is DISAPPROVED / WITH_ISSUES / PENDING_REVIEW right now,
with campaign › ad set and review feedback."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

BAD = {"DISAPPROVED", "WITH_ISSUES", "PENDING_REVIEW", "IN_PROCESS"}
for cfg in ("config.my5.yaml", "config.sg.yaml"):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,updated_time,ad_review_feedback,campaign{name},adset{name}", "limit": "500"})
    hits = [a for a in ads if a.get("effective_status") in BAD]
    print(f"\n## {cfg}: {len(hits)} ads in {sorted(BAD)}")
    for a in hits:
        print(f"  {a['effective_status']:<14} {a['updated_time'][:16]} «{a['name']}» · {a['campaign']['name'][:50]} › {a['adset']['name']}"
              + (f"\n     feedback {json.dumps(a.get('ad_review_feedback'), ensure_ascii=False)[:300]}" if a.get("ad_review_feedback") else ""))
print("\nDISAPPROVED SCAN DONE (read-only)")
