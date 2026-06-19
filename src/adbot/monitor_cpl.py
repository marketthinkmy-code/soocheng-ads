"""CPL guardrail: decide which ads to pause, and run the pause against Meta.

"CPL" here means cost per the campaign's optimized conversion event (e.g. Complete
Registration), not a hardcoded "lead". The decision logic is a pure function (unit-tested);
the runner reads insights via the Graph client, only ever acts on ACTIVE ads, and never
un-pauses — re-activation is always a human (or weekly_on) decision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from . import state
from .logging import final_summary, get_logger
from .settings import KpiCfg, Settings

INSUFFICIENT_SPEND = "insufficient_spend"
ZERO_RESULTS = "zero_results_over_min_spend"
OVER_THRESHOLD = "cpl_over_threshold"
WITHIN_THRESHOLD = "within_threshold"
NO_RESULTS_YET = "no_results_yet"

# Map a Meta custom_event_type to the substring that identifies it in an insight action_type.
EVENT_ACTION_HINTS = {
    "COMPLETE_REGISTRATION": "complete_registration",
    "LEAD": "lead",
    "PURCHASE": "purchase",
    "SCHEDULE": "schedule",
    "SUBSCRIBE": "subscribe",
    "SUBMIT_APPLICATION": "submit_application",
    "START_TRIAL": "start_trial",
    "CONTACT": "contact",
}


def event_token(conversion_event: str) -> str:
    """Substring used to find the optimized event inside an insight `action_type`."""
    ce = (conversion_event or "").upper()
    return EVENT_ACTION_HINTS.get(ce, ce.lower())


def extract_results(actions: Optional[List[Dict[str, Any]]], token: str) -> float:
    """Sum action values whose action_type contains the optimized-event token."""
    total = 0.0
    for action in actions or []:
        if token and token in (action.get("action_type", "")).lower():
            try:
                total += float(action.get("value", 0))
            except (TypeError, ValueError):
                continue
    return total


def parse_metrics(insight: Optional[Dict[str, Any]], token: str) -> Tuple[float, float]:
    """Return (spend, results) from a raw insight row for the optimized event."""
    if not insight:
        return 0.0, 0.0
    try:
        spend = float(insight.get("spend", 0) or 0)
    except (TypeError, ValueError):
        spend = 0.0
    return spend, extract_results(insight.get("actions"), token)


def decide(spend: float, results: float, kpi: KpiCfg) -> Tuple[bool, str, Optional[float]]:
    """(should_pause, reason, cpl). cpl is None when undefined, inf when results==0."""
    if spend < kpi.cpl_min_spend_myr:
        return False, INSUFFICIENT_SPEND, None
    if results <= 0:
        if kpi.pause_zero_lead_after_spend:
            return True, ZERO_RESULTS, math.inf
        return False, NO_RESULTS_YET, math.inf
    cpl = spend / results
    if cpl > kpi.cpl_threshold_myr:
        return True, OVER_THRESHOLD, cpl
    return False, WITHIN_THRESHOLD, cpl


@dataclass
class AdDecision:
    ad_id: str
    name: str
    spend: float
    results: float
    cpl: Optional[float]
    should_pause: bool
    reason: str


def evaluate_account(graph, settings: Settings) -> List[AdDecision]:
    """Read every active managed ad's cost-per-result and compute pause decisions (no writes)."""
    account = settings.meta.account_path
    token = event_token(settings.meta.conversion_event)
    decisions: List[AdDecision] = []
    for campaign in graph.find_campaigns_by_prefix(account, settings.naming.prefix):
        for ad in graph.list_ads_under_campaign(campaign["id"]):
            if ad.get("effective_status") != "ACTIVE":
                continue
            insight = graph.get_ad_insight(ad["id"], settings.kpi.cpl_lookback)
            spend, results = parse_metrics(insight, token)
            should_pause, reason, cpl = decide(spend, results, settings.kpi)
            decisions.append(AdDecision(ad["id"], ad.get("name", ad["id"]),
                                        spend, results, cpl, should_pause, reason))
    return decisions


def run(graph, settings: Settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    event = settings.meta.conversion_event
    decisions = evaluate_account(graph, settings)
    to_pause = [d for d in decisions if d.should_pause]

    for d in decisions:
        cpl_str = "∞" if d.cpl == math.inf else (f"{d.cpl:.2f}" if d.cpl is not None else "n/a")
        verb = "WOULD PAUSE" if (d.should_pause and dry_run) else ("PAUSE" if d.should_pause else "keep")
        log.info("  [%s] %s  spend=%.2f %s=%.0f CPL=%s (%s)",
                 verb, d.name, d.spend, event.lower(), d.results, cpl_str, d.reason)

    paused = 0
    if not dry_run:
        for d in to_pause:
            graph.update_status(d.ad_id, "PAUSED")
            state.append_pause_log(d.ad_id, "ad", d.reason,
                                   {"spend": d.spend, "results": d.results,
                                    "cpl": None if d.cpl is None or d.cpl == math.inf else round(d.cpl, 2)})
            paused += 1

    active_left = len([d for d in decisions if not d.should_pause])
    summary = (f"CPL monitor ({event}): evaluated {len(decisions)} active ads, "
               f"{'would pause' if dry_run else 'paused'} {len(to_pause) if dry_run else paused}, "
               f"{active_left} remain under CPL {settings.kpi.cpl_threshold_myr:.0f} MYR")
    final_summary(log, summary)
    return {"evaluated": len(decisions), "paused": (len(to_pause) if dry_run else paused),
            "remaining": active_left, "dry_run": dry_run}
