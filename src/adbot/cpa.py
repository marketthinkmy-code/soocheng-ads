"""CPA (cost per real paid acquisition) attribution from the Paid Student List.

Each sales row carries the UTM (campaign / ad set / ad name) that drove a paid enrolment
plus a created date. We parse the tab by *header name* (robust to column reordering),
normalise the UTM values for matching against Meta entity names, and window sales by date
(14 / 30 / 60 days + lifetime). Joining Meta spend then yields CPA; the tiers below encode
the operator's KPI. Pure functions only — no I/O — so this is fully unit-tested.
"""
from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

WINDOWS = (14, 30, 60)  # rolling day windows; lifetime is handled separately

# decision tiers (reason codes)
KEEP = "cpa_keep"
MONITOR = "cpa_monitor"
PAUSE_CANDIDATE = "cpa_pause_candidate"
HARD_STOP = "cpa_hard_stop"
NO_SALES = "cpa_no_sales"


def norm(s: str) -> str:
    """Normalise a UTM/name value for matching: unescape, collapse whitespace, casefold."""
    s = (s or "").replace("\\", "")
    return " ".join(s.split()).casefold()


def _hkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").casefold())


def find_columns(header: List[str]) -> Dict[str, int]:
    """Locate date / campaign / adset / ad / amount columns by fuzzy header match."""
    keys = [_hkey(h) for h in header]

    def first(*needles_in_order) -> int:
        for needle in needles_in_order:                 # exact-ish matches first
            for i, k in enumerate(keys):
                if k == needle:
                    return i
        for needle in needles_in_order:                 # then substring
            for i, k in enumerate(keys):
                if needle in k:
                    return i
        return -1

    return {
        "date": first("createddate", "date"),
        "campaign": first("utmcampaign"),
        "adset": first("utmadset", "utmadsset"),
        "ad": first("utmadname", "utmadsname"),
        "amount": first("purchaseamount", "amount"),
    }


def parse_date(s: str) -> Optional[dt.date]:
    s = (s or "").strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)         # D/M/YYYY (sheet default)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        y = y + 2000 if y < 100 else y
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)            # ISO fallback
    if m:
        y, mo, d = (int(x) for x in m.groups())
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    return None


def _money(s: str, default: float) -> float:
    digits = re.sub(r"[^\d.]", "", s or "")
    try:
        val = float(digits)
        return val if val > 0 else default
    except ValueError:
        return default


@dataclass
class Sale:
    date: Optional[dt.date]
    campaign: str   # normalised
    adset: str      # normalised
    ad: str         # normalised
    amount: float


def parse_sales(values: List[List[str]], default_price: float):
    """Find the header row, then parse data rows into Sale records.

    Returns (sales, columns, header_row). The header is the first of the top rows that
    exposes both a UTM campaign and a UTM ad column.
    """
    if not values:
        return [], {}, []
    header_idx, cols = 0, find_columns(values[0])
    for i, row in enumerate(values[:8]):
        candidate = find_columns(row)
        if candidate.get("campaign", -1) >= 0 and candidate.get("ad", -1) >= 0:
            header_idx, cols = i, candidate
            break
    header = values[header_idx]

    sales: List[Sale] = []
    for row in values[header_idx + 1:]:
        def cell(key: str) -> str:
            idx = cols.get(key, -1)
            return row[idx] if 0 <= idx < len(row) else ""

        campaign, ad = norm(cell("campaign")), norm(cell("ad"))
        if not campaign and not ad:
            continue
        sales.append(Sale(parse_date(cell("date")), campaign, norm(cell("adset")),
                          ad, _money(cell("amount"), default_price)))
    return sales, cols, header


def count_windows(sales: List[Sale], today: dt.date, windows=WINDOWS) -> Dict[str, int]:
    """Count sales in each rolling window plus lifetime (key 'life')."""
    out = {f"{w}d": 0 for w in windows}
    out["life"] = len(sales)
    for s in sales:
        if s.date is None:
            continue
        for w in windows:
            if s.date > today - dt.timedelta(days=w):
                out[f"{w}d"] += 1
    return out


def attribute(sales: List[Sale], today: dt.date, windows=WINDOWS):
    """Group sales by (campaign, adset, ad), by (campaign, adset), and by campaign."""
    by_ad: Dict[Tuple[str, str, str], List[Sale]] = {}
    by_adset: Dict[Tuple[str, str], List[Sale]] = {}
    by_campaign: Dict[str, List[Sale]] = {}
    for s in sales:
        by_ad.setdefault((s.campaign, s.adset, s.ad), []).append(s)
        by_adset.setdefault((s.campaign, s.adset), []).append(s)
        by_campaign.setdefault(s.campaign, []).append(s)
    counts = lambda groups: {k: count_windows(v, today, windows) for k, v in groups.items()}
    return counts(by_ad), counts(by_adset), counts(by_campaign)


def cpa(spend: float, sales_count: int):
    """Cost per acquisition; inf when there is spend but no sales, None when no spend."""
    if sales_count > 0:
        return spend / sales_count
    return math.inf if spend > 0 else None


@dataclass
class CpaTiers:
    healthy_max: float = 800.0
    max_acceptable: float = 960.0
    hard_stop: float = 1200.0


def cpa_tier(cpa_value, tiers: CpaTiers) -> str:
    """Map a CPA to a decision tier reason code."""
    if cpa_value is None:
        return NO_SALES          # no spend yet — not judgeable
    if cpa_value == math.inf:
        return NO_SALES          # spent, no sales (handled with min-spend/age elsewhere)
    if cpa_value <= tiers.healthy_max:
        return KEEP
    if cpa_value <= tiers.max_acceptable:
        return MONITOR
    if cpa_value <= tiers.hard_stop:
        return PAUSE_CANDIDATE
    return HARD_STOP
