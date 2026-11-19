"""CPA (cost per real paid acquisition) attribution from the Paid Student List.

Each sales row carries the UTM (campaign / ad set / ad name) that drove a paid enrolment
plus a created date. We parse the tab by *header name* (robust to column reordering),
normalise the UTM values for matching against Meta entity names, and window sales by date
(14 / 30 / 60 days + lifetime). Joining Meta spend then yields CPA; the tiers below encode
the operator's KPI. Pure functions only — no I/O — so this is fully unit-tested.
"""
from __future__ import annotations

import calendar
import datetime as dt
import math
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

WINDOWS = (14, 30, 60)  # rolling day windows; lifetime is handled separately

# decision tiers (reason codes)
KEEP = "cpa_keep"
MONITOR = "cpa_monitor"
PAUSE_CANDIDATE = "cpa_pause_candidate"
HARD_STOP = "cpa_hard_stop"
NO_SALES = "cpa_no_sales"


def norm(s: str) -> str:
    """Normalise a UTM/name value for matching: unescape, collapse whitespace, casefold.

    Also strips the 🌟 marker the owner prefixes onto sold-chain campaigns/ads in Ads
    Manager (2026-09-03 «加上 🌟 做个记录，以免误关»), and the 🚫 ban mark (2026-10-08),
    so a marked live name still matches the unmarked UTM names stamped in the sales
    sheet — and vice versa.
    """
    s = (s or "").replace("\\", "").replace("🌟", "").replace("🚫", "")
    return " ".join(s.split()).casefold()


def _hkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").casefold())


_CREATIVE_PREFIXES = ("hook：", "hook:", "重拍：", "重拍:", "拼接：", "拼接:")


def creative_key(name: str) -> str:
    """norm() plus stripping edition prefixes (HOOK：/ 重拍：), repeatedly.

    A re-cut of a proven creative gets a prefixed ad name («HOOK：Video 12：炒过那么多»),
    but its sales history in the sheet sits under the original name — without this the
    name-only CPA rescue can't see those sales and the monitor kills the re-cut on CPL
    alone (2026-09-14, HOOK 炒过那么多). Used ONLY for the rescue index, never for the
    strict (campaign, ad) join.
    """
    key = norm(name)
    changed = True
    while changed:
        changed = False
        for prefix in _CREATIVE_PREFIXES:
            if key.startswith(prefix):
                key = key[len(prefix):].strip()
                changed = True
    return key


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


_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
_MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_name) if m})


def _safe(y: int, mo: int, d: int) -> Optional[dt.date]:
    y = y + 2000 if y < 100 else y
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def parse_date(s: str) -> Optional[dt.date]:
    """Tolerant date parser: ISO, D/M/Y & M/D/Y (/ - . separators, optional time), month
    names (14 Jan 2026 / Jan 14, 2026), and Google Sheets serial numbers."""
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)              # ISO 2026-01-14
    if m:
        y, mo, d = (int(x) for x in m.groups())
        return _safe(y, mo, d)
    m = re.match(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", s)           # D/M/Y or M/D/Y
    if m:
        a, b, y = (int(x) for x in m.groups())
        if a > 12 and b <= 12:
            return _safe(y, b, a)                                       # a is the day
        if b > 12 and a <= 12:
            return _safe(y, a, b)                                       # month-first
        return _safe(y, b, a) or _safe(y, a, b)                         # ambiguous -> day-first (MY)
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\.?,?\s+(\d{2,4})", s)        # 14 Jan 2026
    if m and m.group(2).lower() in _MONTHS:
        return _safe(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{2,4})", s)        # Jan 14, 2026
    if m and m.group(1).lower() in _MONTHS:
        return _safe(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)))
    if re.fullmatch(r"\d{4,6}", s):                                     # Sheets serial
        try:
            return dt.date(1899, 12, 30) + dt.timedelta(days=int(s))
        except (ValueError, OverflowError):
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


def _sales_header(values: List[List[str]]) -> Tuple[int, Dict[str, int]]:
    """(header row index, columns): the first of the top rows that exposes both a UTM campaign
    and a UTM ad column, else row 0."""
    header_idx, cols = 0, find_columns(values[0])
    for i, row in enumerate(values[:8]):
        candidate = find_columns(row)
        if candidate.get("campaign", -1) >= 0 and candidate.get("ad", -1) >= 0:
            header_idx, cols = i, candidate
            break
    return header_idx, cols


def parse_sales(values: List[List[str]], default_price: float):
    """Find the header row, then parse data rows into Sale records.

    Returns (sales, columns, header_row). The header is the first of the top rows that
    exposes both a UTM campaign and a UTM ad column.
    """
    if not values:
        return [], {}, []
    header_idx, cols = _sales_header(values)
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


# combined CPA × CPL reason codes
CPL_RESCUED = "cpl_high_but_cpa_ok"   # over-CPL, but real sales at an acceptable CPA -> keep
CPA_IMMATURE = "cpa_immature"         # inside the conversion window -> no CPA judgement yet


def combined_decision(*, cpl_pause: bool, cpl_reason: str, cpa_value, cpa_sales: int,
                      cpa_spend: float, age_days, tiers: CpaTiers,
                      conversion_days: int = 14, min_spend: float = 0.0):
    """Fold real-sales CPA into the CPL pause decision — the operator's policy.

    1. Auto-pause on CPA only for a *proven* hard stop: real matched sales, finite CPA above
       the hard-stop line, past the conversion window, with enough spend. Zero matched sales
       never auto-pauses on CPA (it may be an attribution gap, not true waste).
    2. CPA *rescues* an ad the CPL guardrail would pause when it has real sales at CPA at or
       below the hard stop (still profitable against the ~RM2.4k price) — so registration
       cost alone never kills a money-making ad. Rescue ignores age: real sales are real.

    Returns (should_pause, reason).
    """
    finite_cpa = cpa_value is not None and cpa_value != math.inf
    matured = age_days is not None and age_days >= conversion_days and cpa_spend >= min_spend

    if cpa_sales > 0 and finite_cpa and cpa_value > tiers.hard_stop and matured:
        return True, HARD_STOP                       # proven too expensive
    if cpl_pause and cpa_sales > 0 and finite_cpa and cpa_value <= tiers.hard_stop:
        return False, CPL_RESCUED                    # real profitable sales protect it
    return cpl_pause, cpl_reason                      # otherwise the CPL decision stands


# ---------------------------------------------------------------------------------------------
# Register-UTM sales join — owner 2026-11-19「开回 + 修 monitor」+「一定要看完 campaign、ad set、ad」
# ---------------------------------------------------------------------------------------------
def contact_keys(email: str, phone: str) -> Tuple[str, ...]:
    """Identity keys of a person: lower-cased email, last 8 digits of the phone (if ≥8 digits)."""
    e = (email or "").strip().lower()
    d = re.sub(r"\D", "", phone or "")
    return tuple(k for k in (e if "@" in e else "", d[-8:] if len(d) >= 8 else "") if k)


def _named_table(values: List[List[str]], must: str) -> Tuple[List[str], List[List[str]]]:
    """(header hkeys, data rows): header = first of the top 8 rows whose hkeys include `must`."""
    for i, row in enumerate((values or [])[:8]):
        keys = [_hkey(h) for h in row]
        if must in keys:
            return keys, values[i + 1:]
    return [], []


def _col(keys: List[str], *needles: str) -> int:
    for n in needles:                       # exact first, then substring
        if n in keys:
            return keys.index(n)
    for n in needles:
        for i, k in enumerate(keys):
            if n in k:
                return i
    return -1


def position_buyers(paid_values: List[List[str]], register_values: List[List[str]], *,
                    cutoff: dt.date, reg_since: dt.date,
                    camp_key: Callable[[str], str], adset_key: Callable[[str], str]):
    """Buyers per ad position, as sets of Paid-row ids, from two joins (the caller unions them per ad).

    Both joins use the SAME strict position key the monitor has always used:
    (camp_key(campaign), adset_key(ad set), norm(ad)) — campaign AND ad set AND ad must all match
    (owner 11/19「一定要看完 campaign、ad set、ad」; camp_key only ignores the «| 1-x-y |» segment, PR #90).

    exact  — the Paid row's own UTM (unchanged).
    robust — the Register row of the registration: since 10/29 the Register tab stores the UTM of THAT
             registration, while the Paid row's UTM is often blank or the contact's first-ever source
             (10/29 diagnosis). For each Paid row (dated after `cutoff`) take the same person's (email, or
             phone last 8 digits) LAST registration with an ad UTM, on/after `reg_since` and on/before the
             purchase date — one sale, one registration position.
             Why: SG BROAD SG 年纪大 was paused on CPL 80.21 on 11/14 although its buyer registered through it.

    Returns (exact, robust) — dicts of key -> set of Paid-row ids. No personal data leaves this function.
    """
    exact: Dict[Tuple[str, str, str], Set[int]] = {}
    robust: Dict[Tuple[str, str, str], Set[int]] = {}
    if not paid_values:
        return exact, robust
    hi, cols = _sales_header(paid_values)
    pkeys = [_hkey(h) for h in paid_values[hi]]
    pe, pp = _col(pkeys, "email"), _col(pkeys, "phonenumber", "phone")
    cell = lambda row, i: row[i] if 0 <= i < len(row) else ""
    buyers: List[Tuple[int, dt.date, Tuple[str, ...]]] = []
    for rid, row in enumerate(paid_values[hi + 1:]):
        d = parse_date(cell(row, cols.get("date", -1)))
        if not d or d <= cutoff:
            continue
        campaign, ad = norm(cell(row, cols.get("campaign", -1))), norm(cell(row, cols.get("ad", -1)))
        if campaign or ad:
            k = (camp_key(campaign), adset_key(norm(cell(row, cols.get("adset", -1)))), ad)
            exact.setdefault(k, set()).add(rid)
        who = contact_keys(cell(row, pe), cell(row, pp))
        if who:
            buyers.append((rid, d, who))

    rkeys, rrows = _named_table(register_values, "utmcampaign")
    if not rkeys or not buyers:
        return exact, robust
    rd, rc = _col(rkeys, "createddate", "date"), _col(rkeys, "utmcampaign")
    rs, ra = _col(rkeys, "utmadsset", "utmadset"), _col(rkeys, "utmadsname", "utmadname")
    re_, rp = _col(rkeys, "email"), _col(rkeys, "phonenumber", "phone")
    regs: Dict[str, List[Tuple[dt.date, int, Tuple[str, str, str]]]] = {}
    for order, row in enumerate(rrows):
        campaign = norm(cell(row, rc))
        if not campaign:
            continue
        d = parse_date(cell(row, rd))
        if not d or d < reg_since:
            continue
        k = (camp_key(campaign), adset_key(norm(cell(row, rs))), norm(cell(row, ra)))
        for ck in contact_keys(cell(row, re_), cell(row, rp)):
            regs.setdefault(ck, []).append((d, order, k))
    for rid, pd, who in buyers:
        cands = [x for ck in who for x in regs.get(ck, ()) if x[0] <= pd]
        if cands:
            robust.setdefault(max(cands)[2], set()).add(rid)
    return exact, robust
