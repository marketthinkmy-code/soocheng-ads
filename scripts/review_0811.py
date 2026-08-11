# -*- coding: utf-8 -*-
"""8/11 复盘 data pull (READ-ONLY — no writes, CONFIRM ignored).

Answers, per account (MY + SG):
  1. Reopen week (8/4→8/11): the 8 reactivated ads — status now, spend/regs/CPL, sheet
     sales (strict campaign+ad join AND ad-name-only join, because of the rename bug).
  2. 14-day first judgement (7/28→8/11): BEER / DAY TRADING / TOP3 campaigns — per-ad
     spend/regs/CPL + sales.
  3. New builds (8/10→8/11): the 6 wave + 2 LAL + 2 BROAD MJ campaigns — statuses and any
     first spend.
  4. cpl_hold proof: config value + 你敢吗 ads' live status.
  5. 炒过那么多 receipts: every sheet sale since 7/28 for the focus creatives (date +
     campaign only — no buyer PII).
"""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

PACE = 1.0
TODAY = "2026-08-11"
W_REOPEN = {"since": "2026-08-04", "until": TODAY}
W_14D = {"since": "2026-07-28", "until": TODAY}
W_NEW = {"since": "2026-08-10", "until": TODAY}

GROUPS_14D = ("beer", "day trading", "top3")
GROUPS_NEW = ("omakase", "watches", "diving", "auto", "food drink", "purchase lal", "broad mj")

REOPENED = {
    "MY": [("120247585354180575", "你敢吗"),
           ("120247524817870575", "你没有本钱"),
           (None, "不选 forex")],          # id resolved by name (luxury campaign)
    "SG": [("120248197444110521", "freestyle 1"),
           ("120248220656790521", "盖电脑"),
           ("120248220645830521", "trading 早就不是这样了"),
           ("120248220653470521", "你没有本钱"),
           ("120248256492180521", "用我的方法")],
}
FOCUS_NAMES = ("炒过那么多", "你敢吗", "freestyle 1", "盖电脑", "你没有本钱",
               "trading 早就不是这样了", "用我的方法", "不选 forex")

ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))


def fmt_cpl(spend: float, regs: float) -> str:
    if regs:
        return f"{spend / regs:.2f}"
    return "∞" if spend else "-"


def pull(g, acct: str, token: str, win) -> dict:
    rows = g.account_insights(acct, level="ad",
                              fields="ad_id,ad_name,campaign_name,spend,actions",
                              time_range=win)
    out = {}
    for r in rows:
        spend = float(r.get("spend") or 0)
        regs = extract_results(r.get("actions"), token)
        out[r.get("ad_id")] = {"name": r.get("ad_name") or "?",
                               "camp": r.get("campaign_name") or "?",
                               "spend": spend, "regs": regs}
    return out


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    from adbot.clients.sheets import SheetsClient
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)
    today = dt.date(2026, 8, 11)

    def sheet_counts(since: dt.date):
        strict, by_name, amt_by_name = {}, {}, {}
        for s in sales:
            if not s.date or s.date < since:
                continue
            strict[(s.campaign, s.ad)] = strict.get((s.campaign, s.ad), 0) + 1
            by_name[s.ad] = by_name.get(s.ad, 0) + 1
            amt_by_name[s.ad] = amt_by_name.get(s.ad, 0) + s.amount
        return strict, by_name, amt_by_name

    s60_strict, s60_name, s60_amt = sheet_counts(today - dt.timedelta(days=60))
    s84_strict, s84_name, s84_amt = sheet_counts(dt.date(2026, 8, 4))
    s728_strict, s728_name, s728_amt = sheet_counts(dt.date(2026, 7, 28))
    total_84 = sum(s84_name.values())
    total_728 = sum(s728_name.values())
    print(f"SHEET: {len(sales)} rows · sales since 8/4 = {total_84} · since 7/28 = {total_728}"
          f" · 60d = {sum(s60_name.values())}\n")

    print("── focus-creative sale receipts since 7/28 (date · campaign · ad) ──")
    for s in sales:
        if not s.date or s.date < dt.date(2026, 7, 28):
            continue
        if any(cpa.norm(f) in s.ad for f in FOCUS_NAMES):
            print(f"  {s.date}  RM{s.amount:.0f}  [{s.campaign[:58]}]  «{s.ad[:48]}»")
    print()

    for label, cfg in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══════ [{label}] {acct} ═══════")
        print(f"  kpi.cpl_hold = {s.kpi.cpl_hold}")

        ins_reopen = pull(g, acct, token, W_REOPEN); time.sleep(PACE)
        ins_14d = pull(g, acct, token, W_14D); time.sleep(PACE)
        ins_new = pull(g, acct, token, W_NEW); time.sleep(PACE)

        camps = g.list_campaigns(acct); time.sleep(PACE)

        print(f"\n  ── 1) reopen ads · 8/4→8/11 ──")
        for ad_id, name_sub in REOPENED[label]:
            if ad_id is None:
                hits = [i for i, r in ins_reopen.items() if cpa.norm(name_sub) in cpa.norm(r["name"])]
                if not hits:
                    print(f"    «{name_sub}»: no delivery rows this window (spend 0)")
                    continue
                ad_id = hits[0]
            try:
                ad = g.get_object(ad_id, "name,effective_status,campaign{name}")
            except Exception as e:  # noqa: BLE001
                print(f"    «{name_sub}» {ad_id}: lookup failed {e}")
                continue
            time.sleep(PACE)
            nm, st = ad.get("name", "?"), ad.get("effective_status", "?")
            cn = (ad.get("campaign") or {}).get("name", "?")
            r = ins_reopen.get(ad_id, {"spend": 0.0, "regs": 0.0})
            key = (cpa.norm(cn), cpa.norm(nm))
            n_strict = s84_strict.get(key, 0)
            n_name = s84_name.get(cpa.norm(nm), 0)
            amt = s84_amt.get(cpa.norm(nm), 0.0)
            print(f"    [{st}] «{nm[:44]}» ({cn[:36]})")
            print(f"        spend {r['spend']:.2f} · regs {r['regs']:.0f} · CPL {fmt_cpl(r['spend'], r['regs'])}"
                  f" · sales strict={n_strict} name={n_name} (RM{amt:.0f})")

        print(f"\n  ── 2) BEER / DAY TRADING / TOP3 · 7/28→8/11 ──")
        for c in camps:
            cn = cpa.norm(c.get("name", ""))
            if not any(gname in cn for gname in GROUPS_14D):
                continue
            print(f"    [{c.get('effective_status')}] {c.get('name')}")
            camp_sales = sum(v for (ck, _ak), v in s728_strict.items() if ck == cn)
            rows = [(aid, r) for aid, r in ins_14d.items() if cpa.norm(r["camp"]) == cn]
            spend = sum(r["spend"] for _a, r in rows)
            regs = sum(r["regs"] for _a, r in rows)
            print(f"        campaign: spend {spend:.2f} · regs {regs:.0f} · CPL {fmt_cpl(spend, regs)}"
                  f" · strict-campaign sales={camp_sales}")
            for aid, r in sorted(rows, key=lambda x: -x[1]["spend"]):
                nk = cpa.norm(r["name"])
                print(f"        · «{r['name'][:44]}» spend {r['spend']:.2f} regs {r['regs']:.0f}"
                      f" CPL {fmt_cpl(r['spend'], r['regs'])} · name-sales 7/28+={s728_name.get(nk, 0)}")

        print(f"\n  ── 3) new builds status (8/10 waves + LAL + BROAD MJ) · spend 8/10→8/11 ──")
        for c in camps:
            cn = cpa.norm(c.get("name", ""))
            if not any(gname in cn for gname in GROUPS_NEW):
                continue
            rows = [(aid, r) for aid, r in ins_new.items() if cpa.norm(r["camp"]) == cn]
            spend = sum(r["spend"] for _a, r in rows)
            regs = sum(r["regs"] for _a, r in rows)
            ads = g.list_ads_under_campaign(c["id"]); time.sleep(PACE)
            n_active = sum(1 for a in ads if a.get("effective_status") == "ACTIVE")
            print(f"    [{c.get('effective_status')}] {c.get('name')} — {len(ads)} ads"
                  f" ({n_active} active) · spend {spend:.2f} · regs {regs:.0f}")

        print(f"\n  ── 4) 你敢吗 / 炒过那么多 live rows · 8/4→8/11 ──")
        for aid, r in sorted(ins_reopen.items(), key=lambda x: -x[1]["spend"]):
            if ("你敢吗" in r["name"]) or ("炒过那么多" in r["name"]):
                nk = cpa.norm(r["name"])
                print(f"    «{r['name'][:44]}» [{r['camp'][:40]}] spend {r['spend']:.2f}"
                      f" regs {r['regs']:.0f} CPL {fmt_cpl(r['spend'], r['regs'])}"
                      f" · name-sales 8/4+={s84_name.get(nk, 0)} (RM{s84_amt.get(nk, 0):.0f})")
        print()

    print("REVIEW PULL DONE (read-only)")


if __name__ == "__main__":
    main()
