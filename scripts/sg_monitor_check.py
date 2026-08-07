"""Validate the SG CPL monitor: load config/config.sg.yaml and run the monitor in
DRY-RUN against the live Singapore account (act_893025326577600). Read-only — dry_run
forces evaluate+log only, never pauses. Confirms the SG account reads cleanly and the
CPL decision logic sees the right ads before the hourly workflow goes live on main.
"""
from __future__ import annotations

import os

from adbot import monitor_cpl
from adbot.commands import graph_client
from adbot.settings import load_settings


def main() -> None:
    cfg = os.path.join(os.environ.get("ADBOT_ROOT", "."), "config", "config.sg.yaml")
    settings = load_settings(cfg)
    print(f"SG MONITOR (dry-run)  target={settings.meta.account_path}  "
          f"event={settings.meta.conversion_event}  CPL<=RM{settings.kpi.cpl_threshold_myr:.0f}  "
          f"min_spend=RM{settings.kpi.cpl_min_spend_myr:.0f}  cpa={settings.cpa.enabled}\n")
    g = graph_client(settings)
    monitor_cpl.run(g, settings, dry_run=True)


if __name__ == "__main__":
    main()
