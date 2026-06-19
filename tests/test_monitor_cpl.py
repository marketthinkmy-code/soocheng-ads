import math

from adbot.monitor_cpl import (INSUFFICIENT_SPEND, NO_RESULTS_YET, OVER_THRESHOLD,
                               WITHIN_THRESHOLD, ZERO_RESULTS, decide, event_token,
                               extract_results, parse_metrics)
from adbot.settings import KpiCfg

KPI = KpiCfg(cpl_threshold_myr=40, cpl_min_spend_myr=80, pause_zero_lead_after_spend=True)


def test_insufficient_spend_is_skipped():
    should, reason, cpl = decide(50, 0, KPI)
    assert not should and reason == INSUFFICIENT_SPEND and cpl is None


def test_zero_results_after_min_spend_pauses():
    should, reason, cpl = decide(100, 0, KPI)
    assert should and reason == ZERO_RESULTS and cpl == math.inf


def test_zero_results_kept_when_disabled():
    kpi = KpiCfg(cpl_threshold_myr=40, cpl_min_spend_myr=80, pause_zero_lead_after_spend=False)
    should, reason, _ = decide(100, 0, kpi)
    assert not should and reason == NO_RESULTS_YET


def test_cpl_over_threshold_pauses():
    should, reason, cpl = decide(100, 1, KPI)
    assert should and reason == OVER_THRESHOLD and round(cpl) == 100


def test_cpl_within_threshold_keeps():
    should, reason, cpl = decide(100, 4, KPI)
    assert not should and reason == WITHIN_THRESHOLD and cpl == 25


def test_event_token_maps_complete_registration():
    assert event_token("COMPLETE_REGISTRATION") == "complete_registration"
    assert event_token("LEAD") == "lead"


def test_extract_results_matches_configured_event():
    actions = [
        {"action_type": "offsite_conversion.fb_pixel_complete_registration", "value": "3"},
        {"action_type": "lead", "value": "99"},
        {"action_type": "complete_registration", "value": "2"},
    ]
    assert extract_results(actions, "complete_registration") == 5


def test_parse_metrics_reads_spend_and_results():
    insight = {"spend": "120.50",
               "actions": [{"action_type": "complete_registration", "value": "2"}]}
    spend, results = parse_metrics(insight, "complete_registration")
    assert spend == 120.5 and results == 2


def test_parse_metrics_handles_empty():
    assert parse_metrics(None, "complete_registration") == (0.0, 0.0)
