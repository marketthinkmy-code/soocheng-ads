"""adbot CLI — ``python -m adbot <command> [--dry-run]``."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .logging import get_logger
from .settings import load_settings

COMMANDS = ["doctor", "sync", "build", "monitor", "weekly_off", "weekly_on", "intel",
            "resync_targeting", "notion_seed"]
DRY_RUN_DEFAULT_SAFE = {"sync", "build", "monitor", "weekly_off", "weekly_on", "intel",
                        "resync_targeting", "notion_seed"}


def _dispatch(command: str):
    from .commands import (build, doctor, intel, monitor, notion_seed, resync_targeting,
                           sync, weekly_off, weekly_on)
    return {
        "doctor": doctor.run, "sync": sync.run, "build": build.run, "monitor": monitor.run,
        "weekly_off": weekly_off.run, "weekly_on": weekly_on.run, "intel": intel.run,
        "resync_targeting": resync_targeting.run, "notion_seed": notion_seed.run,
    }[command]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="adbot", description=__doc__)
    parser.add_argument("--config", help="path to config.yaml (defaults to repo config/config.yaml)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        if name in DRY_RUN_DEFAULT_SAFE:
            p.add_argument("--dry-run", action="store_true",
                           help="show what would happen without writing to Meta/Docs")
        if name == "build":
            p.add_argument("--manifest",
                           help="path to a creatives manifest JSON (curated file_ids + clean "
                                "content_ids); bypasses the Drive folder scan")
            p.add_argument("--state-key", default="entities",
                           help="state/entities key (use a distinct key, e.g. entities_images, so a "
                                "second campaign creates fresh entities instead of reusing the first)")
            p.add_argument("--label", default="1-1-10",
                           help="campaign label / name suffix (e.g. 'Single-Image')")
            p.add_argument("--start-time",
                           help="ad-set scheduled start, ISO8601 with tz offset "
                                "(e.g. 2026-06-25T00:00:00+08:00)")
            p.add_argument("--daily-budget", type=float, dest="daily_budget",
                           help="override the CBO daily budget in MYR for this build")
    args = parser.parse_args(argv)

    settings = load_settings(args.config)
    log = get_logger()
    log.info("adbot %s  (config: %s)", args.command, settings.config_path)

    dry_run = getattr(args, "dry_run", False)
    kwargs = {}
    if args.command == "build":
        kwargs = dict(manifest=args.manifest, state_key=args.state_key, label=args.label,
                      start_time=args.start_time, daily_budget_myr=args.daily_budget)
    try:
        result = _dispatch(args.command)(settings, dry_run=dry_run, **kwargs)
    except Exception as exc:  # noqa: BLE001 - surface a clean error in the mobile log
        log.error("ERROR: %s", exc)
        return 1

    # doctor returns an exit code; the rest return a dict and succeed if no exception.
    return result if (args.command == "doctor" and isinstance(result, int)) else 0


if __name__ == "__main__":
    sys.exit(main())
