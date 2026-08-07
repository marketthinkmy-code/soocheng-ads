# -*- coding: utf-8 -*-
"""Monthly sales analysis (June / July / August) from the Paid Student List.

Owner ask 2026-08-04: per-month 成交 breakdown incl. which ads converted, accuracy
first. So: the same battle-tested parser the CPA layer uses (header-by-name, tolerant
dates, per-row amount), full parse diagnostics, and BOTH bases reported — A: every
parsed row; B: the owner's own filter view (gid 1805763216 / fvid 1919158556) — with
the per-ad delta explained, so my numbers can be reconciled against the sheet they see.
Read-only; no Meta calls.
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
MONTHS = ("2026-06", "2026-07", "2026-08")


def cell(row, idx):
    return row[idx] if 0 <= idx < len(row) else ""


def passes(criteria_by_col, row) -> bool:
    for col, crit in criteria_by_col.items():
        val = (cell(row, col) or "").strip()
        if val in (crit.get("hiddenValues") or []):
            return False
        cond = crit.get("condition") or {}
        ctype = cond.get("type")
        cvals = [v.get("userEnteredValue", "") for v in cond.get("values", [])]
        v_cf, cv = val.casefold(), (cvals[0].casefold() if cvals else "")
        if ctype == "NOT_BLANK" and not val:
            return False
        if ctype == "BLANK" and val:
            return False
        if ctype == "TEXT_CONTAINS" and cv not in v_cf:
            return False
        if ctype == "TEXT_NOT_CONTAINS" and cv in v_cf:
            return False
        if ctype == "TEXT_EQ" and v_cf != cv:
            return False
        if ctype == "ONE_OF_LIST" and val not in cvals:
            return False
    return True


def bucket(campaign: str) -> str:
    if not campaign:
        return "无UTM"
    if campaign.startswith("[sg]"):
        return "SG新户"
    if campaign.startswith("stockbloom"):
        return "MY新户"
    return "旧账户/其他"


def month_report(label, sales):
    print(f"\n════════ {label} ════════")
    grand = 0
    for m in MONTHS:
        rows = [s for s in sales if s.date and f"{s.date:%Y-%m}" == m]
        n, rev = len(rows), sum(s.amount for s in rows)
        grand += n
        prices = Counter(int(s.amount) for s in rows)
        acct = Counter(bucket(s.campaign) for s in rows)
        print(f"\n── {m}: {n} 单 · RM{rev:,.0f} ──")
        print("   价格构成: " + "  ".join(f"RM{p:,}×{c}" for p, c in prices.most_common()))
        print("   账户构成: " + "  ".join(f"{k}:{v}" for k, v in acct.most_common()))
        by_ad = defaultdict(lambda: [0, 0.0, Counter()])
        for s in rows:
            key = s.ad or "(无 ad UTM)"
            by_ad[key][0] += 1
            by_ad[key][1] += s.amount
            by_ad[key][2][s.campaign or "(无 campaign)"] += 1
        print(f"   转化广告 ({len(by_ad)} 条不同 ad):")
        for ad, (cnt, rv, camps) in sorted(by_ad.items(), key=lambda kv: -kv[1][0]):
            camp = camps.most_common(1)[0][0]
            more = f" +{len(camps)-1}camp" if len(camps) > 1 else ""
            print(f"     {cnt:>2} 单 RM{rv:>7,.0f}  {ad[:44]:44} ← {camp[:36]}{more}")
    undated = sum(1 for s in sales if s.date is None)
    print(f"\n   {MONTHS[0][:4]} 三个月合计 {grand} 单"
          + (f"   ⚠️ 另有 {undated} 行无日期（无法归月）" if undated else ""))


def main() -> None:
    s = load_settings()
    svc = SheetsClient(s.secrets.google_sa_json)._svc
    meta = svc.spreadsheets().get(
        spreadsheetId=SPREADSHEET,
        fields="sheets(properties(sheetId,title),filterViews)").execute()
    tab_title, fv = None, None
    for sh in meta.get("sheets", []):
        if sh.get("properties", {}).get("sheetId") == GID:
            tab_title = sh["properties"].get("title")
        for v in sh.get("filterViews", []) or []:
            if v.get("filterViewId") == FVID:
                fv = v
    if not tab_title:
        raise SystemExit(f"gid {GID} not found")
    print(f"tab «{tab_title}» (gid {GID})")

    vals = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET, range=tab_title,
        valueRenderOption="FORMATTED_VALUE", dateTimeRenderOption="FORMATTED_STRING",
    ).execute().get("values", [])
    sales_all, cols, header = C.parse_sales(vals, s.cpa.price_myr)
    hdr_idx = vals.index(header)
    data_rows = vals[hdr_idx + 1:]
    no_utm = sum(1 for r in data_rows
                 if not (C.norm(cell(r, cols.get("campaign", -1))) or C.norm(cell(r, cols.get("ad", -1)))))
    latest = max((x.date for x in sales_all if x.date), default=None)
    print(f"rows={len(data_rows)} parsed={len(sales_all)} dropped(no-utm)={no_utm} latest={latest}")
    print("per-month all-time: " + "  ".join(
        f"{m}:{c}" for m, c in sorted(Counter(f'{x.date:%Y-%m}' for x in sales_all if x.date).items())))

    month_report("口径 A：全表（所有解析行）", sales_all)

    criteria_by_col = {}
    if fv:
        for col, cdef in (fv.get("criteria") or {}).items():
            criteria_by_col[int(col)] = cdef
        for spec in fv.get("filterSpecs", []) or []:
            if "columnIndex" in spec:
                criteria_by_col[int(spec["columnIndex"])] = spec.get("filterCriteria", {})
    if criteria_by_col:
        kept = [r for r in data_rows if passes(criteria_by_col, r)]
        sales_f, _c, _h = C.parse_sales([header] + kept, s.cpa.price_myr)
        month_report(f"口径 B：你的筛选视图 fvid={FVID}（隐藏 {len(data_rows)-len(kept)} 行）", sales_f)
        for m in MONTHS:
            da = Counter((x.ad or "(blank)") for x in sales_all if x.date and f"{x.date:%Y-%m}" == m)
            df = Counter((x.ad or "(blank)") for x in sales_f if x.date and f"{x.date:%Y-%m}" == m)
            delta = da - df
            if delta:
                print(f"   {m} 你的视图比全表少: " +
                      "; ".join(f"{nm[:30]}×{n}" for nm, n in delta.most_common(6)))
    else:
        print("\n(筛选视图无隐藏条件 — 两个口径相同)")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
