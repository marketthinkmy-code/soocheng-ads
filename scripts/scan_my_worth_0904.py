# -*- coding: utf-8 -*-
"""READ-ONLY: which MY ads are worth switching ON? (owner 2026-09-04)

Joins every Paid-Student-List MY sale (campaign not starting [sg]) against the
CURRENT MY account's ad inventory by normalised ad name, with 60d + lifetime
spend per ad from insights. Prints, per selling ad name: sales windows, last
sale date, then each live instance's status chain and spend, plus a summary of
paused-but-proven candidates. Old-account (mtc - *) spend is invisible here, so
CPA shown is CURRENT-account spend / ALL MY sales of that name — a floor tag,
labelled accordingly."""
from __future__ import annotations

import collections
import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
N = cpa.norm


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(s.secrets.google_sa_json).read_tab(
        s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)

    stat = collections.defaultdict(lambda: {"14": 0, "30": 0, "60": 0, "life": 0,
                                            "last": None, "new_acct": 0})
    for sale in sales:
        if not sale.ad or sale.campaign.startswith("[sg]"):
            continue
        e = stat[sale.ad]
        e["life"] += 1
        if sale.campaign.startswith("stockbloom"):
            e["new_acct"] += 1
        if sale.date:
            e["last"] = max(e["last"], sale.date) if e["last"] else sale.date
            for w in (14, 30, 60):
                if sale.date > TODAY - dt.timedelta(days=w):
                    e[str(w)] += 1

    g = graph_client(s)
    acct = s.meta.account_path
    ads = g._get_all(
        f"{acct}/ads",
        {"fields": "id,name,status,effective_status,"
                   "campaign{name,status},adset{name,status}", "limit": "500"})
    time.sleep(1.2)
    sp60, splife = {}, {}
    for row in g.account_insights(acct, level="ad", fields="ad_id,spend",
                                  time_range={"since": (TODAY - dt.timedelta(days=60)).isoformat(),
                                              "until": TODAY.isoformat()}):
        sp60[row.get("ad_id")] = float(row.get("spend") or 0)
    time.sleep(1.2)
    for row in g.account_insights(acct, level="ad", fields="ad_id,spend",
                                  date_preset="maximum"):
        splife[row.get("ad_id")] = float(row.get("spend") or 0)

    by_name = collections.defaultdict(list)
    for a in ads:
        by_name[N(a.get("name") or "")].append(a)

    print(f"MY 值得开体检 — {TODAY}（read-only）· MY 成交 "
          f"{sum(e['life'] for e in stat.values())} 单 · {len(stat)} 个 ad 名\n")
    candidates = []
    for ad_n, e in sorted(stat.items(), key=lambda kv: (-kv[1]["60"], -kv[1]["life"])):
        insts = by_name.get(ad_n, [])
        live = [a for a in insts if a.get("effective_status") == "ACTIVE"]
        acct_spend = sum(splife.get(a["id"], 0) for a in insts)
        cpa_tag = (f" 现账户花费 RM{acct_spend:.0f}"
                   f"（÷{e['new_acct']}新账户单 = RM{acct_spend / e['new_acct']:.0f}/单）"
                   if insts and e["new_acct"] else
                   (f" 现账户花费 RM{acct_spend:.0f}（新账户 0 单）" if insts else ""))
        print(f"● {e['life']:>3}单 | 14d {e['14']} · 30d {e['30']} · 60d {e['60']} | "
              f"last {e['last']} | 现账户 instance {len(live)}/{len(insts)} 在投 | "
              f"«{ad_n[:34]}»{cpa_tag}")
        for a in insts:
            c, aset = a.get("campaign") or {}, a.get("adset") or {}
            est = a.get("effective_status")
            mark = "✅" if est == "ACTIVE" else "🔴"
            print(f"    {mark} [{est:>15}] own={a.get('status'):>6} "
                  f"camp={(c.get('status') or ''):>6}/{(aset.get('status') or ''):>6} "
                  f"60d RM{sp60.get(a['id'], 0):.0f} · life RM{splife.get(a['id'], 0):.0f} "
                  f"«{((c.get('name') or ''))[:40]}»")
            if est != "ACTIVE":
                candidates.append((e, a, c))
        print()

    print("══ 关着但有成交记录的现账户 instance（候选开）══")
    for e, a, c in sorted(candidates, key=lambda t: (-t[0]["60"], -t[0]["life"])):
        print(f"  ▸ {e['life']}单/60d {e['60']} last {e['last']}  "
              f"«{(a.get('name') or '')[:30]}» in «{(c.get('name') or '')[:42]}» "
              f"[{a.get('effective_status')}]")
    print("\nSCAN DONE (read-only)")


if __name__ == "__main__":
    main()
