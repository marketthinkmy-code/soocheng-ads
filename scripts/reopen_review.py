# -*- coding: utf-8 -*-
"""Reopen review: latest Paid Student List sales -> per-ad CPL / CPA / ROAS + reopen list.

Owner directive 2026-07-30: judge ads by real purchases (CPA/ROAS), never kill or keep
dead an ad just for a high CPL. The monitor never un-pauses by design, so ads paused
before their registrations converted stay dark even when the sheet now shows sales.
This read-only report finds them: for BOTH accounts (MY + SG) it joins ad-level Meta
spend (60d + lifetime) to sheet sales at the (campaign, ad) grain the monitor itself
uses, then lists every non-delivering ad whose real-sales CPA clears the hard stop.

Run via adbot-ops (read-only; `confirm` is ignored — nothing here writes).
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from pathlib import Path

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

ACCOUNTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))
NOT_DELIVERING = {"PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"}
BANNED_SUBSTR = ("炒过那么多",)  # owner 2026-07-30 ban = video 12：炒过那么多，累而且不稳定 ONLY
                               # (video 12：不选 forex 不选黄金 is a different creative — a proven angle)


def _sheet_aggregates(sales, today):
    """(campaign, ad) -> {n60, rev60, nlife, revlife} from parsed sheet rows."""
    cut60 = today - dt.timedelta(days=60)
    agg = defaultdict(lambda: {"n60": 0, "rev60": 0.0, "nlife": 0, "revlife": 0.0})
    for s in sales:
        key = (s.campaign, s.ad)
        agg[key]["nlife"] += 1
        agg[key]["revlife"] += s.amount
        if s.date and s.date > cut60:
            agg[key]["n60"] += 1
            agg[key]["rev60"] += s.amount
    return agg


def _insights(g, acct, token, *, date_preset=None, time_range=None):
    """(campaign, ad) -> {spend, results, campaign_name, ad_name} at the sales-join grain."""
    rows = g.account_insights(acct, level="ad", fields="ad_id,ad_name,adset_name,campaign_name,spend,actions",
                              date_preset=date_preset, time_range=time_range)
    out = defaultdict(lambda: {"spend": 0.0, "results": 0.0, "camp": "", "ad": ""})
    for r in rows:
        key = (cpa.norm(r.get("campaign_name", "")), cpa.norm(r.get("ad_name", "")))
        try:
            out[key]["spend"] += float(r.get("spend", 0) or 0)
        except (TypeError, ValueError):
            pass
        out[key]["results"] += extract_results(r.get("actions"), token)
        out[key]["camp"], out[key]["ad"] = r.get("campaign_name", ""), r.get("ad_name", "")
    return out


def _statuses(g, acct):
    """(campaign, ad) -> {statuses: set, ids: [(ad_id, status)]} for every ad on the account."""
    ads = g._get_all(f"{acct}/ads", {"fields": "id,name,effective_status,campaign{name}", "limit": 200})
    out = defaultdict(lambda: {"statuses": set(), "ids": []})
    for a in ads:
        key = (cpa.norm((a.get("campaign") or {}).get("name", "")), cpa.norm(a.get("name", "")))
        st = a.get("effective_status", "?")
        out[key]["statuses"].add(st)
        out[key]["ids"].append((a.get("id", ""), st))
    return out


def _fmt_cpa(c):
    if c is None:
        return "—"
    return "∞" if c == math.inf else f"{c:,.0f}"


def main() -> None:
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    base = load_settings(REPO_ROOT / "config" / ACCOUNTS[0][1])
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _cols, _hdr = cpa.parse_sales(values, base.cpa.price_myr)
    dated = [s for s in sales if s.date]
    agg = _sheet_aggregates(sales, today)
    print(f"Reopen review — today MYT={today} · sheet rows parsed={len(sales)} "
          f"(dated {len(dated)}, latest {max((s.date for s in dated), default='—')}) · "
          f"tiers: healthy≤{base.cpa.healthy_max_myr:.0f} / hard-stop {base.cpa.hard_stop_myr:.0f}")
    print("ROAS below is FRONTEND-only (sheet amounts; BE 陪跑 revenue not included).\n")

    matched_keys = set()
    for label, cfg in ACCOUNTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct, token = s.meta.account_path, result_action_type(s.meta.conversion_event)
        t60 = {"since": (today - dt.timedelta(days=60)).isoformat(), "until": today.isoformat()}
        ins60 = _insights(g, acct, token, time_range=t60)
        inslife = _insights(g, acct, token, date_preset="maximum")
        stat = _statuses(g, acct)

        keys = set(ins60) | set(inslife)
        rows = []
        for k in keys:
            sh = agg.get(k)
            if sh:
                matched_keys.add(k)
            sp60, rg60 = ins60[k]["spend"], ins60[k]["results"]
            splife, rglife = inslife[k]["spend"], inslife[k]["results"]
            n60 = sh["n60"] if sh else 0
            nlife = sh["nlife"] if sh else 0
            rows.append({
                "camp": inslife[k]["camp"] or ins60[k]["camp"] or k[0],
                "ad": inslife[k]["ad"] or ins60[k]["ad"] or k[1],
                "key": k,
                "statuses": stat.get(k, {}).get("statuses", set()),
                "ids": stat.get(k, {}).get("ids", []),
                "sp60": sp60, "rg60": rg60,
                "cpl60": (sp60 / rg60) if rg60 else (math.inf if sp60 > 0 else None),
                "n60": n60, "cpa60": cpa.cpa(sp60, n60),
                "rev60": sh["rev60"] if sh else 0.0,
                "roas60": (sh["rev60"] / sp60) if sh and sp60 > 0 else None,
                "splife": splife, "rglife": rglife,
                "nlife": nlife, "cpalife": cpa.cpa(splife, nlife),
                "revlife": sh["revlife"] if sh else 0.0,
                "roaslife": (sh["revlife"] / splife) if sh and splife > 0 else None,
            })

        tot_sp60 = sum(r["sp60"] for r in rows)
        tot_n60 = sum(r["n60"] for r in rows)
        tot_rev60 = sum(r["rev60"] for r in rows)
        print(f"═══ [{label}] {acct} — 60d spend RM{tot_sp60:,.0f} · sheet sales {tot_n60} · "
              f"blended CPA RM{_fmt_cpa(cpa.cpa(tot_sp60, tot_n60))} · "
              f"FE ROAS {tot_rev60 / tot_sp60 if tot_sp60 else 0:.2f}x ═══")

        hdr = (f"{'ad (campaign)':58} | {'status':14} | {'60d spend':>9} | {'CPL':>5} | "
               f"{'sale':>4} | {'CPA':>6} | {'ROAS':>5} | {'life sale/CPA/ROAS':>19}")
        print(hdr)
        print("-" * len(hdr))
        for r in sorted(rows, key=lambda x: -x["sp60"]):
            if r["sp60"] < 1 and r["nlife"] == 0:
                continue
            st = sorted(r["statuses"])
            stx = ("ACTIVE" if "ACTIVE" in st else "/".join(st) or "?")[:14]
            cpl = "—" if r["cpl60"] is None else ("∞" if r["cpl60"] == math.inf else f"{r['cpl60']:.0f}")
            roas = "—" if r["roas60"] is None else f"{r['roas60']:.1f}x"
            rl = "—" if r["roaslife"] is None else f"{r['roaslife']:.1f}x"
            life = f"{r['nlife']}/{_fmt_cpa(r['cpalife'])}/{rl}"
            name = f"{r['ad'][:34]} ({r['camp'][:20]})"
            print(f"{name:58} | {stx:14} | {r['sp60']:>9,.0f} | {cpl:>5} | "
                  f"{r['n60']:>4} | {_fmt_cpa(r['cpa60']):>6} | {roas:>5} | {life:>19}")

        reopen, proven_old, hardstop_live, banned = [], [], [], []
        for r in rows:
            st = r["statuses"]
            delivering = "ACTIVE" in st
            paused_like = bool(st & NOT_DELIVERING) and not delivering
            is_banned = any(b in r["ad"].casefold() for b in BANNED_SUBSTR)
            finite60 = r["cpa60"] is not None and r["cpa60"] != math.inf
            if paused_like and r["n60"] > 0 and finite60 and r["cpa60"] <= s.cpa.hard_stop_myr:
                (banned if is_banned else reopen).append(r)
            elif paused_like and r["n60"] == 0 and r["nlife"] > 0 and not is_banned:
                proven_old.append(r)
            if delivering and finite60 and r["cpa60"] > s.cpa.hard_stop_myr and r["sp60"] >= s.cpa.min_spend_myr:
                hardstop_live.append(r)

        print(f"\n🔓 [{label}] 建议重开 (paused, 60d 有成交, CPA ≤ hard-stop RM{s.cpa.hard_stop_myr:.0f}):")
        if not reopen:
            print("   （无）")
        for r in sorted(reopen, key=lambda x: (x["roas60"] or 0), reverse=True):
            star = " ⭐" if r["cpa60"] <= s.cpa.healthy_max_myr else ""
            ids = ", ".join(i for i, st in r["ids"] if st in NOT_DELIVERING) or "?"
            print(f"   {r['ad'][:40]:40} ({r['camp'][:24]}) — 60d {r['n60']} sale · "
                  f"CPA RM{_fmt_cpa(r['cpa60'])} · FE ROAS {r['roas60'] or 0:.1f}x · "
                  f"RM{r['rev60']:,.0f} rev{star}  [ad {ids}]")
        if banned:
            print(f"   ⛔ 有成交但 owner 禁跑，不列入: " + "; ".join(r["ad"][:30] for r in banned))
        if proven_old:
            print(f"   ℹ️  paused、60d 无成交但历史有过 ({len(proven_old)}): " +
                  "; ".join(f"{r['ad'][:26]}(life {r['nlife']})" for r in
                            sorted(proven_old, key=lambda x: -x['nlife'])[:6]))
        if hardstop_live:
            print(f"   ⚠️  仍在跑但 60d CPA 超 hard-stop: " +
                  "; ".join(f"{r['ad'][:26]}(RM{_fmt_cpa(r['cpa60'])})" for r in hardstop_live))
        print()

    cut60 = today - dt.timedelta(days=60)
    un = defaultdict(int)
    for s_ in sales:
        if s_.date and s_.date > cut60 and (s_.campaign, s_.ad) not in matched_keys:
            un[(s_.campaign or "(no utm)", s_.ad or "(no utm)")] += 1
    print(f"⚠️ 60d 成交中对不上这两个账户任何广告的 ({sum(un.values())} 单 — 旧账户 UTM / 无 UTM / 名字改过):")
    for (c, a), n in sorted(un.items(), key=lambda x: -x[1])[:10]:
        print(f"   {n:>2} × {a[:34]:34} ← {c[:40]}")


if __name__ == "__main__":
    main()
