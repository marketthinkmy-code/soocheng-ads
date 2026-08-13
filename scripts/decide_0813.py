# -*- coding: utf-8 -*-
"""READ-ONLY 8/13 decision pull: fresh sales (since 8/8) from the Paid Student List
joined against live ad performance on both accounts, so the owner gets a
scale / open / close recommendation.

Prints:
  A. sale receipts since 8/8 (date · amount · campaign · adset · ad)
  B. per account: every campaign with 3-day spend — campaign CPL + per-ad rows
     (3d spend/regs/CPL · yesterday spend · 60d strict sales · 60d CPA), 💰 marks
     ads matched to a recent sale (strict) / 💰? name-only match
  C. PAUSED campaigns whose ads match a recent-sale creative (re-open candidates)
"""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

PACE = 1.0
TODAY = "2026-08-13"
W_YDAY = {"since": "2026-08-12", "until": TODAY}
W_3D = {"since": "2026-08-10", "until": TODAY}
W_60D = {"since": "2026-06-14", "until": TODAY}
RECENT = dt.date(2026, 8, 8)
CUT60 = dt.date(2026, 6, 14)

ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))


def fmt_cpl(spend: float, regs: float) -> str:
    if regs:
        return f"{spend / regs:.1f}"
    return "∞" if spend else "-"


def pull(g, acct, token, win, with_actions=True):
    fields = "ad_id,ad_name,campaign_name,spend" + (",actions" if with_actions else "")
    out = {}
    for r in g.account_insights(acct, level="ad", fields=fields, time_range=win):
        out[r.get("ad_id")] = {
            "name": r.get("ad_name") or "?", "camp": r.get("campaign_name") or "?",
            "spend": float(r.get("spend") or 0),
            "regs": extract_results(r.get("actions"), token) if with_actions else 0.0}
    return out


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    from adbot.clients.sheets import SheetsClient
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    recent = [s for s in sales if s.date and s.date >= RECENT]
    strict60: dict = {}
    name60: dict = {}
    for s in sales:
        if s.date and s.date > CUT60:
            strict60[(s.campaign, s.ad)] = strict60.get((s.campaign, s.ad), 0) + 1
            name60[s.ad] = name60.get(s.ad, 0) + 1
    r_strict = {(s.campaign, s.ad) for s in recent}
    r_names = {s.ad for s in recent}

    print(f"A. SALE RECEIPTS since {RECENT} ({len(recent)} 单):")
    for s in sorted(recent, key=lambda x: str(x.date)):
        print(f"  {s.date}  RM{s.amount:.0f}  [{s.campaign[:52]}] / [{s.adset[:32]}]  «{s.ad[:46]}»")
    print()

    for label, cfg in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══════ [{label}] {acct} ═══════")
        ins3 = pull(g, acct, token, W_3D); time.sleep(PACE)
        insy = pull(g, acct, token, W_YDAY); time.sleep(PACE)
        ins60 = pull(g, acct, token, W_60D, with_actions=False); time.sleep(PACE)
        camps = {cpa.norm(c.get("name", "")): c for c in g.list_campaigns(acct)}
        time.sleep(PACE)

        by_camp: dict = {}
        for aid, r in ins3.items():
            by_camp.setdefault(r["camp"], []).append((aid, r))

        print("B. campaigns with 3d spend (8/10→8/13):")
        for camp_name, rows in sorted(by_camp.items(),
                                      key=lambda kv: -sum(r["spend"] for _a, r in kv[1])):
            spend = sum(r["spend"] for _a, r in rows)
            regs = sum(r["regs"] for _a, r in rows)
            if spend < 1:
                continue
            st = (camps.get(cpa.norm(camp_name)) or {}).get("effective_status", "?")
            ck = cpa.norm(camp_name)
            print(f"  [{st}] {camp_name}  · 3d spend {spend:.0f} regs {regs:.0f} CPL {fmt_cpl(spend, regs)}")
            for aid, r in sorted(rows, key=lambda x: -x[1]["spend"]):
                ak = cpa.norm(r["name"])
                n60 = strict60.get((ck, ak), 0)
                sp60 = (ins60.get(aid) or {}).get("spend", 0.0)
                cpa60 = f"{sp60 / n60:.0f}" if n60 else ("∞" if sp60 else "-")
                flag = " 💰NEW" if (ck, ak) in r_strict else (" 💰?name" if ak in r_names else "")
                y = insy.get(aid) or {"spend": 0, "regs": 0}
                print(f"      «{r['name'][:42]}»  3d {r['spend']:.0f}/{r['regs']:.0f}reg"
                      f" CPL {fmt_cpl(r['spend'], r['regs'])} · yday {y['spend']:.0f}/{y['regs']:.0f}"
                      f" · 60d sales {n60} CPA {cpa60}{flag}")
        print()

        hits = []
        for ck_norm, c in camps.items():
            if c.get("effective_status") == "ACTIVE":
                continue
            try:
                ads = g._get_all(f"{c['id']}/ads", {"fields": "id,name,effective_status", "limit": "50"})
            except Exception:  # noqa: BLE001
                continue
            time.sleep(0.4)
            match = [a for a in ads if cpa.norm(a.get("name") or "") in r_names]
            if match:
                hits.append((c.get("name"), [a.get("name") for a in match]))
        print("C. PAUSED campaigns containing a recent-sale creative:")
        for cn, names in hits:
            print(f"  [PAUSED] {cn}  →  {names}")
        if not hits:
            print("  (none)")
        print()

    print("DECISION PULL DONE (read-only)")


if __name__ == "__main__":
    main()
