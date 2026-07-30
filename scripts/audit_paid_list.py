# -*- coding: utf-8 -*-
"""Audit the Paid Student List against the owner's EXACT view.

The owner reviews gid=1805763216 with filter view fvid=1919158556. Our CPA layer reads the
tab by NAME and counts every parsed row — if the owner's filter view hides rows (refunds,
non-ads, dupes) or the gid is a different tab, our numbers drift from what the owner sees.

This audit (read-only):
  1. resolves gid 1805763216 -> tab title (is it really "Paid Student List"?)
  2. dumps filter view 1919158556 (range + criteria) and applies what it can
  3. parse diagnostics: rows dropped and why (no utm / no date), per-month histogram, tail rows
  4. recounts last-30d TOP ads / ad sets on BOTH bases (all rows vs owner's filtered view)
"""
from __future__ import annotations

import datetime as dt
import json
from collections import Counter, defaultdict

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

SPREADSHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
GID = 1805763216
FVID = 1919158556
PRICE = 2399.0
WINDOW = 30


def cell(row, idx):
    return row[idx] if 0 <= idx < len(row) else ""


def passes(criteria_by_col, row) -> bool:
    """Apply the filter-view criteria we understand; unknown conditions are treated as pass
    (and reported separately so nothing is silently misapplied)."""
    for col, crit in criteria_by_col.items():
        val = (cell(row, col) or "").strip()
        hidden = crit.get("hiddenValues") or []
        if val in hidden:
            return False
        cond = crit.get("condition") or {}
        ctype = cond.get("type")
        cvals = [v.get("userEnteredValue", "") for v in cond.get("values", [])]
        if not ctype:
            continue
        v_cf = val.casefold()
        cv = cvals[0].casefold() if cvals else ""
        if ctype == "NOT_BLANK":
            if not val:
                return False
        elif ctype == "BLANK":
            if val:
                return False
        elif ctype == "TEXT_CONTAINS":
            if cv not in v_cf:
                return False
        elif ctype == "TEXT_NOT_CONTAINS":
            if cv in v_cf:
                return False
        elif ctype == "TEXT_EQ":
            if v_cf != cv:
                return False
        elif ctype == "ONE_OF_LIST":
            if val not in cvals:
                return False
        # other types: pass-through (reported as unsupported below)
    return True


def top_counts(sales, today):
    cut = today - dt.timedelta(days=WINDOW)
    recent = [x for x in sales if x.date and x.date > cut]
    ad, aset = defaultdict(int), defaultdict(int)
    for x in recent:
        if x.ad:
            ad[x.ad] += 1
        if x.adset:
            aset[x.adset] += 1
    return recent, ad, aset


def show(label, sales, today):
    recent, ad, aset = top_counts(sales, today)
    sg = sum(1 for x in recent if (x.campaign or "").startswith("[sg]"))
    print(f"--- {label}: lifetime={len(sales)} · last-{WINDOW}d={len(recent)} (SG {sg} · other {len(recent)-sg}) ---")
    print("  TOP 5 ADS (30d):")
    for i, (nm, n) in enumerate(sorted(ad.items(), key=lambda kv: (-kv[1], kv[0]))[:5], 1):
        print(f"    {i}. {n:3d}  {nm[:52]}")
    print("  TOP 3 AD SETS (30d):")
    for i, (nm, n) in enumerate(sorted(aset.items(), key=lambda kv: (-kv[1], kv[0]))[:3], 1):
        print(f"    {i}. {n:3d}  {nm[:52]}")
    print()
    return recent


def main() -> None:
    s = load_settings()
    svc = SheetsClient(s.secrets.google_sa_json)._svc
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()

    meta = svc.spreadsheets().get(
        spreadsheetId=SPREADSHEET,
        fields="sheets(properties(sheetId,title,gridProperties(rowCount)),filterViews)").execute()

    tab_title, fv = None, None
    print("== TABS ==")
    for sh in meta.get("sheets", []):
        p = sh.get("properties", {})
        mark = "  <== gid in owner's URL" if p.get("sheetId") == GID else ""
        print(f"  gid={p.get('sheetId')}  rows={p.get('gridProperties',{}).get('rowCount')}  «{p.get('title')}»{mark}")
        if p.get("sheetId") == GID:
            tab_title = p.get("title")
        for v in sh.get("filterViews", []) or []:
            if v.get("filterViewId") == FVID:
                fv = v
    if not tab_title:
        raise SystemExit(f"gid {GID} not found in spreadsheet!")
    print(f"\nowner's tab = «{tab_title}»")

    print("\n== FILTER VIEW fvid=%d ==" % FVID)
    criteria_by_col = {}
    unsupported = []
    if not fv:
        print("  (filter view not found — maybe deleted; auditing unfiltered)")
    else:
        rng = fv.get("range", {})
        print(f"  title=«{fv.get('title')}»  range rows {rng.get('startRowIndex')}..{rng.get('endRowIndex')} "
              f"cols {rng.get('startColumnIndex')}..{rng.get('endColumnIndex')}")
        # two API shapes: criteria{col: {...}} (legacy) or filterSpecs[]
        crit = fv.get("criteria") or {}
        for col, cdef in crit.items():
            criteria_by_col[int(col)] = cdef
        for spec in fv.get("filterSpecs", []) or []:
            if "columnIndex" in spec:
                criteria_by_col[int(spec["columnIndex"])] = spec.get("filterCriteria", {})
        for col, cdef in sorted(criteria_by_col.items()):
            ctype = (cdef.get("condition") or {}).get("type")
            hid = cdef.get("hiddenValues") or []
            print(f"  col {col}: hiddenValues={hid[:8]}{'…' if len(hid) > 8 else ''}  condition={ctype}"
                  f" {json.dumps((cdef.get('condition') or {}).get('values', []), ensure_ascii=False)[:80]}")
            if ctype and ctype not in ("NOT_BLANK", "BLANK", "TEXT_CONTAINS", "TEXT_NOT_CONTAINS",
                                       "TEXT_EQ", "ONE_OF_LIST"):
                unsupported.append((col, ctype))
        if fv.get("sortSpecs"):
            print("  (sortSpecs present — sorting only, doesn't hide rows)")
    if unsupported:
        print(f"  ⚠️ unsupported condition types (NOT applied): {unsupported}")

    vals = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET, range=tab_title,
        valueRenderOption="FORMATTED_VALUE", dateTimeRenderOption="FORMATTED_STRING",
    ).execute().get("values", [])
    sales_all, cols, header = C.parse_sales(vals, PRICE)
    hdr_idx = vals.index(header)
    data_rows = vals[hdr_idx + 1:]

    print(f"\n== PARSE DIAGNOSTICS («{tab_title}») ==")
    print(f"  sheet rows={len(vals)} (header at row {hdr_idx+1})  data rows={len(data_rows)}  parsed sales={len(sales_all)}")
    print(f"  header cols -> {cols}")
    no_utm = sum(1 for r in data_rows if not (C.norm(cell(r, cols.get('campaign', -1))) or C.norm(cell(r, cols.get('ad', -1)))))
    no_date = sum(1 for x in sales_all if x.date is None)
    print(f"  dropped (no utm campaign AND no utm ad) = {no_utm}   parsed-but-undated = {no_date}"
          f"{'  ⚠️ undated rows NEVER count in any 30d window' if no_date else ''}")
    months = Counter(f"{x.date:%Y-%m}" for x in sales_all if x.date)
    print("  per-month:", "  ".join(f"{m}:{c}" for m, c in sorted(months.items())))
    print("  last 6 data rows (freshness check):")
    dcol, adcol = cols.get("date", -1), cols.get("ad", -1)
    for r in data_rows[-6:]:
        print(f"    date={cell(r, dcol)!r:14} ad={cell(r, adcol)[:40]!r}")

    print(f"\n== BASIS A: ALL parsed rows (what my previous reports used) ==")
    show("ALL ROWS", sales_all, today)

    if criteria_by_col:
        kept_rows = [r for r in data_rows if passes(criteria_by_col, r)]
        hidden_ct = len(data_rows) - len(kept_rows)
        sales_f, _c, _h = C.parse_sales([header] + kept_rows, PRICE)
        print(f"== BASIS B: OWNER'S FILTER VIEW applied (hides {hidden_ct} data rows) ==")
        show("FILTERED (your view)", sales_f, today)
        # what got excluded, by ad (30d) — so the delta is explainable
        ra, _, _ = top_counts(sales_all, today)
        rf, _, _ = top_counts(sales_f, today)
        delta = Counter(x.ad or "(blank)" for x in ra) - Counter(x.ad or "(blank)" for x in rf)
        if delta:
            print("  30d rows your filter EXCLUDES, by ad:")
            for nm, n in delta.most_common(10):
                print(f"    -{n}  {nm[:52]}")
    else:
        print("== BASIS B: (filter view has no row-hiding criteria — bases identical) ==")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
