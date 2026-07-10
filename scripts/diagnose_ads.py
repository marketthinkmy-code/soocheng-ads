"""Read-only 3-in-1 diagnostic for STOCK BLOOM (no writes to Meta):

  TASK 1  which ad is getting more expensive — per-ad daily CPL trend, last 14d.
  TASK 2  rejected / with-issues ads — pull issues_info + creative to judge
          whether the block is the COPY (fixable → request review) or the VIDEO.
  TASK 3  Singapore candidates — current + past creatives, their angle/language,
          lifetime paid buyers, and a MY-locality flag (RM / 马来西亚 …) so we know
          which need localizing before they can run in SG.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

MY_TOKENS = ["RM", "令吉", "马来西亚", "大马", "Malaysia", "MYR", "ringgit"]


def _cpl(spend: float, regs: float) -> str:
    if spend <= 0:
        return "  ·  "
    if regs <= 0:
        return f"RM{spend:.0f}/0reg=∞"
    return f"RM{spend/regs:.0f}"


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 1 — per-ad DAILY CPL trend (last 14 days)
    # ══════════════════════════════════════════════════════════════════════════
    print("=" * 78)
    print("TASK 1 · WHICH AD IS GETTING MORE EXPENSIVE  (daily CPL, last 14d)")
    print("=" * 78)
    rows = g._get_all(f"{acct}/insights", {
        "level": "ad", "fields": "ad_id,ad_name,spend,actions",
        "time_increment": "1", "date_preset": "last_14d", "limit": "500"})
    daily = defaultdict(dict)      # name -> {date: (spend, regs)}
    tot = defaultdict(float)
    for r in rows:
        name = r.get("ad_name", "?")
        d = r.get("date_start")
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        daily[name][d] = (sp, rg)
        tot[name] += sp

    all_dates = sorted({d for n in daily for d in daily[n]})
    half = len(all_dates) // 2 or 1
    early_dates, late_dates = all_dates[:half], all_dates[half:]

    def window_cpl(name, dates):
        sp = sum(daily[name].get(d, (0, 0))[0] for d in dates)
        rg = sum(daily[name].get(d, (0, 0))[1] for d in dates)
        return sp, rg, (sp / rg if rg else float("inf") if sp else 0.0)

    big = [n for n in tot if tot[n] >= 30]           # only ads with real spend
    climbers = []
    for n in big:
        e_sp, e_rg, e_cpl = window_cpl(n, early_dates)
        l_sp, l_rg, l_cpl = window_cpl(n, late_dates)
        if e_cpl not in (0.0, float("inf")) and l_cpl not in (0.0, float("inf")):
            delta = l_cpl - e_cpl
        elif l_cpl == float("inf") and l_sp > 0:
            delta = 9e9                              # went from converting to zero-result
        else:
            delta = -9e9
        climbers.append((delta, n, e_cpl, l_cpl, e_sp, l_sp, e_rg, l_rg))
    climbers.sort(key=lambda x: -x[0])

    if early_dates and late_dates:
        print(f"\n(early half = {early_dates[0]}…{early_dates[-1]}, "
              f"late half = {late_dates[0]}…{late_dates[-1]})\n")
    print(f"{'ad name':42} {'earlyCPL':>9} {'lateCPL':>9} {'delta':>7} {'14dSpend':>9}")
    print("-" * 82)
    for delta, n, e_cpl, l_cpl, e_sp, l_sp, e_rg, l_rg in climbers:
        ec = "inf" if e_cpl == float("inf") else (f"{e_cpl:.0f}" if e_cpl else "-")
        lc = "inf" if l_cpl == float("inf") else (f"{l_cpl:.0f}" if l_cpl else "-")
        dd = "UP-BIG" if delta >= 9e8 else ("-" if delta <= -9e8 else f"{delta:+.0f}")
        print(f"{n[:42]:42} {ec:>9} {lc:>9} {dd:>7} {tot[n]:9.0f}")

    print("\n\n--- DAILY DETAIL for the top climbers (spend / reg / CPL per day) ---")
    for delta, n, *_ in climbers[:6]:
        print(f"\n> {n}   (14d spend RM{tot[n]:.0f})")
        for d in all_dates:
            sp, rg = daily[n].get(d, (0, 0))
            if sp > 0:
                print(f"    {d}  spend RM{sp:6.1f}  reg {rg:4.0f}  CPL {_cpl(sp, rg)}")

    print("\n\n--- ACCOUNT BLENDED daily CPL (all ads) ---")
    arows = g._get_all(f"{acct}/insights", {
        "level": "account", "fields": "spend,actions",
        "time_increment": "1", "date_preset": "last_14d"})
    for r in sorted(arows, key=lambda x: x.get("date_start", "")):
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        print(f"    {r.get('date_start')}  spend RM{sp:7.1f}  reg {rg:4.0f}  blendedCPL {_cpl(sp, rg)}")

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 2 — rejected / with-issues ads
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n" + "=" * 78)
    print("TASK 2 · REJECTED / WITH-ISSUES ADS  (copy problem vs video problem)")
    print("=" * 78)
    ads = g._get_all(f"{acct}/ads", {
        "fields": "name,effective_status,configured_status,issues_info,"
                  "campaign{name},creative{id,body,title,video_id,image_hash,"
                  "object_story_id,call_to_action_type}",
        "limit": "400"})
    bad = [a for a in ads if a.get("issues_info")
           or a.get("effective_status") in ("DISAPPROVED", "WITH_ISSUES", "PENDING_REVIEW")]
    print(f"\n{len(ads)} ads total · {len(bad)} rejected/with-issues/pending\n")
    for a in bad:
        cr = a.get("creative") or {}
        kind = "VIDEO" if cr.get("video_id") else ("IMAGE" if cr.get("image_hash") else "post/other")
        camp = ((a.get("campaign") or {}).get("name") or "?")
        print(f"\n# {a.get('name')}   [{a.get('effective_status')}]  ({kind})")
        print(f"    campaign: {camp}")
        for iss in a.get("issues_info") or []:
            print(f"    ISSUE level={iss.get('level')} code={iss.get('error_code')} "
                  f"type={iss.get('error_type')}")
            print(f"      summary: {iss.get('error_summary')}")
            if iss.get("error_message"):
                print(f"      detail : {iss.get('error_message')}")
        body = (cr.get("body") or "").replace("\n", " / ")
        if body:
            print(f"    COPY(body): {body[:600]}")
        if cr.get("title"):
            print(f"    headline  : {cr.get('title')}")

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 3 — Singapore candidates
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n" + "=" * 78)
    print("TASK 3 · SINGAPORE CANDIDATES  (proven creatives + language/locality flag)")
    print("=" * 78)

    buyers = defaultdict(int)
    try:
        values = SheetsClient(s.secrets.google_sa_json).read_tab(
            s.cpa.spreadsheet_id, s.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)
        for sale in sales:
            if sale.ad:
                buyers[cpa.norm(sale.ad)] += 1
    except Exception as exc:  # noqa: BLE001
        print("  (Paid Student List unavailable:", exc, ")")

    spend_life = defaultdict(float)
    for r in g.account_insights(acct, level="ad", fields="ad_name,spend", date_preset="maximum"):
        try:
            spend_life[cpa.norm(r.get("ad_name", ""))] += float(r.get("spend") or 0)
        except (TypeError, ValueError):
            pass

    seen = {}
    for camp in g.list_campaigns(acct):
        for ad in g.list_ads_under_campaign(camp["id"]):
            nm = ad.get("name", "")
            key = cpa.norm(nm)
            cr = ad.get("creative") or {}
            status = ad.get("effective_status")
            row = seen.get(key)
            if not row or status == "ACTIVE":
                seen[key] = {"name": nm, "status": status, "creative_id": cr.get("id"),
                             "buyers": buyers.get(key, 0), "life_spend": spend_life.get(key, 0.0)}

    print(f"\n{'creative name':46} {'buys':>4} {'status':>10} {'kind':>6}  MYlocal?")
    print("-" * 88)
    ranked = sorted(seen.values(), key=lambda r: (-r["buyers"], -r["life_spend"]))
    for r in ranked:
        cid = r.get("creative_id")
        kind, body = "?", ""
        if cid:
            try:
                c = g.get_object(cid, "body,title,video_id,image_hash")
                kind = "VIDEO" if c.get("video_id") else ("IMAGE" if c.get("image_hash") else "post")
                body = (c.get("body") or "") + " " + (c.get("title") or "")
            except Exception:  # noqa: BLE001
                pass
        my_hits = [t for t in MY_TOKENS if t.lower() in body.lower()]
        flag = ("MY:" + ",".join(my_hits)) if my_hits else "clean"
        print(f"{r['name'][:46]:46} {r['buyers']:>4} {r['status'][:10]:>10} {kind:>6}  {flag}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
