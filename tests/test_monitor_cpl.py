import math

from adbot.monitor_cpl import (INSUFFICIENT_SPEND, NO_LEADS_YET, OVER_THRESHOLD,
                               WITHIN_THRESHOLD, ZERO_LEADS, decide,
                               extract_leads, parse_metrics)
from adbot.settings import KpiCfg

KPI = KpiCfg(cpl_threshold_myr=40, cpl_min_spend_myr=80, pause_zero_lead_after_spend=True)


def test_insufficient_spend_is_skipped():
    should, reason, cpl = decide(spend=50, leads=0, kpi=KPI)
    assert not should and reason == INSUFFICIENT_SPEND and cpl is None


def test_zero_leads_after_min_spend_pauses():
    should, reason, cpl = decide(spend=100, leads=0, kpi=KPI)
    assert should and reason == ZERO_LEADS and cpl == math.inf


def test_zero_leads_kept_when_disabled():
    kpi = KpiCfg(cpl_threshold_myr=40, cpl_min_spend_myr=80, pause_zero_lead_after_spend=False)
    should, reason, _ = decide(spend=100, leads=0, kpi=kpi)
    assert not should and reason == NO_LEADS_YET


def test_cpl_over_threshold_pauses():
    should, reason, cpl = decide(spend=100, leads=1, kpi=KPI)
    assert should and reason == OVER_THRESHOLD and round(cpl) == 100


def test_cpl_within_threshold_keeps():
    should, reason, cpl = decide(spend=100, leads=4, kpi=KPI)
    assert not should and reason == WITHIN_THRESHOLD and cpl == 25


def test_extract_leads_sums_lead_actions_only():
    actions = [
        {"action_type": "offsite_conversion.fb_pixel_lead", "value": "3"},
        {"action_type": "link_click", "value": "99"},
        {"action_type": "lead", "value": "2"},
    ]
    assert extract_leads(actions) == 5


def test_parse_metrics_reads_spend_and_leads():
    insight = {"spend": "120.50", "actions": [{"action_type": "lead", "value": "2"}]}
    spend, leads = parse_metrics(insight)
    assert spend == 120.5 and leads == 2


def test_parse_metrics_handles_empty():
    assert parse_metrics(None) == (0.0, 0.0)
