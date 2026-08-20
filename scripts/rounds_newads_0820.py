# -*- coding: utf-8 -*-
"""READ-ONLY (owner 8/20 meeting list):
1. last-7-week «round» trend per account — spend / leads / CPL / sales / CPA / conv%
   (answers: when did CPL spike & which round did lead quality drop)
2. new-ad batches scoreboard — the 8/12 re-cut BROAD A/B/C, the BROAD MJ V-adds,
   and the AUG NEW fleet (launched 2026-08-20 00:00): per-ad spend/leads/CPL,
   sheet sales, and effective/review status."""
from __future__ import annotations

import datetime as dt
import re
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 20)
N = cpa.norm
NEW_BATCH = re.compile(r"(\| 1-1-3 [ABC]$)|(BROAD MJ)|(AUG NEW)", re.IGNORECASE)


def monday(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    weeks = [monday(TODAY) - dt.timedelta(weeks=i) for i in range(6, -1, -1)]

    sold_week = {"MY": {}, "SG": {}}
    sold_ca = {"MY": {}, "SG": {}}          # (norm campaign, norm ad) -> n
    for s in sales:
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        if s.date:
            wk = monday(s.date)
            sold_week[label][wk] = sold_week[label].get(wk, 0) + 1
        key = (N(s.campaign), N(s.ad or ""))
        sold_ca[label][key] = sold_ca[label].get(key, 0) + 1

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══ [{label}] {acct} ═══")
        try:
            print("  ▍逐周趋势 (spend / leads / CPL / 成交(按成交日) / CPA / 名单→成交%)")
            for wk in weeks:
                until = min(wk + dt.timedelta(days=6), TODAY)
                rows = g.account_insights(
                    acct, level="account", fields="spend,actions",
                    time_range={"since": wk.isoformat(), "until": until.isoformat()})
                sp = sum(float(r.get("spend") or 0) for r in rows)
                ld = sum(extract_results(r.get("actions"), token) for r in rows)
                so = sold_week[label].get(wk, 0)
                cpl = f"{sp/ld:5.1f}" if ld else "    -"
                cpa_ = f"{sp/so:5.0f}" if so else ("    ∞" if sp > 0 else "    -")
                conv = f"{so/ld*100:4.1f}%" if ld else "   - "
                mark = " ←本周(未完)" if wk == weeks[-1] else ""
                print(f"   {wk.isoformat()}  RM{sp:7.0f}  {ld:5.0f}  CPL {cpl}"
                      f"  sold {so:2d}  CPA {cpa_}  {conv}{mark}")
                time.sleep(1)

            print("\n  ▍新广告批次 (spend / leads / CPL / 成交 / 状态)")
            eff = {}
            for a in g._get_all(f"{acct}/ads",
                                {"fields": "id,effective_status,campaign{name}",
                                 "limit": "300"}):
                eff[a["id"]] = a.get("effective_status")
            time.sleep(2)
            rows = [r for r in g.account_insights(
                acct, level="ad",
                fields="ad_id,ad_name,campaign_name,spend,actions",
                date_preset="maximum") if NEW_BATCH.search(r.get("campaign_name") or "")]
            time.sleep(2)
            # ads with zero delivery have no insights row — list them from the ads edge
            seen_ids = {r.get("ad_id") for r in rows}
            for a in g._get_all(f"{acct}/ads",
                                {"fields": "id,name,effective_status,campaign{name}",
                                 "limit": "300"}):
                cn = (a.get("campaign") or {}).get("name") or ""
                if NEW_BATCH.search(cn) and a["id"] not in seen_ids:
                    rows.append({"ad_id": a["id"], "ad_name": a.get("name"),
                                 "campaign_name": cn, "spend": 0, "actions": []})
            time.sleep(1)

            by_camp = {}
            for r in rows:
                by_camp.setdefault(r.get("campaign_name") or "?", []).append(r)
            for cn in sorted(by_camp):
                print(f"   ◆ {cn}")
                for r in sorted(by_camp[cn], key=lambda x: -float(x.get("spend") or 0)):
                    sp = float(r.get("spend") or 0)
                    ld = extract_results(r.get("actions"), token)
                    cpl = f"{sp/ld:5.1f}" if ld else "    -"
                    so = sold_ca[label].get((N(cn), N(r.get("ad_name") or "")), 0)
                    st = eff.get(r.get("ad_id"), "?")
                    print(f"      RM{sp:6.0f}  {ld:4.0f}  CPL {cpl}  sold {so}"
                          f"  [{st}]  «{(r.get('ad_name') or '')[:36]}»")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()
    print("ROUNDS+NEWADS DONE (read-only)")


if __name__ == "__main__":
    main()
