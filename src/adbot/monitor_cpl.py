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
MANUAL_HOLD = "manual_hold"  # owner asked to keep this ad running despite CPL

def result_action_type(conversion_event: str) -> str:
    """The exact insights action_type that equals Ads Manager "Results" for a pixel-optimized ad.

    Meta reports the SAME conversion under several overlapping buckets (complete_registration,
    omni_complete_registration, offsite_complete_registration_*, offsite_conversion.fb_pixel_*),
    so we must match ONE exactly — substring-summing them multiplies the real count.
    """
    return f"offsite_conversion.fb_pixel_{(conversion_event or '').lower()}"


def extract_results(actions: Optional[List[Dict[str, Any]]], action_type: str) -> float:
    """Sum values for ONLY the exact optimized-event bucket (= Ads Manager 'Results')."""
    total = 0.0
    for action in actions or []:
        if action.get("action_type") == action_type:
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
    """Read every active ad in the account and compute per-ad pause decisions (no writes).

    Whole-account scope (every campaign, MTC + STOCKBLOOM), but judged one ad at a time —
    a single bad creative is paused without touching the rest of its ad set or campaign.
    Only ads whose ad set optimizes for the configured conversion event (e.g. Complete
    Registration) are evaluated, so a campaign chasing a different objective can never be
    paused on a registration-CPL it was never trying to produce.
    """
    account = settings.meta.account_path
    token = result_action_type(settings.meta.conversion_event)
    want_event = (settings.meta.conversion_event or "").upper()
    decisions: List[AdDecision] = []
    for campaign in graph.list_campaigns(account):
        if campaign.get("effective_status") != "ACTIVE":  # paused/archived have no live ads
            continue
        for ad in graph.list_ads_under_campaign(campaign["id"]):
            if ad.get("effective_status") != "ACTIVE":
                continue
            promoted = (ad.get("adset") or {}).get("promoted_object") or {}
            if (promoted.get("custom_event_type") or "").upper() != want_event:
                continue  # not optimized for our event — not ours to judge or pause
            name = ad.get("name", ad["id"])
            insight = graph.get_ad_insight(ad["id"], settings.kpi.cpl_lookback)
            spend, results = parse_metrics(insight, token)
            if any(h and h in name for h in settings.kpi.cpl_hold):
                cpl = (spend / results) if results else (math.inf if spend else None)
                decisions.append(AdDecision(ad["id"], name, spend, results, cpl, False, MANUAL_HOLD))
                continue
            should_pause, reason, cpl = decide(spend, results, settings.kpi)
            decisions.append(AdDecision(ad["id"], name, spend, results, cpl, should_pause, reason))
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
