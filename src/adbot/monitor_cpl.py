"""CPL guardrail: decide which ads to pause, and run the pause against Meta.

"CPL" here means cost per the campaign's optimized conversion event (e.g. Complete
Registration), not a hardcoded "lead". The decision logic is a pure function (unit-tested);
the runner reads insights via the Graph client, only ever acts on ACTIVE ads, and never
un-pauses — re-activation is always a human (or weekly_on) decision.

TEMPORARY (kpi.cpl_soft_reduce, owner 2026-09-10「先降 30%，再犯才关」): an over-CPL ad's
FIRST breach of a Thu-week cuts its budget carrier 30% instead of pausing the ad; a breach on
a later day of the same week pauses as before. Zero-result and CPA hard-stop pauses stay hard.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from . import cpa, state
from .logging import final_summary, get_logger
from .settings import KpiCfg, Settings

INSUFFICIENT_SPEND = "insufficient_spend"
ZERO_RESULTS = "zero_results_over_min_spend"
OVER_THRESHOLD = "cpl_over_threshold"
WITHIN_THRESHOLD = "within_threshold"
NO_RESULTS_YET = "no_results_yet"
MANUAL_HOLD = "manual_hold"  # owner asked to keep this ad running despite CPL
NAME_RESCUED = "cpl_high_but_creative_sells"  # sales matched by ad name only (renamed campaign)
SOFT_REDUCED = "cpl_over_soft_reduced"  # budget carrier cut instead of pausing (kpi.cpl_soft_reduce)

# TEMPORARY soft-landing (owner 2026-09-10「先降 30%，再犯才关」). The "already cut" state must
# survive across stateless monitor runs, so it lives on Meta itself: a date-stamped adlabel on
# the budget carrier. Labels from earlier Thu-weeks are ignored — each week gets one fresh cut.
SOFT_REDUCE_PREFIX = "ADBOT_CPL30_"

def _week_start_thursday(today: dt.date) -> dt.date:
    """Most recent Thursday (the weekly ON/reset day) on or before `today`."""
    return today - dt.timedelta(days=(today.weekday() - 3) % 7)  # Mon=0..Thu=3


def cpl_window(settings: Settings, today: dt.date):
    """(date_preset, time_range) for the CPL lookback.

    'week_thu' = week-to-date from the most recent Thursday — the window the operator
    actually reviews (matches the weekly OFF/ON cycle). Anything else is a Meta date_preset.
    """
    lookback = settings.kpi.cpl_lookback
    if lookback == "week_thu":
        return None, {"since": _week_start_thursday(today).isoformat(), "until": today.isoformat()}
    return lookback, None


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


def _label_dates(labels: Optional[List[Dict[str, Any]]], prefix: str) -> List[dt.date]:
    """Dates of our soft-reduce labels on an entity; anything unparsable is ignored."""
    out: List[dt.date] = []
    for label in labels or []:
        name = label.get("name") or ""
        if name.startswith(prefix):
            try:
                out.append(dt.date.fromisoformat(name[len(prefix):]))
            except ValueError:
                continue
    return out


def soft_reduce_action(label_dates: List[dt.date], today: dt.date, carrier_budget_myr: float,
                       pct: float, floor_myr: float) -> Tuple[str, Optional[float]]:
    """What to do with an over-CPL ad's budget carrier: ('reduce', new_myr) | ('skip', None)
    | ('pause', None).

    First breach of the Thu-week cuts the carrier by pct (never below floor_myr). A carrier
    already cut TODAY is left alone (the reduced budget needs the rest of the day to prove
    itself — the monitor sweeps every ~20 min, and week-to-date CPL moves slowly). A cut on an
    EARLIER day of the same Thu-week means this breach is the second strike: pause. No visible
    budget, or already at the floor, also escalates to pause — there is nothing left to cut.
    """
    if any(d == today for d in label_dates):
        return "skip", None
    week_start = _week_start_thursday(today)
    if any(week_start <= d < today for d in label_dates):
        return "pause", None
    if carrier_budget_myr <= 0:
        return "pause", None
    new_myr = max(floor_myr, round(carrier_budget_myr * (1 - pct)))
    if new_myr >= carrier_budget_myr:
        return "pause", None
    return "reduce", float(new_myr)


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
    cpa: Optional[float] = None     # 60-day real-sales CPA (None when not judged)
    cpa_sales: int = 0              # 60-day matched paid sales
    age_days: Optional[int] = None  # ad age, for the conversion-window guard
    carrier_kind: Optional[str] = None   # where this ad's budget sits: 'adset' (ABO) | 'campaign' (CBO)
    carrier_id: Optional[str] = None
    carrier_budget_myr: float = 0.0


def _mkey(name: str) -> str:
    """Campaign match key: drop a leading '(Image)' tag Meta adds, then normalise."""
    s = (name or "").strip()
    if s.lower().startswith("(image)"):
        s = s[len("(image)"):]
    return cpa.norm(s)


def build_cpa_context(graph, settings: Settings, today: dt.date):
    """(60-day sales by (campaign,ad), 60-day sales by ad name, 60-day spend by ad_id).

    The ad-name-only index exists because campaigns get renamed in Ads Manager after the
    UTM was stamped, so the strict (campaign, ad) join silently loses those sales (the
    你敢吗 case, 2026-08). Returns empty dicts when CPA is disabled or any source is
    unavailable, so a Sheets/Meta hiccup degrades the monitor to CPL-only, not a crash.
    """
    if not settings.cpa.enabled:
        return {}, {}, {}
    try:
        from .clients.sheets import SheetsClient
        values = SheetsClient(settings.secrets.google_sa_json).read_tab(
            settings.cpa.spreadsheet_id, settings.cpa.sales_tab)
        sales, _cols, _hdr = cpa.parse_sales(values, settings.cpa.price_myr)
        cutoff = today - dt.timedelta(days=60)
        sold: Dict[Tuple[str, str], int] = {}
        sold_by_ad: Dict[str, int] = {}
        for s in sales:
            if s.date and s.date > cutoff:
                key = (_mkey(s.campaign), s.ad)
                sold[key] = sold.get(key, 0) + 1
                if s.ad:
                    sold_by_ad[s.ad] = sold_by_ad.get(s.ad, 0) + 1
        spend: Dict[str, float] = {}
        for row in graph.account_insights(
                settings.meta.account_path, level="ad", fields="ad_id,spend",
                time_range={"since": cutoff.isoformat(), "until": today.isoformat()}):
            try:
                spend[row.get("ad_id")] = float(row.get("spend") or 0)
            except (TypeError, ValueError):
                continue
        return sold, sold_by_ad, spend
    except Exception as exc:  # noqa: BLE001
        get_logger().warning("CPA context unavailable (%s) — CPL-only this run", exc)
        return {}, {}, {}


def evaluate_account(graph, settings: Settings, *, cpa_ctx=None) -> List[AdDecision]:
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
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    cpl_preset, cpl_range = cpl_window(settings, today)
    ctx = cpa_ctx if cpa_ctx is not None else build_cpa_context(graph, settings, today)
    if len(ctx) == 3:
        sold60, sold60_by_ad, spend60 = ctx
    else:                       # legacy (sold, spend) shape — no name-fallback index
        (sold60, spend60), sold60_by_ad = ctx, {}
    use_cpa = settings.cpa.enabled and (bool(sold60) or bool(spend60))
    tiers = cpa.CpaTiers(settings.cpa.healthy_max_myr, settings.cpa.max_acceptable_myr,
                         settings.cpa.hard_stop_myr)
    # ONE account-level insights call for every ad's spend+results in the window, instead of a
    # get_ad_insight per ad — a big account otherwise makes ~1 call per ad and trips Meta's rate
    # limit ("too many calls from this ad account"), which used to crash the whole run.
    cpl_by_ad = {r.get("ad_id"): r for r in graph.account_insights(
        account, level="ad", fields="ad_id,spend,actions",
        date_preset=cpl_preset, time_range=cpl_range)}

    decisions: List[AdDecision] = []
    for campaign in graph.list_campaigns(account):
        if campaign.get("effective_status") != "ACTIVE":  # paused/archived have no live ads
            continue
        camp_key = _mkey(campaign.get("name", ""))
        for ad in graph.list_ads_under_campaign(campaign["id"]):
            if ad.get("effective_status") != "ACTIVE":
                continue
            promoted = (ad.get("adset") or {}).get("promoted_object") or {}
            if (promoted.get("custom_event_type") or "").upper() != want_event:
                continue  # not optimized for our event — not ours to judge or pause
            name = ad.get("name", ad["id"])
            insight = cpl_by_ad.get(ad["id"])   # from the single batched account_insights call
            spend, results = parse_metrics(insight, token)

            # Where this ad's budget sits, for the soft-reduce: its ad set when ABO, else the
            # CBO campaign. No visible daily budget on either level -> None (falls back to pause).
            aset = ad.get("adset") or {}
            try:
                aset_budget = float(aset.get("daily_budget") or 0) / 100.0
            except (TypeError, ValueError):
                aset_budget = 0.0
            try:
                camp_budget = float(campaign.get("daily_budget") or 0) / 100.0
            except (TypeError, ValueError):
                camp_budget = 0.0
            if aset_budget > 0:
                carrier_kind, carrier_id, carrier_budget = "adset", ad.get("adset_id") or aset.get("id"), aset_budget
            elif camp_budget > 0:
                carrier_kind, carrier_id, carrier_budget = "campaign", campaign["id"], camp_budget
            else:
                carrier_kind, carrier_id, carrier_budget = None, None, 0.0

            held = any(h and h in name for h in settings.kpi.cpl_hold)
            if held:                                   # a hold exempts from CPL (not CPA)
                cpl_pause, cpl_reason = False, MANUAL_HOLD
                cpl = (spend / results) if results else (math.inf if spend else None)
            else:
                cpl_pause, cpl_reason, cpl = decide(spend, results, settings.kpi)

            cpa_val: Optional[float] = None
            n_sales, age = 0, None
            should_pause, reason = cpl_pause, cpl_reason
            if use_cpa:
                n_sales = sold60.get((camp_key, cpa.norm(name)), 0)
                sp60 = spend60.get(ad["id"], 0.0)
                cpa_val = cpa.cpa(sp60, n_sales)
                created = cpa.parse_date((ad.get("created_time") or "")[:10])
                age = (today - created).days if created else None
                should_pause, reason = cpa.combined_decision(
                    cpl_pause=cpl_pause, cpl_reason=cpl_reason, cpa_value=cpa_val,
                    cpa_sales=n_sales, cpa_spend=sp60, age_days=age, tiers=tiers,
                    conversion_days=settings.cpa.conversion_days, min_spend=settings.cpa.min_spend_myr)
                if should_pause and n_sales == 0 and sold60_by_ad:
                    # Rename-proof rescue: when the strict (campaign, ad) join finds
                    # nothing, real sales may still exist under the creative's name with
                    # a pre-rename campaign UTM. A name-only match may only ever RESCUE
                    # (block a pause) — it never feeds the hard-stop path, so an
                    # attribution gap can't auto-pause an ad.
                    n_fb = sold60_by_ad.get(cpa.norm(name), 0)
                    fb_cpa = cpa.cpa(sp60, n_fb) if n_fb else None
                    if fb_cpa is not None and fb_cpa != math.inf and fb_cpa <= tiers.hard_stop:
                        should_pause, reason = False, NAME_RESCUED
                        cpa_val, n_sales = fb_cpa, n_fb

            decisions.append(AdDecision(ad["id"], name, spend, results, cpl, should_pause, reason,
                                        cpa=cpa_val, cpa_sales=n_sales, age_days=age,
                                        carrier_kind=carrier_kind, carrier_id=carrier_id,
                                        carrier_budget_myr=carrier_budget))
    return decisions


def run(graph, settings: Settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    event = settings.meta.conversion_event
    kpi = settings.kpi
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    decisions = evaluate_account(graph, settings)
    to_pause = [d for d in decisions if d.should_pause]

    # TEMPORARY soft-landing (kpi.cpl_soft_reduce): plan one action per budget carrier for the
    # OVER_THRESHOLD pauses. Reading labels is a GET, so planning also runs in dry-run mode.
    # A carrier we can't read falls through to the classic pause (no plan entry).
    soft_plan: Dict[str, Dict[str, Any]] = {}   # carrier_id -> {kind, act, new, existing_label_ids}
    if kpi.cpl_soft_reduce:
        for d in to_pause:
            if d.reason != OVER_THRESHOLD or not d.carrier_id or d.carrier_id in soft_plan:
                continue
            try:
                raw = ((graph.get_object(d.carrier_id, "adlabels").get("adlabels") or {})
                       .get("data") or [])
            except Exception as exc:  # noqa: BLE001
                log.warning("  soft-reduce: can't read labels on %s %s (%s) — classic pause",
                            d.carrier_kind, d.carrier_id, exc)
                continue
            act, new_myr = soft_reduce_action(_label_dates(raw, SOFT_REDUCE_PREFIX), today,
                                              d.carrier_budget_myr, kpi.cpl_reduce_pct,
                                              kpi.cpl_reduce_floor_myr)
            soft_plan[d.carrier_id] = {"kind": d.carrier_kind, "act": act, "new": new_myr,
                                       "existing": [l["id"] for l in raw if l.get("id")]}

    def _plan(d: AdDecision) -> Optional[Dict[str, Any]]:
        return soft_plan.get(d.carrier_id) if d.reason == OVER_THRESHOLD else None

    for d in decisions:
        cpl_str = "∞" if d.cpl == math.inf else (f"{d.cpl:.2f}" if d.cpl is not None else "n/a")
        cpa_str = ("" if d.cpa is None else
                   f" CPA={'∞' if d.cpa == math.inf else f'{d.cpa:.0f}'}(60d {d.cpa_sales} sale,{d.age_days}d)")
        plan = _plan(d)
        if not d.should_pause:
            verb = "keep"
        elif plan and plan["act"] == "reduce":
            verb = (f"REDUCE30 {plan['kind']} "
                    f"RM{d.carrier_budget_myr:.0f}→RM{plan['new']:.0f}")
        elif plan and plan["act"] == "skip":
            verb = "GRACE (carrier cut today)"
        elif plan and plan["act"] == "pause":
            verb = "PAUSE (2nd strike this week)"
        else:
            verb = "PAUSE"
        if dry_run and d.should_pause:
            verb = "WOULD " + verb
        log.info("  [%s] %s  spend=%.2f %s=%.0f CPL=%s%s (%s)",
                 verb, d.name, d.spend, event.lower(), d.results, cpl_str, cpa_str, d.reason)

    paused = reduced = 0
    if not dry_run:
        soft_label_id: Optional[str] = None
        done_reduce: set = set()
        for d in to_pause:
            plan = _plan(d)
            if plan and plan["act"] in ("reduce", "skip"):
                if plan["act"] == "reduce" and d.carrier_id not in done_reduce:
                    done_reduce.add(d.carrier_id)
                    try:
                        if soft_label_id is None:
                            soft_label_id = graph.get_or_create_label(
                                settings.meta.account_path, f"{SOFT_REDUCE_PREFIX}{today}")
                        # Label FIRST: the label is the cross-run state. If the budget write then
                        # fails, the next sweep sees "cut today" and skips — it can never compound
                        # a second -30% onto the same carrier.
                        graph.set_ad_labels(d.carrier_id, plan["existing"] + [soft_label_id])
                        graph.update_daily_budget(d.carrier_id, int(round(plan["new"] * 100)))
                        state.append_pause_log(d.carrier_id, plan["kind"], SOFT_REDUCED,
                                               {"ad": d.name, "spend": d.spend, "results": d.results,
                                                "budget_from": d.carrier_budget_myr,
                                                "budget_to": plan["new"]})
                        reduced += 1
                    except Exception as exc:  # noqa: BLE001
                        log.warning("  soft-reduce FAILED on %s %s (%s) — will retry next sweep",
                                    plan["kind"], d.carrier_id, exc)
                continue  # ad itself is spared this run (carrier cut, or cut earlier today)
            graph.update_status(d.ad_id, "PAUSED")
            state.append_pause_log(d.ad_id, "ad", d.reason,
                                   {"spend": d.spend, "results": d.results,
                                    "cpl": None if d.cpl is None or d.cpl == math.inf else round(d.cpl, 2),
                                    "cpa": None if d.cpa is None or d.cpa == math.inf else round(d.cpa, 2),
                                    "cpa_sales": d.cpa_sales})
            paused += 1
    else:
        paused = len([d for d in to_pause if (p := _plan(d)) is None or p["act"] == "pause"])
        reduced = len({d.carrier_id for d in to_pause
                       if (p := _plan(d)) is not None and p["act"] == "reduce"})

    active_left = len([d for d in decisions if not d.should_pause])
    soft_str = (f", cut {reduced} budget carrier(s) −{kpi.cpl_reduce_pct * 100:.0f}%"
                if kpi.cpl_soft_reduce else "")
    summary = (f"CPL monitor ({event}): evaluated {len(decisions)} active ads, "
               f"{'would pause' if dry_run else 'paused'} {paused}{soft_str}, "
               f"{active_left} remain under CPL {settings.kpi.cpl_threshold_myr:.0f} MYR")
    final_summary(log, summary)
    return {"evaluated": len(decisions), "paused": paused, "reduced": reduced,
            "remaining": active_left, "dry_run": dry_run}
