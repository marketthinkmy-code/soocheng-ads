# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-17「看现在开的广告，按最新 Paid Student List 算每个
广告的 CPA，哪个需要开/scale/关，以 CPA 为准」.

  Per ACTIVE registration-optimized ad (MY + SG): 60d spend, 60d strict sales
  (campaign+ad UTM join), CPA, verdict vs owner tiers (720/960/1200,
  min_spend RM1,000). Creative-level rollup fills attribution gaps (creative_key
  pools 🌟/HOOK：/重拍：/拼接： variants). Plus: creatives WITH 60d sales but NO
  active instance anywhere = reopen candidates (owner decides — his rule).
  Prints dates/UTM/RM only, no student PII."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings
from adbot.commands import graph_client

TIERS = (720.0, 960.0, 1200.0)
MIN_SPEND = 1000.0


def verdict(sp, n):
    if n == 0:
        return "❌ 关候选（花满无单）" if sp >= MIN_SPEND else f"⏳ 数据未满（0 单 / RM{sp:.0f}）"
    c = sp / n
    if sp < MIN_SPEND:
        return f"⏳ 数据未满但已有 {n:.0f} 单"
    if c <= TIERS[0]:
        return "🚀 SCALE 候选"
    if c <= TIERS[1]:
        return "✓ keep"
    if c <= TIERS[2]:
        return "⚠️ watch（960-1200）"
    return "❌ 关候选（>1200）"


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s_sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d60 = today - dt.timedelta(days=60)
    rng60 = {"since": d60.isoformat(), "until": today.isoformat()}
    rng7 = {"since": (today - dt.timedelta(days=7)).isoformat(), "until": today.isoformat()}

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    recent = [x for x in sales if x.date and x.date >= d60]
    strict, by_creative, last_sale = {}, {}, {}
    for x in recent:
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        strict[k] = strict.get(k, 0) + 1
        ck = cpa.creative_key(x.ad)
        by_creative[ck] = by_creative.get(ck, 0) + 1
        if ck not in last_sale or x.date > last_sale[ck]:
            last_sale[ck] = x.date
    print(f"Paid Student List 近 60 天（{d60} 起）成交 {len(recent)} 单\n")

    active_creatives = set()
    for label, st in (("MY", s_my), ("SG", s_sg)):
        g = graph_client(st)
        ads = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "id,name,effective_status,campaign{name},"
                       "adset{promoted_object}",
             "limit": "500"})
        time.sleep(1.2)
        sp60 = {r.get("ad_id"): float(r.get("spend") or 0)
                for r in g.account_insights(st.meta.account_path, level="ad",
                                            fields="ad_id,spend", time_range=rng60)}
        time.sleep(1.2)
        sp7 = {r.get("ad_id"): float(r.get("spend") or 0)
               for r in g.account_insights(st.meta.account_path, level="ad",
                                           fields="ad_id,spend", time_range=rng7)}
        time.sleep(1.2)

        rows = []
        for a in ads:
            if a.get("effective_status") != "ACTIVE":
                continue
            ev = ((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type")
            if (ev or "").upper() != "COMPLETE_REGISTRATION":
                continue
            name = a.get("name") or a["id"]
            camp = (a.get("campaign") or {}).get("name") or "?"
            active_creatives.add(cpa.creative_key(name))
            sp = sp60.get(a["id"], 0.0)
            n = strict.get((_mkey(camp), cpa.norm(name)), 0)
            rows.append((sp, sp7.get(a["id"], 0.0), name, camp, n))
        rows.sort(reverse=True)
        print(f"═══ [{label}] 现在开着的（{len(rows)} 支，按 60 天花费排）═══")
        for sp, s7, name, camp, n in rows:
            c = f"RM{sp / n:.0f}" if n else "∞"
            ck = cpa.creative_key(name)
            pool = by_creative.get(ck, 0)
            extra = f" ·同素材全账户 {pool} 单" if pool > n else ""
            print(f"  {verdict(sp, n):<24} «{name[:34]}» @ «{camp[:30]}»")
            print(f"      60天 RM{sp:,.0f} / {n} 单 / CPA {c} · 近7天 RM{s7:.0f}{extra}")
        print()

    dead = [(ck, n, last_sale.get(ck)) for ck, n in by_creative.items()
            if ck not in active_creatives]
    dead.sort(key=lambda x: -x[1])
    print("═══ 有 60 天成交、但现在全账户没有活跃位（开回候选，等 owner 点名）═══")
    if not dead:
        print("  （没有）")
    for ck, n, d in dead:
        print(f"  «{ck[:40]}»  {n} 单 · 最后成交 {d}")
    print("\nCPA PER-AD DONE (read-only)")


if __name__ == "__main__":
    main()
