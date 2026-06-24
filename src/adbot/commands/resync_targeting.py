"""resync-targeting: push the configured ad-set targeting to the already-built ad set.

The 1-1-10 build only sets targeting when it first *creates* the ad set; re-running build
reuses the existing ad set untouched (so it never disturbs a learning ad set). This command
is the deliberate exception: it rewrites the live ad set's targeting to exactly what config
says — Broad MY + Chinese + ``advantage_audience`` + any ``excluded_custom_audiences`` —
so an exclusion (or Advantage+) added after the build lands without a full rebuild.

Safe to run on the current PAUSED, zero-spend ad set: there is no learning phase to reset.
"""

from __future__ import annotations

from typing import Any, Dict

from . import graph_client
from .. import state
from ..build_1_1_10 import resolve_excluded_audiences
from ..logging import final_summary, get_logger


def run(settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    graph = graph_client(settings)
    account = settings.meta.account_path
    targeting_cfg = settings.meta.targeting

    adset_id = state.load("entities").get("adset_id")
    if not adset_id:
        raise SystemExit("no adset_id in state/entities.json — run build first")

    names = targeting_cfg.excluded_custom_audiences
    excluded_ids = resolve_excluded_audiences(graph, account, names, log) if names else []
    spec = targeting_cfg.to_spec(excluded_ids)

    if dry_run:
        log.info("[dry-run] would set ad set %s targeting to: %s", adset_id, spec)
        final_summary(log, f"resync-targeting (dry-run): ad set {adset_id} unchanged "
                           f"(advantage_audience={targeting_cfg.advantage_audience}, "
                           f"{len(excluded_ids)} exclusion(s) resolved)")
        return {"dry_run": True, "adset_id": adset_id, "targeting": spec}

    graph.update_targeting(adset_id, spec)
    final_summary(log, f"resync-targeting: ad set {adset_id} targeting updated "
                       f"(advantage_audience={targeting_cfg.advantage_audience}, "
                       f"{len(excluded_ids)} audience exclusion(s))")
    return {"adset_id": adset_id, "targeting": spec, "excluded_ids": excluded_ids}
