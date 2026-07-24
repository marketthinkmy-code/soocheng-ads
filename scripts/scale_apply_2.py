# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-24):
  (info)  which ad(s) drove the MY GOLF PICKLEBALL 1-1-3 sales — from the Paid Student List.
  (action) SCALE 8 proven low-CPA campaigns +40-100% (moderate — 10-day campaigns, don't
           reset learning). Matched by name + current budget (two MY TRAVEL|1-1-3 exist:
           RM100 and RM250 — disambiguated by current daily_budget).

Live budget change is immediate + reversible. Dry-run unless CONFIRM=true. Each budget POST
is isolated so one rejection (e.g. an account cap) never blocks the rest.
"""
from __future__ import annotations

import os
from collections import Counter

from adbot import cpa as C
from adbot.clients.graph import GraphError
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
PRICE = 2399.0
MY = "act_759339046918885"
SG = "act_893025326577600"

# (account, name_substring, expected_current_budget_cents|None, new_budget_cents, label)
SCALE = [
    (SG, "GOLF",                 None,  40000, "SG GOLF"),
    (SG, "TRAVEL | 1-1-3 (2)",   None,  37500, "SG TRAVEL(2)"),
    (SG, "INVESTMENT | 1-1-3",   None,  35000, "SG INVESTMENT"),
    (SG, "BROAD | 1-1-3 A",      None,  35000, "SG BROAD A"),
    (SG, "BROAD | 1-1-3 B",      None,  35000, "SG BROAD B"),
    (MY, "TRAVEL | 1-1-3",       10000, 20000, "MY TRAVEL[100]"),
    (MY, "BUSINESS OWNER | 1-1-3", None, 18000, "MY BUSINESS OWNER"),
    (MY, "TRAVEL | 1-1-3",       25000, 32000, "MY TRAVEL[250]"),
]


def budget_cents(c) -> int:
    try:
        return int(c.get("daily_budget") or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = C.parse_sales(vals, PRICE)

    camps = {acct: g._get_all(f"{acct}/campaigns",
             {"fields": "id,name,effective_status,daily_budget", "limit": "300"})
             for acct in (MY, SG)}

    # ── (1) which ad(s) converted in GOLF (MY, and SG for context — GOLF is the #1 campaign) ──
    print("== GOLF PICKLEBALL — which ad(s) actually converted (paid buyers) ==")
    for acct, tag in ((MY, "MY"), (SG, "SG")):
        for c in [x for x in camps[acct] if "golf" in x["name"].lower()]:
            key = C.norm(c["name"])
            rows = [x for x in sales if x.campaign == key]
            print(f"  [{tag}] «{c['name']}»  [{c['effective_status']}]  id={c['id']}  "
                  f"RM{budget_cents(c)/100:.0f}/d  — {len(rows)} buyer(s)")
            by_ad = Counter((x.ad or "(no ad name in sheet)") for x in rows)
            for ad, ct in by_ad.most_common():
                dts = sorted(str(x.date) for x in rows if (x.ad or "(no ad name in sheet)") == ad)
                print(f"        {ct}×  {ad[:64]}   {dts}")
    print()

    # ── (2) scale the 8 winners ──
    print(f"== SCALE 8 winners (CONFIRM={CONFIRM}) ==")
    for acct, sub, expb, newb, label in SCALE:
        cand = [c for c in camps[acct]
                if sub.lower() in c["name"].lower()
                and c.get("effective_status") == "ACTIVE"
                and (expb is None or budget_cents(c) == expb)]
        if len(cand) != 1:
            print(f"  ⚠️ {label}: «{sub}»"
                  + (f" @RM{expb/100:.0f}" if expb else "")
                  + f" matched {len(cand)} ACTIVE campaigns — SKIP (resolve manually)")
            for c in cand:
                print(f"        - {c['name']} [{c.get('effective_status')}] RM{budget_cents(c)/100:.0f}")
            continue
        c = cand[0]
        old = budget_cents(c)
        if not CONFIRM:
            print(f"  WOULD SET {label:18} {c['id']}  «{c['name'][:42]}»  RM{old/100:.0f} -> RM{newb/100:.0f}")
            continue
        try:
            g._request("POST", c["id"], data={"daily_budget": newb})
            print(f"  ✓ {label:18} {c['id']}  RM{old/100:.0f} -> RM{newb/100:.0f}")
        except GraphError as e:
            print(f"  ✗ {label:18} {c['id']}  RM{old/100:.0f} -> RM{newb/100:.0f}  FAILED: {e}")

    print("\nDONE — budgets raised live." if CONFIRM else "\nDRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
