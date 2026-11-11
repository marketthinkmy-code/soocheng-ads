# -*- coding: utf-8 -*-
"""Guardian (owner 2026-08-24 «上保险»): hourly watchdog over the protected
seller campaigns that keep getting hand-paused (5 times in 4 days as of 8/24)
despite CPL-high-but-CPA-low economics.

For each protected campaign: if its stored status is not ACTIVE, flip the
campaign (and its paused ad sets) back to ACTIVE and log the find-time — the
log doubles as the incident timeline. Two guards:

  · a campaign carrying the ADBOT_WEEKLY_OFF label is skipped (the Wednesday
    weekly-off cycle owns that pause; weekly-on restores it Thursday 00:09)
  · ad-level statuses are never touched, so the CPL monitor's per-ad pauses
    (which understand CPA rescue) stay in force

Edit PROTECTED to add/remove campaigns. Runs headless from adbot-guardian.yml
(hourly cron on main); CONFIRM=true is set by the workflow — without it this
prints what it would do."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 3.0
WEEKLY_LABEL = "ADBOT_WEEKLY_OFF"

PROTECTED = {
    "config.yaml": [
        ("120247921988670575", "MY DAY TRADING (炒过那么多)"),
        ("120247525704130575", "MY 用我的方法 (1-1-1)"),
    ],
    "config.sg.yaml": [
        ("120248220643620521", "SG GOLF PICKBLEBALL (我只有一个目的)"),
        ("120248231846030521", "SG RUNNING (你敢吗)"),
    ],
}


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    revived = 0
    for cfg, items in PROTECTED.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        for cid, label in items:
            try:
                c = g._request("GET", cid, params={"fields": "name,status,adlabels"})
                status = c.get("status")
                labels = {(l.get("name") or "") for l in (c.get("adlabels") or [])}
                if status == "ACTIVE":
                    print(f"  ✓ {label} — ACTIVE")
                    continue
                if WEEKLY_LABEL in labels:
                    print(f"  💤 {label} — paused by weekly-off cycle, leaving it")
                    continue
                print(f"  🚨 {label} found {status} at {now}")
                if not CONFIRM:
                    print("     (dry-run — would revive)")
                    continue
                g.update_status(cid, "ACTIVE")
                time.sleep(PACE)
                for aset in g._get_all(f"{cid}/adsets",
                                       {"fields": "id,status", "limit": "10"}):
                    if aset.get("status") != "ACTIVE":
                        g.update_status(aset["id"], "ACTIVE")
                        time.sleep(PACE)
                revived += 1
                print(f"  ⛑ revived «{c.get('name')}» (campaign + paused ad sets)")
            except Exception as e:
                print(f"  ❌ {label}: {str(e)[:120]} — continuing")
    print(f"GUARDIAN DONE — revived {revived} at {now}"
          if CONFIRM else "GUARDIAN DRY-RUN DONE")


if __name__ == "__main__":
    main()
