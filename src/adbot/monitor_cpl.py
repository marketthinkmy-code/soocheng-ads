"""CPL guardrail: decide which ads to pause, and run the pause against Meta.

The decision logic is a pure function (unit-tested). The runner reads insights via the
Graph client and pauses ads over threshold. It is idempotent (only ever acts on
currently-ACTIVE ads) and never un-pauses — re-activation is always a human decision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from . import state
from .logging import final_summary, get_logger
from .settings import KpiCfg, Settings

INSUFFICIENT_SPEND = "insufficient_spend"
ZERO_LEADS = "zero_leads_over_min_spend"
OVER_THRESHOLD = "cpl_over_threshold"
WITHIN_THRESHOLD = "within_threshold"
NO_LEADS_YET = "no_leads_yet"


def extract_leads(actions: Optional[List[Dict[str, Any]]]) -> float:
    """Sum action values whose action_type looks like a lead (pixel or on-Meta)."""
    total = 0.0
    for action in actions or []:
        if "lead" in (action.get("action_type", "")).lower():
            try:
                total += float(action.get("value", 0))
            except (TypeError, ValueError):
                continue
    return total


def parse_metrics(insight: Optional[Dict[str, Any]]) -> Tuple[float, float]:
    """Return (spend, leads) from a raw insight row."""
    if not insight:
        return 0.0, 0.0
    try:
        spend = float(insight.get("spend", 0) or 0)
    except (TypeError, ValueError):
        spend = 0.0
    return spend, extract_leads(insight.get("actions"))


def decide(spend: float, leads: float, kpi: KpiCfg) -> Tuple[bool, str, Optional[float]]:
    """(should_pause, reason, cpl). cpl is None when undefined, inf when leads==0."""
    if spend < kpi.cpl_min_spend_myr:
        return False, INSUFFICIENT_SPEND, None
    if leads <= 0:
        if kpi.pause_zero_lead_after_spend:
            return True, ZERO_LEADS, math.inf
        return False, NO_LEADS_YET, math.inf
    cpl = spend / leads
    if cpl > kpi.cpl_threshold_myr:
        return True, OVER_THRESHOLD, cpl
    return False, WITHIN_THRESHOLD, cpl


@dataclass
class AdDecision:
    ad_id: str
    name: str
    spend: float
    leads: float
    cpl: Optional[float]
    should_pause: bool
    reason: str


def evaluate_account(graph, settings: Settings) -> List[AdDecision]:
    """Read every active managed ad's CPL and compute pause decisions (no writes)."""
    account = settings.meta.account_path
    decisions: List[AdDecision] = []
    for campaign in graph.find_campaigns_by_prefix(account, settings.naming.prefix):
        for ad in graph.list_ads_under_campaign(campaign["id"]):
            if ad.get("effective_status") != "ACTIVE":
                continue
            insight = graph.get_ad_insight(ad["id"], settings.kpi.cpl_lookback)
            spend, leads = parse_metrics(insight)
            should_pause, reason, cpl = decide(spend, leads, settings.kpi)
            decisions.append(AdDecision(ad["id"], ad.get("name", ad["id"]),
                                        spend, leads, cpl, should_pause, reason))
    return decisions


def run(graph, settings: Settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    decisions = evaluate_account(graph, settings)
    to_pause = [d for d in decisions if d.should_pause]

    for d in decisions:
        cpl_str = "∞" if d.cpl == math.inf else (f"{d.cpl:.2f}" if d.cpl is not None else "n/a")
        verb = "WOULD PAUSE" if (d.should_pause and dry_run) else ("PAUSE" if d.should_pause else "keep")
        log.info("  [%s] %s  spend=%.2f leads=%.0f CPL=%s (%s)",
                 verb, d.name, d.spend, d.leads, cpl_str, d.reason)

    paused = 0
    if not dry_run:
        for d in to_pause:
            graph.update_status(d.ad_id, "PAUSED")
            state.append_pause_log(d.ad_id, "ad", d.reason,
                                   {"spend": d.spend, "leads": d.leads, "cpl": None if d.cpl is None or d.cpl == math.inf else round(d.cpl, 2)})
            paused += 1

    active_left = len([d for d in decisions if not d.should_pause])
    summary = (f"CPL monitor: evaluated {len(decisions)} active ads, "
               f"{'would pause' if dry_run else 'paused'} {len(to_pause) if dry_run else paused}, "
               f"{active_left} remain under CPL {settings.kpi.cpl_threshold_myr:.0f} MYR")
    final_summary(log, summary)
    return {"evaluated": len(decisions), "paused": (len(to_pause) if dry_run else paused),
            "remaining": active_left, "dry_run": dry_run}
