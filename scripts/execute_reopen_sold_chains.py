# -*- coding: utf-8 -*-
"""Owner 2026-08-30 «就只開有成交的 campaign - ad set - ad 就好»:

For every Paid-Student-List sale in the last 14 days, reopen EXACTLY the
attributed chain — the campaign → ad set → ad named by the row's UTMs — and
nothing else. No sibling ads, no sibling ad sets, no shell campaigns.

Matching is exact on cpa.norm(campaign/adset/ad). A triple that can't be
resolved in the account is reported and skipped (never guessed).
Idempotent; dry-run unless CONFIRM=true."""
from __future__ import annotations

import collections
import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
SINCE = TODAY - dt.timedelta(days=14)
N = cpa.norm


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"只开成交链 — 成交窗口 {SINCE} → {TODAY} — {mode}\n")

    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    triples = {"MY": collections.Counter(), "SG": collections.Counter()}
    for s in sales:
        if not (s.date and s.date >= SINCE and s.ad and s.adset and s.campaign):
            continue
        acct = "SG" if s.campaign.startswith("[sg]") else "MY"
        triples[acct][(s.campaign, s.adset, s.ad)] += 1
    print(f"14d 可归因成交链: MY {len(triples['MY'])} 条 · SG {len(triples['SG'])} 条\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s2 = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s2)
        acct = s2.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,"
                       "campaign{id,name,status},adset{id,name,status}",
             "limit": "500"})
        time.sleep(1.2)
        idx = collections.defaultdict(list)
        for a in ads:
            c = a.get("campaign") or {}
            aset = a.get("adset") or {}
            idx[(N(c.get("name") or ""), N(aset.get("name") or ""),
                 N(a.get("name") or ""))].append(a)

        flipped_c, flipped_as = set(), set()
        for (camp_n, aset_n, ad_n), n_sales in triples[label].most_common():
            hits = idx.get((camp_n, aset_n, ad_n))
            if not hits:
                print(f"  ?? 找不到链 ({n_sales}单)  «{camp_n[:34]}» › «{aset_n[:26]}» › «{ad_n[:26]}» — skip")
                continue
            for a in hits:
                c = a.get("campaign") or {}
                aset = a.get("adset") or {}
                todo = []
                if c.get("status") != "ACTIVE" and c["id"] not in flipped_c:
                    todo.append(("campaign", c["id"]))
                if aset.get("status") != "ACTIVE" and aset["id"] not in flipped_as:
                    todo.append(("adset", aset["id"]))
                if a.get("status") != "ACTIVE":
                    todo.append(("ad", a["id"]))
                tag = (f"({n_sales}单)  «{(c.get('name') or '')[:34]}» › "
                       f"«{(aset.get('name') or '')[:24]}» › «{(a.get('name') or '')[:26]}»")
                if not todo:
                    print(f"  · 已在投 {tag}")
                    continue
                if not CONFIRM:
                    print(f"  ▶ would open [{'+'.join(t for t, _ in todo)}] {tag}")
                    continue
                try:
                    for level, oid in todo:
                        g.update_status(oid, "ACTIVE")
                        if level == "campaign":
                            flipped_c.add(oid)
                        if level == "adset":
                            flipped_as.add(oid)
                        time.sleep(PACE)
                    print(f"  ✅ opened [{'+'.join(t for t, _ in todo)}] {tag}")
                except Exception as e:
                    print(f"  ❌ {tag}: {str(e)[:110]} — continuing")
        print()

    print("SOLD-CHAIN REOPEN DONE." if CONFIRM else "DRY-RUN — review then confirm.")


if __name__ == "__main__":
    main()
