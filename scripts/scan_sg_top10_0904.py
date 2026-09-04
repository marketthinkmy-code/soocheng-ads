# -*- coding: utf-8 -*-
"""READ-ONLY: SG per-creative 60d CPL + CPA + sales record, for the owner's
Top-10 relaunch ranking (2026-09-04, 「根据 cpa，cpl，成交纪录」).

One insights call (level=ad, 60d, spend+actions) + one /ads call + the sheet.
Aggregates by normalised creative name across every instance:
  spend60, leads60 (configured conversion event), CPL60,
  new-account sales in 60d (sheet rows whose UTM campaign starts '[sg] stockbloom'),
  CPA60 = spend60 / new60, plus lifetime/30d/last-sale from the sheet.
Per-campaign spend split is printed for the sold creatives so best-chain CPA
can be eyeballed. Old-account (mtc) spend is invisible — CPL/CPA are
current-account only."""
from __future__ import annotations

import collections
import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import parse_metrics, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
SINCE = TODAY - dt.timedelta(days=60)
N = cpa.norm


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    token = result_action_type(s.meta.conversion_event)
    values = SheetsClient(s.secrets.google_sa_json).read_tab(
        s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)

    rec = collections.defaultdict(lambda: {
        "life": 0, "d60": 0, "d30": 0, "new60": 0, "last": None})
    for sale in sales:
        if not sale.ad or not sale.campaign.startswith("[sg]"):
            continue
        e = rec[sale.ad]
        e["life"] += 1
        if sale.date:
            e["last"] = max(e["last"], sale.date) if e["last"] else sale.date
            if sale.date >= SINCE:
                e["d60"] += 1
                if sale.campaign.startswith("[sg] stockbloom"):
                    e["new60"] += 1
            if sale.date >= TODAY - dt.timedelta(days=30):
                e["d30"] += 1

    g = graph_client(s)
    acct = s.meta.account_path
    ads = g._get_all(f"{acct}/ads",
                     {"fields": "id,name,campaign{name}", "limit": "500"})
    time.sleep(1.2)
    name_of, camp_of = {}, {}
    for a in ads:
        name_of[a["id"]] = N(a.get("name") or "")
        camp_of[a["id"]] = ((a.get("campaign") or {}).get("name") or "")[:34]

    per = collections.defaultdict(lambda: {"sp": 0.0, "ld": 0.0,
                                           "bycamp": collections.Counter()})
    for row in g.account_insights(
            acct, level="ad", fields="ad_id,spend,actions",
            time_range={"since": SINCE.isoformat(), "until": TODAY.isoformat()}):
        aid = row.get("ad_id")
        key = name_of.get(aid)
        if key is None:
            continue
        spend, leads = parse_metrics(row, token)
        per[key]["sp"] += spend
        per[key]["ld"] += leads
        per[key]["bycamp"][camp_of.get(aid, "?")] += round(spend)

    print(f"SG per-creative 60d CPL+CPA+成交 — {SINCE} → {TODAY}（read-only）\n")
    for ad_n, e in sorted(rec.items(), key=lambda kv: (-kv[1]["d60"], -kv[1]["life"])):
        p = per.get(ad_n)
        if not p and e["d60"] == 0:
            continue                      # stale old-account creative, no live data
        sp = p["sp"] if p else 0.0
        ld = p["ld"] if p else 0.0
        cpl = sp / ld if ld else None
        cpa60 = sp / e["new60"] if (sp and e["new60"]) else None
        print(f"● «{ad_n[:34]}»  成交 life {e['life']} · 60d {e['d60']} "
              f"(新账户 {e['new60']}) · 30d {e['d30']} · last {e['last']}")
        print(f"   60d spend RM{sp:.0f} · leads {ld:.0f} · "
              f"CPL {'RM%.0f' % cpl if cpl else '—'} · "
              f"CPA60 {'RM%.0f' % cpa60 if cpa60 else '—'}")
        if p:
            top = " / ".join(f"{c[:30]}:RM{v}" for c, v in p["bycamp"].most_common(3))
            print(f"   花在: {top}")
        print()
    print("TOP10 SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
