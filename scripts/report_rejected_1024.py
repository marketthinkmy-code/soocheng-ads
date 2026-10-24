# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-24: the MY 5.0 «Video：赚美金，一定要接美国客户？» rejection — which ad, review feedback, issues,
creative, and the status of every other 赚美金 copy (MY 5.0 + SG)."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

for cfg in ("config.my5.yaml", "config.sg.yaml"):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,created_time,updated_time,ad_review_feedback,issues_info,creative{id},adset{name},campaign{name}", "limit": "500"})
    print(f"\n## {cfg}")
    for a in ads:
        if "赚美金" not in (a.get("name") or "") or a["effective_status"] in ("DELETED", "ARCHIVED"):
            continue
        print(f"  {a['id']} «{a['name']}» {a['status']}/{a['effective_status']} · cr {a['creative']['id']} · {a['campaign']['name'][13:50]} › {a['adset']['name']} · upd {a['updated_time'][:16]}")
        if a.get("ad_review_feedback") or a.get("issues_info") or a["effective_status"] == "DISAPPROVED":
            print(f"     feedback {json.dumps(a.get('ad_review_feedback'), ensure_ascii=False)} · issues {json.dumps(a.get('issues_info'), ensure_ascii=False)[:400]}")
            try:
                d = g.get_object(a["id"], "recommendations,failed_delivery_checks")
                print(f"     extra {json.dumps(d, ensure_ascii=False)[:400]}")
            except Exception as exc:                                     # noqa: BLE001
                print(f"     extra err {str(exc)[:100]}")
print("REJECTED DONE (read-only)")
