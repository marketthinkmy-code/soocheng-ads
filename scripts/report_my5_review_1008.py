# -*- coding: utf-8 -*-
"""READ-ONLY: review status of everything on the new MY account «[MY] MTC X SB 5.0»
(act_2285351942292267). For each ad: status chain, effective_status, ad_review_feedback,
issues_info. Summarises approved / pending / rejected. A rejected ad here is a strike on
the whole BM family — the rule (CLAUDE.md ⛔) is DELETE, never resubmit. No PII."""
from __future__ import annotations

import collections
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    info = g._request("GET", acct, params={"fields": "name,account_status,disable_reason,amount_spent"})
    print(f"账户 «{info.get('name')}» status={info.get('account_status')} reason={info.get('disable_reason')}"
          f" 累计花费 RM{float(info.get('amount_spent') or 0)/100:,.0f}\n")
    time.sleep(0.8)
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,ad_review_feedback,issues_info,"
                  "campaign{name,status,daily_budget},adset{name,status}", "limit": "100"})
    buckets = collections.Counter()
    by_camp = collections.defaultdict(list)
    for a in ads:
        by_camp[(a.get("campaign") or {}).get("name") or "?"].append(a)
    for camp, rows in by_camp.items():
        c = rows[0].get("campaign") or {}
        print(f"[{c.get('status')}] «{camp}» CBO RM{float(c.get('daily_budget') or 0)/100:.0f}")
        for a in rows:
            eff = a.get("effective_status")
            fb = a.get("ad_review_feedback") or {}
            iss = a.get("issues_info") or []
            rejected = eff in ("DISAPPROVED", "WITH_ISSUES") or bool(fb) or bool(iss)
            pending = eff in ("PENDING_REVIEW", "IN_PROCESS")
            tag = "❌ 被拒/有问题" if rejected else ("⏳ 审核中" if pending else "✅")
            buckets["rejected" if rejected else ("pending" if pending else "ok")] += 1
            print(f"    {tag} [{a.get('status')}/{eff}] «{(a.get('name') or '')[:34]}» id={a['id']}"
                  f"  adset={(a.get('adset') or {}).get('status')}")
            for k, v in (fb.get("global") or {}).items() if isinstance(fb, dict) else []:
                print(f"         review: {k}: {str(v)[:140]}")
            for i in iss:
                print(f"         issue: {i.get('error_summary','')[:60]} / {i.get('error_message','')[:120]}")
        print()
    print(f"合计 {len(ads)} 支：✅ {buckets['ok']} · ⏳ {buckets['pending']} · ❌ {buckets['rejected']}")
    if buckets["rejected"]:
        print("⛔ 有被拒的：按规则 DELETE（不申诉、不 resubmit），并把母带加进禁跑名单 + 🚫。")
    print("MY5 REVIEW DONE (read-only)")


if __name__ == "__main__":
    main()
