# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: for Paid Student List rows dated >= 10/21, look the buyer up in the Register tab
(by email, then phone digits) and print only: sale date · found? · register date · source · UTM campaign/ad set/ad.
Emails/phones are used for the join inside this run and never printed."""
from __future__ import annotations

import datetime as dt
import re

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings


def _hdr(vals, need):
    hi = next(i for i, r in enumerate(vals[:8]) if need in r)
    return hi, vals[hi]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    sc = SheetsClient(s.secrets.google_sa_json)
    paid = sc.read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    reg = sc.read_tab(s.cpa.spreadsheet_id, "Register")
    phi, ph = _hdr(paid, "UTM Campaign")
    rhi, rh = _hdr(reg, "UTM Campaign")
    em = lambda v: (v or "").strip().lower()
    tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
    idx = {}
    for r in reg[rhi + 1:]:
        row = dict(zip(rh, r))
        for k in (em(row.get("Email")), tel(row.get("Phone Number"))):
            if k:
                idx.setdefault(k, []).append(row)
    for r in paid[phi + 1:]:
        row = dict(zip(ph, r))
        d = cpa.parse_date(row.get("Date", ""))
        if not d or d < dt.date(2026, 10, 21):
            continue
        hits = idx.get(em(row.get("Email"))) or idx.get(tel(row.get("Phone Number"))) or []
        print(f"\n成交 {d} · {row.get('Source', '')} · 表内 UTM «{row.get('UTM Campaign', '')[:40]}» · Register 命中 {len(hits)} 行")
        for h in hits[-6:]:
            print(f"    报名 {h.get('Created date', '')[:22]} · {h.get('Source', '')[:28]} · «{h.get('UTM Campaign', '')[:50]}» / {h.get('UTM Ads Set', '')[:24]} / {h.get('UTM Ads Name', '')[:28]}")
    print("\nMATCH DONE (read-only)")


if __name__ == "__main__":
    main()
