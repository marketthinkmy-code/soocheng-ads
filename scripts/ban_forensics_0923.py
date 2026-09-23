# -*- coding: utf-8 -*-
"""READ-ONLY forensics for the 2026-09-23 ban of MTC X SB 3.0 (act_759339046918885).

Owner: 「My ads account banned already, list out all those rejected ads for me」.
Scans BOTH accounts (MY = disabled, SG = still live at time of writing):

  1) account_status + disable_reason  — Meta's official account-level code
  2) EVERY ad ever rejected: effective_status DISAPPROVED / WITH_ISSUES / PENDING_REVIEW
     plus issues_info + ad_review_feedback (the exact policy cited per ad)
  3) account activity: ad_review_declined events (the full rejection timeline)

No writes. Every section degrades to an error line instead of crashing, because a
disabled account can block reads at any endpoint."""
from __future__ import annotations

import datetime as dt
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          8: "PENDING_SETTLEMENT", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE",
          101: "CLOSED"}
DISABLE = {0: "NONE", 1: "ADS_INTEGRITY_POLICY — 广告诚信政策违规",
           2: "ADS_IP_REVIEW", 3: "RISK_PAYMENT", 4: "GRAY_ACCOUNT_SHUT_DOWN",
           5: "AMBIGUOUS_NONEXISTENT_BUSINESS", 8: "UMBRELLA_AD_ACCOUNT",
           9: "BUSINESS_INTEGRITY_RAR", 10: "MISREPRESENTATION"}
BAD = ("DISAPPROVED", "WITH_ISSUES", "PENDING_REVIEW", "ADSET_PAUSED_WITH_ISSUES")


def main() -> None:
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print("=" * 78)
        print(f"[{label}]  {acct}")
        print("=" * 78)

        try:
            info = g.get_object(acct, fields="name,account_status,disable_reason")
            st, dr = info.get("account_status"), info.get("disable_reason")
            print(f"  name={info.get('name')}")
            print(f"  account_status={st} ({STATUS.get(st, '?')})")
            print(f"  disable_reason={dr} ({DISABLE.get(dr, '? code')})")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ account read failed: {type(exc).__name__}: {str(exc)[:160]}")
        print()

        try:
            ads = g._get_all(
                f"{acct}/ads",
                {"fields": "id,name,effective_status,created_time,"
                           "campaign{name},issues_info,"
                           "creative{effective_object_story_id}",
                 "limit": "500"})
            time.sleep(1.2)
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ ads read failed: {type(exc).__name__}: {str(exc)[:160]}\n")
            ads = []

        rejected, seen_names = [], {}
        for a in ads:
            es = a.get("effective_status") or ""
            iss = a.get("issues_info") or []
            if es not in BAD and not iss:
                continue
            rejected.append(a)
            nm = (a.get("name") or "").strip()
            seen_names.setdefault(nm, []).append(a)

        print(f"  ── 被拒 / 有问题的广告：{len(rejected)} 支，{len(seen_names)} 个不同素材 ──")
        for nm, group in sorted(seen_names.items(), key=lambda kv: -len(kv[1])):
            print(f"\n  ⛔ «{nm}»  ×{len(group)} 个位置")
            for a in group:
                camp = (a.get("campaign") or {}).get("name") or "?"
                print(f"       [{a.get('effective_status')}] @ «{camp[:46]}»  "
                      f"建于 {(a.get('created_time') or '')[:10]}  id={a.get('id')}")
            cites = set()
            for a in group:
                for iss in a.get("issues_info") or []:
                    cites.add((iss.get("error_summary") or "").strip()[:90])
                    msg = (iss.get("error_message") or "").strip()
                    if msg:
                        cites.add("· " + msg[:150])
            for c in sorted(cites):
                if c:
                    print(f"       ↳ {c}")
        print()

        try:
            since = int((dt.datetime.utcnow() - dt.timedelta(days=45)).timestamp())
            acts = g._get_all(
                f"{acct}/activities",
                {"fields": "event_time,event_type,actor_name,object_name,extra_data",
                 "since": str(since), "limit": "400"})
            time.sleep(1.2)
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ activities read failed: {type(exc).__name__}: {str(exc)[:160]}\n")
            acts = []

        decl = [x for x in acts if "declined" in (x.get("event_type") or "")
                or "reject" in (x.get("event_type") or "")]
        print(f"  ── 近 45 天 ad_review_declined 事件：{len(decl)} 条 ──")
        for x in decl[:80]:
            print(f"     {(x.get('event_time') or '')[:16]}  «{(x.get('object_name') or '')[:50]}»")
        print()

    print("BAN FORENSICS 0923 DONE (read-only)")


if __name__ == "__main__":
    main()
