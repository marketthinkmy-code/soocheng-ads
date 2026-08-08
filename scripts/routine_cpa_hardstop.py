"""CPA hard-stop pause for ONE named campaign the daily routine flagged (2026-08-08).

Owner's standing routine rule: pause a campaign only when ALL of
  60d CPA > RM1,200  ·  60d spend >= RM1,000  ·  created >= 14 days ago  ·  still ACTIVE
and the hourly CPL/CPA monitor did not already pause it.

Tonight that is exactly one campaign — MY «STOCKBLOOM | LUXURY GOODS | 1-1-3»
(60d CPA RM1,220 on RM3,660 / 3 sales, created 2026-07-15, ACTIVE).

Safety: resolves the target by EXACT name on ONE account and aborts unless exactly one
campaign matches; re-checks ACTIVE + age before writing. Dry-run unless CONFIRM_PAUSE=true.
"""
from __future__ import annotations

import datetime as dt
import os

from adbot import state
from adbot.commands import graph_client
from adbot.settings import load_settings

ACCOUNT = "act_759339046918885"                     # MY
TARGET_NAME = "STOCKBLOOM | LUXURY GOODS | 1-1-3"
MIN_AGE_DAYS = 14
REASON = "cpa_hard_stop_60d"
METRICS = {"cpa_60d": 1220, "spend_60d": 3660, "sales_60d": 3, "hard_stop": 1200}


def main() -> None:
    confirm = os.environ.get("CONFIRM_PAUSE", "").lower() == "true"
    g = graph_client(load_settings())
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()

    campaigns = g._get_all(f"{ACCOUNT}/campaigns",
                           {"fields": "id,name,effective_status,created_time", "limit": "300"})
    matches = [c for c in campaigns if c.get("name") == TARGET_NAME]
    if len(matches) != 1:
        print(f"ABORT: expected exactly 1 campaign named «{TARGET_NAME}» on {ACCOUNT}, "
              f"found {len(matches)}: {[(c['id'], c.get('name')) for c in matches]}")
        return

    c = matches[0]
    cid, status = c["id"], c.get("effective_status")
    created = dt.date.fromisoformat((c.get("created_time") or "")[:10])
    age = (today - created).days
    print(f"TARGET  «{c['name']}»  id={cid}  status={status}  created={created} ({age}d)")

    if status != "ACTIVE":
        print(f"SKIP: already {status} — the monitor or the owner has it off; nothing to do.")
        return
    if age < MIN_AGE_DAYS:
        print(f"SKIP: only {age}d old (< {MIN_AGE_DAYS}d) — too young to judge on CPA.")
        return
    if not confirm:
        print("DRY-RUN (CONFIRM_PAUSE != true) — would set PAUSED. No write made.")
        return

    g.update_status(cid, "PAUSED")
    after = g.get_object(cid, "effective_status").get("effective_status")
    state.append_pause_log(cid, "campaign", REASON, METRICS)
    print(f"PAUSED  «{c['name']}»  {status} -> {after}  (id={cid}, reason={REASON}, {METRICS})")


if __name__ == "__main__":
    main()
