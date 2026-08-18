# -*- coding: utf-8 -*-
"""READ-ONLY: top converting AD SETs per account from the Paid Student List.

Split by UTM campaign prefix: campaigns starting with "[sg]" are SG, the rest MY
(owner's rule 2026-08-18). Rank ad sets by sales in the last 30 days (tiebreak 60d),
then resolve each top ad set against the LIVE ad sets on that account and print its
exact detailed-targeting keywords (flexible_spec interests) for the new-fleet build.
"""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 18)
D30 = TODAY - dt.timedelta(days=30)
D60 = TODAY - dt.timedelta(days=60)
TOP_N = 5

ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    from adbot.clients.sheets import SheetsClient
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    per = {"MY": {}, "SG": {}}
    for s in sales:
        if not s.date or s.date <= D60 or not s.adset:
            continue
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        d = per[label].setdefault(s.adset, {"d30": 0, "d60": 0, "last": s.date})
        d["d60"] += 1
        if s.date > D30:
            d["d30"] += 1
        if s.date > d["last"]:
            d["last"] = s.date

    for label, cfg in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══════ [{label}] {acct} — sales by UTM ad set ═══════")
        ranked = sorted(per[label].items(), key=lambda kv: (-kv[1]["d30"], -kv[1]["d60"]))
        for name, d in ranked[:TOP_N]:
            print(f"  {d['d30']:2d} (30d) / {d['d60']:2d} (60d)  last={d['last']}  «{name[:60]}»")
        print()

        live = g._get_all(f"{acct}/adsets",
                          {"fields": "id,name,effective_status,campaign{name},targeting",
                           "limit": "500"})
        time.sleep(1)
        print(f"  ── live targeting of the top {min(3, len(ranked))} ──")
        for name, d in ranked[:3]:
            hits = [a for a in live if cpa.norm(a.get("name") or "") == name]
            if not hits:
                hits = [a for a in live if name in cpa.norm(a.get("name") or "")]
            if not hits:
                print(f"  ⚠️ «{name[:50]}»: no live ad set matched (renamed?)")
                continue
            a = hits[0]
            tgt = a.get("targeting") or {}
            print(f"  ● «{a.get('name')}»  [{a.get('effective_status')}]  "
                  f"campaign «{(a.get('campaign') or {}).get('name')}»  id={a['id']}")
            flex = tgt.get("flexible_spec") or []
            if not flex:
                print(f"      (no flexible_spec — broad / Advantage+)")
            for spec in flex:
                for kind, items in spec.items():
                    names = [f"{i.get('name')} ({i.get('id')})" for i in items]
                    print(f"      {kind}: {names}")
            geo = (tgt.get("geo_locations") or {}).get("countries")
            print(f"      geo={geo} age={tgt.get('age_min')}-{tgt.get('age_max')} "
                  f"advantage_audience={tgt.get('targeting_automation') or tgt.get('advantage_audience', '?')}")
        print()

    print("TOP-ADSET PULL DONE (read-only)")


if __name__ == "__main__":
    main()
