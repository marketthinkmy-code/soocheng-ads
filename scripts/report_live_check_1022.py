# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: owner「都开了 你看看」— every Webinarkit campaign on MY 5.0 + SG: campaign / ad set / ad
status, budgets, review feedback; live daily total per account."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    for cfg in ("config.my5.yaml", "config.sg.yaml"):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        camps = [c for c in g._get_all(s.meta.account_path + "/campaigns", {"fields": "name,status,effective_status,daily_budget", "limit": "100"})
                 if "webinarkit" in c["name"].lower() and c["effective_status"] not in ("DELETED", "ARCHIVED")]
        total = 0
        print(f"\n######## {cfg}")
        for c in camps:
            cb = int(c.get("daily_budget") or 0) // 100
            print(f"\n «{c['name'][13:70]}» {c['effective_status']}" + (f" CBO RM{cb}" if cb else " ABO"))
            if c["effective_status"] == "ACTIVE" and cb:
                total += cb
            for a in g._get_all(c["id"] + "/adsets", {"fields": "name,effective_status,daily_budget", "limit": "20"}):
                ab = int(a.get("daily_budget") or 0) // 100
                if c["effective_status"] == "ACTIVE" and a["effective_status"] == "ACTIVE" and ab:
                    total += ab
                ads = g._get_all(a["id"] + "/ads", {"fields": "name,effective_status,ad_review_feedback", "limit": "20"})
                print(f"   ▸ {a['name'][:34]:<34} {a['effective_status']:<16}" + (f" RM{ab}" if ab else ""))
                for x in ads:
                    fb = x.get("ad_review_feedback")
                    print(f"       {x['name'][:28]:<28} {x['effective_status']}" + (f"  ⚠️ {json.dumps(fb, ensure_ascii=False)[:160]}" if fb else ""))
                time.sleep(0.5)
        print(f"\n  {cfg} 在跑的日预算合计 ≈ RM{total}")
    print("\nLIVE CHECK DONE (read-only)")


if __name__ == "__main__":
    main()
