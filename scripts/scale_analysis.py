"""Scale analysis (read-only). Cross-reference the Paid Student List (paid conversions)
against CURRENTLY-ACTIVE ads on both accounts —
  MY  act_759339046918885
  SG  act_893025326577600
— to see which running creatives actually convert paid students, and which are worth scaling.

Attribution: a sale row's UTM ad name (utm_content = {{ad.name}}) matched to the live ad's
name, via the same normaliser the production CPA monitor uses (adbot.cpa.norm). Spend/regs
are the currently-active instances' LIFETIME numbers, so the rough CPA is optimistic (it omits
spend from paused/other-account instances of the same creative) — read it with CPL alongside.
No writes.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
PRICE = 2399.0
ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]
TOKEN = result_action_type("COMPLETE_REGISTRATION")


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT

    # ── sales ────────────────────────────────────────────────────────────────
    values = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, cols, _hdr = cpa.parse_sales(values, PRICE)
    dated = [x for x in sales if x.date]
    dmin = min((x.date for x in dated), default=None)
    dmax = max((x.date for x in dated), default=None)
    n14 = sum(1 for x in dated if x.date > today - dt.timedelta(days=14))
    n7 = sum(1 for x in dated if x.date > today - dt.timedelta(days=7))
    print(f"SHEET rows={len(values)}  parsed_sales={len(sales)}  dated={len(dated)}  "
          f"range {dmin}..{dmax}  last14d={n14}  last7d={n7}  cols={cols}")
    print("\n-- 20 most-recent dated sales (normalised UTM: campaign | ad) --")
    for x in sorted(dated, key=lambda z: z.date, reverse=True)[:20]:
        print(f"  {x.date}  «{x.campaign[:30]}» | «{x.ad[:40]}»")

    life = defaultdict(int); w30 = defaultdict(int); w14 = defaultdict(int)
    for x in sales:
        if not x.ad:
            continue
        life[x.ad] += 1
        if x.date and x.date > today - dt.timedelta(days=30): w30[x.ad] += 1
        if x.date and x.date > today - dt.timedelta(days=14): w14[x.ad] += 1

    # ── active ads (lifetime spend + registrations), both accounts, by creative ──
    agg = defaultdict(lambda: {"spend": 0.0, "regs": 0.0, "insts": 0,
                               "accts": set(), "camps": set()})
    active_names = set()
    for label, acct in ACCTS:
        ins = {r.get("ad_id"): r for r in g.account_insights(
            acct, level="ad", fields="ad_id,spend,actions", date_preset="maximum")}
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "id,name,effective_status,campaign{name}", "limit": "600"})
        n_active = 0
        for a in ads:
            if a.get("effective_status") != "ACTIVE":
                continue
            n_active += 1
            nm = cpa.norm(a.get("name", ""))
            active_names.add(nm)
            r = ins.get(a["id"]) or {}
            try:
                sp = float(r.get("spend") or 0)
            except (TypeError, ValueError):
                sp = 0.0
            e = agg[nm]
            e["spend"] += sp
            e["regs"] += extract_results(r.get("actions"), TOKEN)
            e["insts"] += 1
            e["accts"].add(label)
            e["camps"].add((a.get("campaign") or {}).get("name", ""))
        print(f"\n[{label}] {acct}: {n_active} active ads")

    # ── View A: active creatives ranked by paid sales ────────────────────────
    print("\n" + "=" * 98)
    print("ACTIVE creatives ranked by PAID sales   (sales life/30d/14d · spend · roughCPA · reg · CPL)")
    print("=" * 98)
    rows = []
    for nm, e in agg.items():
        sl = life.get(nm, 0)
        cpa_v = (e["spend"] / sl) if sl > 0 else None
        cpl_v = (e["spend"] / e["regs"]) if e["regs"] > 0 else None
        rows.append((sl, w30.get(nm, 0), w14.get(nm, 0), e["spend"], cpa_v,
                     e["regs"], cpl_v, sorted(e["accts"]), e["insts"], nm))
    rows.sort(key=lambda r: (-r[0], -r[1], r[4] if r[4] is not None else 9e9))
    for sl, s30, s14, sp, cpa_v, regs, cpl_v, accts, insts, nm in rows:
        cpa_s = f"{cpa_v:6.0f}" if cpa_v is not None else "   -  "
        cpl_s = f"{cpl_v:5.1f}" if cpl_v is not None else "  -  "
        print(f"  {sl:3d}/{s30:2d}/{s14:2d}  RM{sp:6.0f}  CPA{cpa_s}  reg{regs:4.0f}  CPL{cpl_s}  "
              f"{'+'.join(accts):5} x{insts}  {nm[:42]}")

    # ── converting creatives NOT currently active (relaunch candidates) ──────
    print("\n-- creatives with 30d paid sales but NOT currently active (relaunch/scale-back-in?) --")
    for nm, c in sorted(w30.items(), key=lambda kv: -kv[1])[:20]:
        if nm not in active_names:
            print(f"  {c:3d} sales(30d)  {nm[:60]}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
