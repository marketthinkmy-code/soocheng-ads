# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-15「为什么我的广告被 restricted，是什么触犯了？」

  Scan BOTH accounts for every ad with a rejection/issue (DISAPPROVED /
  WITH_ISSUES / non-empty issues_info) and print Meta's own reason strings
  (error_summary + error_message), grouped by campaign."""
from __future__ import annotations

import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

BAD = {"DISAPPROVED", "WITH_ISSUES"}


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        rows = g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,issues_info,"
                       "campaign{name,effective_status}",
             "limit": "500"})
        time.sleep(1.2)
        print(f"═══ [{label}] 有问题的广告 ═══")
        n = 0
        for a in rows:
            issues = a.get("issues_info") or []
            if a.get("effective_status") not in BAD and not issues:
                continue
            n += 1
            camp = (a.get("campaign") or {})
            print(f"◆ «{(a.get('name') or '')[:40]}»  [{a.get('effective_status')}]")
            print(f"   @ «{(camp.get('name') or '')[:48]}» (camp {camp.get('effective_status')})")
            if not issues:
                print("   （无 issues_info——被拒原因要在 Ads Manager 的 Account Quality 看）")
            for i in issues[:3]:
                print(f"   · summary: {(i.get('error_summary') or '?')[:100]}")
                print(f"     message: {(i.get('error_message') or '?')[:400]}")
        if not n:
            print("  （没有）")
        print()
    print("REJECTION SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
