# -*- coding: utf-8 -*-
"""Read-only scale/pause/reopen review — judge by REAL BUYERS (Paid Student List) + CPA,
not registration CPL. Joins live Meta per-campaign spend with sheet buyers for BOTH accounts.

Per campaign: lifetime spend / buyers -> CPA(life), and last-30d spend / registrations (CPL)
/ buyers (CPA-30d). A REC column applies the operator's CPA tiers so the winners to scale and
the wasters to check jump out. Nothing is changed — this only prints. (CLAUDE.md: cheapest CPL
≠ best ad; Travel had the lowest CPL but the worst CPA.)
"""
from __future__ import annotations

import datetime as dt
import math

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]
PRICE = 2399.0
TARGET, HEALTHY, HARDSTOP = 720.0, 800.0, 1200.0   # CPA tiers (config/cpa)
NEW_DAYS = 14                                       # younger than this -> too early to judge CPA


def regs(actions) -> int:
    best = 0
    for a in actions or []:
        if "complete_registration" in (a.get("action_type") or ""):
            try:
                best = max(best, int(float(a.get("value", 0))))
            except (TypeError, ValueError):
                pass
    return best


def fmt(x) -> str:
    if x is None:
        return "—"
    if x == math.inf:
        return "∞"
    return f"RM{x:,.0f}"


def rec_for(st: str, sp_life: float, b_life: int, cpa_life, age_days) -> str:
    active = st == "ACTIVE"
    young = age_days is not None and age_days < NEW_DAYS
    if young:
        return "🆕 too new"
    if b_life >= 3 and cpa_life is not None and cpa_life != math.inf:
        if cpa_life <= TARGET:
            return "⏫ SCALE" if active else "♻️ REOPEN"
        if cpa_life <= HEALTHY:
            return "✅ keep" if active else "♻️ reopen?"
        if cpa_life <= HARDSTOP:
            return "👀 watch CPA"
        return "🛑 PAUSE (CPA)" if active else "leave off"
    if active and sp_life >= 1500 and b_life == 0:
        return "⚠️ verify (0 buyers)"
    if b_life >= 1 and cpa_life is not None and cpa_life <= HEALTHY:
        return "✅ keep" if active else "♻️ reopen?"
    return "· watch"


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = C.parse_sales(vals, PRICE)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    _byad, _byaset, bycamp = C.attribute(sales, today)
    print(f"sheet rows={len(vals)}  parsed sales={len(sales)}  as-of {today} (GMT+8)\n")

    matched_keys = set()
    for label, acct in ACCTS:
        life = {r.get("campaign_id"): r for r in g.account_insights(
            acct, level="campaign", fields="campaign_id,campaign_name,spend", date_preset="maximum")}
        d30 = {r.get("campaign_id"): r for r in g.account_insights(
            acct, level="campaign", fields="campaign_id,campaign_name,spend,actions",
            date_preset="last_30d")}
        camps = g._get_all(f"{acct}/campaigns",
                           {"fields": "id,name,effective_status,created_time,daily_budget", "limit": "300"})

        rows = []
        for c in camps:
            cid, name, st = c["id"], c.get("name", ""), c.get("effective_status", "")
            key = C.norm(name)
            b = bycamp.get(key, {})
            if b:
                matched_keys.add(key)
            b_life, b_30 = b.get("life", 0), b.get("30d", 0)
            sp_life = float((life.get(cid) or {}).get("spend", 0) or 0)
            r30 = d30.get(cid) or {}
            sp_30 = float(r30.get("spend", 0) or 0)
            reg30 = regs(r30.get("actions"))
            cpa_life = C.cpa(sp_life, b_life)
            cpa_30 = C.cpa(sp_30, b_30)
            cpl30 = (sp_30 / reg30) if reg30 else None
            budget = c.get("daily_budget")
            bud = f"RM{int(budget)/100:.0f}" if budget else "—"
            age = None
            ct = c.get("created_time", "")[:10]
            try:
                age = (today - dt.date.fromisoformat(ct)).days
            except (ValueError, TypeError):
                pass
            rec = rec_for(st, sp_life, b_life, cpa_life, age)
            rows.append((b_life, st, name, sp_life, cpa_life, sp_30, reg30, cpl30, b_30, cpa_30, bud, age, rec))

        rows.sort(key=lambda x: (-x[0], -x[3]))
        print("=" * 100)
        print(f"{label}  {acct}   (sorted by lifetime buyers)")
        print("=" * 100)
        tot_sp = sum(r[3] for r in rows)
        tot_b = sum(r[0] for r in rows)
        for b_life, st, name, sp_life, cpa_life, sp_30, reg30, cpl30, b_30, cpa_30, bud, age, rec in rows:
            print(f"{rec:20} [{st[:6]:6}] {name[:38]:38} bud {bud:>6}/d age{str(age or '?'):>3}d")
            print(f"{'':20}   life: RM{sp_life:>7.0f} / {b_life:>3} buyers = CPA {fmt(cpa_life):>7}"
                  f"   | 30d: RM{sp_30:>6.0f} / {reg30:>3} reg (CPL {fmt(cpl30):>6}) / {b_30} buy (CPA {fmt(cpa_30)})")
        print(f"  ── {label} totals: lifetime spend RM{tot_sp:,.0f} · {tot_b} buyers · "
              f"blended CPA {fmt(C.cpa(tot_sp, tot_b))}\n")

    unmatched = [(k, v.get("life", 0)) for k, v in bycamp.items() if k not in matched_keys]
    unmatched.sort(key=lambda x: -x[1])
    if unmatched:
        print("=" * 100)
        print("SHEET utm_campaign values with buyers but NO live campaign match "
              "(renamed/deleted/other acct):")
        for k, n in unmatched[:20]:
            print(f"  {n:>3}  {k[:80]}")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
