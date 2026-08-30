# -*- coding: utf-8 -*-
"""READ-ONLY: which ads sold in the last 14 days (Paid Student List) and is any
of them currently switched off?

For every ad with >=1 sale since TODAY-14: list ALL its instances in the
matching account with ad/adset/campaign status. 🔴 = not delivering. Sellers
with ZERO active instances are the top-severity misclosures."""
from __future__ import annotations

import collections
import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
SINCE = TODAY - dt.timedelta(days=14)
N = cpa.norm


def main() -> None:
    print(f"14 天成交广告在投状态体检 — {SINCE} → {TODAY}（read-only）\n")
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    sellers = {"MY": collections.Counter(), "SG": collections.Counter()}
    latest = {}
    for s in sales:
        if not (s.date and s.date >= SINCE and s.ad):
            continue
        acct = "SG" if (s.campaign or "").startswith("[sg]") else "MY"
        key = N(s.ad)
        sellers[acct][key] += 1
        latest[(acct, key)] = max(latest.get((acct, key), s.date), s.date)

    n_total = sum(sum(c.values()) for c in sellers.values())
    print(f"14d 成交(有广告归因): {n_total} 单 · MY {sum(sellers['MY'].values())} · "
          f"SG {sum(sellers['SG'].values())}\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s2 = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s2)
        acct = s2.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,effective_status,"
                       "campaign{name,status},adset{name,status}", "limit": "500"})
        time.sleep(1.2)
        by_name = collections.defaultdict(list)
        for a in ads:
            by_name[N(a.get("name") or "")].append(a)

        dark, partial = [], []
        for key, n in sellers[label].most_common():
            insts = by_name.get(key, [])
            disp = insts[0].get("name") if insts else key
            live = [a for a in insts if a.get("effective_status") == "ACTIVE"]
            head = (f"● {n}单(最近{latest[(label, key)].strftime('%m/%d')})  "
                    f"«{(disp or '')[:34]}»  instance {len(live)}/{len(insts)} 在投")
            if not insts:
                print(f"  ?? {head} — 账户里找不到（organic/旧账户?）")
                continue
            print(("  ✅ " if live else "  🔴 ") + head)
            for a in insts:
                est = a.get("effective_status")
                if est == "ACTIVE":
                    continue
                c = a.get("campaign") or {}
                aset = a.get("adset") or {}
                who = ("campaign关" if c.get("status") != "ACTIVE"
                       else "adset关" if aset.get("status") != "ACTIVE"
                       else "ad关")
                print(f"       🔴 [{who}] «{(c.get('name') or '')[:40]}»")
            if not live:
                dark.append(disp)
            elif len(live) < len(insts):
                partial.append(disp)
        print()

    print("SELLER-14D SCAN DONE (read-only)")


if __name__ == "__main__":
    main()
