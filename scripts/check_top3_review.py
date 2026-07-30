# -*- coding: utf-8 -*-
"""Watch Meta review of the TRAVEL TOP3 ads (both accounts) — especially video 12 炒过那么多,
which re-entered review under an owner override of the 禁跑名单.

Polls every 90s for up to 50 minutes inside the CI job (the runner holds the Meta token).
Early-exits once every found video-12 ad reaches a terminal state. Prints a machine-greppable
VERDICT line per account plus the full ad_review_feedback on any rejection. Read-only.
"""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

ACCTS = [("SG", "act_893025326577600"), ("MY", "act_759339046918885")]
NAME_MATCH = "TRAVEL TOP3"
PENDING = {"IN_PROCESS", "PENDING_REVIEW"}
REJECTED = {"DISAPPROVED", "WITH_ISSUES"}
POLL_SECONDS = 90
MAX_MINUTES = 50
MIN_WAIT_FOR_MY_MIN = 8   # give the MY twin time to be built before concluding without it


def snapshot(g):
    """[(acct_label, ad_name, status, feedback)] for every ad under *TRAVEL TOP3* campaigns."""
    out = []
    for label, acct in ACCTS:
        camps = [c for c in g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
                 if NAME_MATCH in (c.get("name") or "")]
        for c in camps:
            for a in g._get_all(f"{c['id']}/ads",
                                {"fields": "id,name,effective_status,ad_review_feedback",
                                 "limit": "50"}):
                out.append((label, a.get("name") or "", a.get("effective_status") or "",
                            a.get("ad_review_feedback")))
    return out


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    start = time.time()
    last_line = ""
    while True:
        elapsed_min = (time.time() - start) / 60
        rows = snapshot(g)
        v12 = [(l, n, st, fb) for l, n, st, fb in rows if "炒过那么多" in n]
        line = " | ".join(f"{l}·{n[:10]}…={st}" for l, n, st, fb in rows) or "(no TOP3 ads found)"
        if line != last_line:
            print(f"[{dt.datetime.utcnow():%H:%M:%S}Z +{elapsed_min:4.1f}m] {line}", flush=True)
            last_line = line

        v12_terminal = v12 and all(st not in PENDING for _, _, st, _ in v12)
        both_accounts_seen = {l for l, _, _, _ in v12} >= {"SG", "MY"}
        if v12_terminal and (both_accounts_seen or elapsed_min >= MIN_WAIT_FOR_MY_MIN):
            break
        if elapsed_min >= MAX_MINUTES:
            print(f"\nTIMEOUT after {MAX_MINUTES}m — review still pending; re-dispatch for another round.")
            break
        time.sleep(POLL_SECONDS)

    print("\n== FINAL ==")
    for l, n, st, fb in snapshot(g):
        mark = "⛔REJECTED" if st in REJECTED else ("⏳pending" if st in PENDING else "✅ok")
        print(f"  [{l}] {n[:40]:40} {st:16} {mark}")
        if "炒过那么多" in n:
            print(f"VERDICT {l}: " + ("REJECTED" if st in REJECTED else
                                      "PENDING" if st in PENDING else "APPROVED") + f" ({st})")
            if fb:
                print(f"  review_feedback: {json.dumps(fb, ensure_ascii=False)[:800]}")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
