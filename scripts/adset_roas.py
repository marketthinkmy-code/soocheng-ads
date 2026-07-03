"""Read-only: rank ad sets by ROAS (Paid Student List revenue / Meta spend) + CPL.

Used to pick the single best-performing ad set to clone when scaling into a new campaign.
Revenue = sum of the sheet's purchase Amount attributed to the ad set (by UTM ad-set name);
ROAS = revenue / Meta spend; CPL = spend / registrations. Window: last 60 days. No writes.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import load_settings

WINDOW_DAYS = 60


def main() -> None:
    s = load_settings()
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cutoff = today - dt.timedelta(days=WINDOW_DAYS)
    ceiling = s.kpi.cpl_threshold_myr

    # revenue + paid sales per (campaign, ad set) from the sheet
    values = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _cols, _hdr = cpa.parse_sales(values, s.cpa.price_myr)
    rev, cnt = defaultdict(float), defaultdict(int)
    for sale in sales:
        if sale.date and sale.date > cutoff:
            k = (_mkey(sale.campaign), sale.adset)
            rev[k] += sale.amount
            cnt[k] += 1

    # spend + registrations per ad set from Meta
    token = result_action_type(s.meta.conversion_event)
    g = graph_client(s)
    insights = g.account_insights(
        s.meta.account_path, level="adset",
        fields="campaign_name,adset_name,adset_id,spend,actions",
        time_range={"since": cutoff.isoformat(), "until": today.isoformat()})

    data = []
    for r in insights:
        try:
            spend = float(r.get("spend") or 0)
        except (TypeError, ValueError):
            spend = 0.0
        if spend <= 0:
            continue
        k = (_mkey(r.get("campaign_name", "")), cpa.norm(r.get("adset_name", "")))
        regs = extract_results(r.get("actions"), token)
        revenue, n = rev.get(k, 0.0), cnt.get(k, 0)
        cpl = spend / regs if regs else math.inf
        roas = revenue / spend if spend else 0.0
        data.append({"campaign": r.get("campaign_name", ""), "adset": r.get("adset_name", ""),
                     "adset_id": r.get("adset_id", ""), "spend": spend, "regs": regs,
                     "cpl": cpl, "sales": n, "revenue": revenue, "roas": roas})

    data.sort(key=lambda d: -d["roas"])
    print(f"Ad-set ROAS · last {WINDOW_DAYS} days  (revenue = Paid Student List Amount; ceiling RM{ceiling:.0f})\n")
    hdr = f"{'campaign':26} {'ad set':18} {'spend':>8} {'reg':>4} {'CPL':>6} {'sale':>4} {'revenue':>9} {'ROAS':>5}"
    print(hdr)
    print("-" * len(hdr))
    for d in data[:25]:
        cpls = "∞" if d["cpl"] == math.inf else f"{d['cpl']:.0f}"
        print(f"{d['campaign'][:26]:26} {d['adset'][:18]:18} {d['spend']:8.0f} {d['regs']:4.0f} "
              f"{cpls:>6} {d['sales']:4} {d['revenue']:9.0f} {d['roas']:5.2f}")

    winners = [d for d in data if d["cpl"] <= ceiling and d["revenue"] > 0]
    winners.sort(key=lambda d: -d["roas"])
    print(f"\n🏆 Best ad set — CPL ≤ RM{ceiling:.0f} AND highest ROAS:")
    for d in winners[:5]:
        print(f"  ROAS {d['roas']:.2f} · CPL RM{d['cpl']:.0f} · {d['sales']} sales · "
              f"revenue RM{d['revenue']:,.0f} · spend RM{d['spend']:,.0f}  ·  "
              f"{d['campaign']} | {d['adset']}  (adset_id {d['adset_id']})")
    if not winners:
        print("  (no ad set with CPL under ceiling + attributed revenue)")

    # ── BY AD CONTENT NAME — bridges the account switch (a creative keeps its UTM Ads Name
    #    even when the campaign/account changes), so historical sales attribute to the creative.
    rev_ad, n30, n60, nlife, raw = (defaultdict(float), defaultdict(int),
                                    defaultdict(int), defaultdict(int), {})
    for sale in sales:
        a = sale.ad
        if not a:
            continue
        raw.setdefault(a, a)
        nlife[a] += 1
        rev_ad[a] += sale.amount
        if sale.date:
            age = (today - sale.date).days
            if age <= 60:
                n60[a] += 1
            if age <= 30:
                n30[a] += 1
    spend_ad = defaultdict(float)            # CURRENT-account lifetime spend per creative name
    for r in g.account_insights(s.meta.account_path, level="ad",
                                fields="ad_name,spend", date_preset="maximum"):
        try:
            spend_ad[cpa.norm(r.get("ad_name", ""))] += float(r.get("spend") or 0)
        except (TypeError, ValueError):
            pass
    status = {}                              # current status per creative name (ACTIVE wins)
    for camp in g.list_campaigns(s.meta.account_path):
        if camp.get("effective_status") not in ("ACTIVE", "PAUSED"):
            continue
        for ad in g.list_ads_under_campaign(camp["id"]):
            nm = cpa.norm(ad.get("name", ""))
            if status.get(nm) != "ACTIVE":
                status[nm] = ad.get("effective_status")

    rows = sorted(nlife, key=lambda a: (-nlife[a], -rev_ad[a]))
    print("\n\n=== BY AD CONTENT NAME (UTM Ads Name) — proven creatives + current status ===")
    print("(revenue = all paid sales attributed to this creative name, ANY account; "
          "newAcct$ = spend on the CURRENT account only)\n")
    hdr = f"{'ad content name':40} {'30d':>3} {'60d':>3} {'life':>4} {'revenue':>9} {'newAcct$':>9}  status"
    print(hdr)
    print("-" * len(hdr))
    for a in rows[:45]:
        sp = spend_ad.get(a)
        stt = status.get(a, "OFF (not on acct)")
        sps = f"RM{sp:.0f}" if sp else "—"
        flag = "  🟢 proven & OFF" if (nlife[a] >= 2 and stt != "ACTIVE") else ""
        print(f"{raw.get(a, a)[:40]:40} {n30[a]:>3} {n60[a]:>3} {nlife[a]:>4} "
              f"RM{rev_ad[a]:>7.0f} {sps:>9}  {stt}{flag}")

    # ── TOP ADS BY PURCHASE COUNT (Paid Student List) + full row accounting ──
    from collections import Counter
    sc = SheetsClient(s.secrets.google_sa_json)
    try:
        meta = sc._svc.spreadsheets().get(spreadsheetId=s.cpa.spreadsheet_id).execute()
        tabs = [sh["properties"]["title"] for sh in meta.get("sheets", [])]
    except Exception as exc:                                       # noqa: BLE001
        tabs = []; print("tab-list failed:", exc)
    print("\n\n=== SHEET TABS ===", tabs)

    # purchases: `values` was read from the Paid Student List tab at the top of main()
    pnorm, praw = Counter(), {}
    for sale in sales:
        if sale.ad:
            pnorm[sale.ad] += 1; praw.setdefault(sale.ad, sale.ad)
    total_rows = max(0, len(values) - 1)
    with_ad = sum(pnorm.values())
    print(f"PURCHASES accounting: {total_rows} data rows | {with_ad} attributable to an ad "
          f"({len(pnorm)} distinct ads) | {total_rows - with_ad} with no ad-UTM (organic/blank)")

    reg_tab = next((t for t in tabs if "regist" in t.lower()), None)
    if reg_tab:
        try:
            rvals = sc.read_tab(s.cpa.spreadsheet_id, reg_tab)
            rsales, _c, _h = cpa.parse_sales(rvals, 0.0)
            with_ad_r = sum(1 for r in rsales if r.ad)
            print(f"REGISTER accounting ('{reg_tab}'): {max(0,len(rvals)-1)} data rows | "
                  f"{with_ad_r} attributable to an ad | rest = no ad-UTM (organic/blank)")
        except Exception as exc:                                  # noqa: BLE001
            print("register read failed:", exc)

    print("\n=== TOP 10 ADS BY PURCHASE COUNT (Paid Student List, lifetime) ===")
    print(f"{'#':>2}  {'buys':>4}  ad content name")
    for i, (ad, npur) in enumerate(sorted(pnorm.items(), key=lambda x: (-x[1], x[0]))[:10], 1):
        print(f"{i:>2}  {npur:>4}  {praw.get(ad, ad)}")


if __name__ == "__main__":
    main()
