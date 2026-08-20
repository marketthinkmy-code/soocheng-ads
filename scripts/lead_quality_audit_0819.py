# -*- coding: utf-8 -*-
"""READ-ONLY lead-quality vs spend audit (owner 2026-08-19):

«compare 有成交的名单 vs 什么广告花得最多 — 是不是赚钱的广告没放钱？»

Per account ([sg] campaign-prefix split), join
  · Meta insights per ad (spend + registrations) over 14d / 30d / 60d / lifetime
  · Paid Student List buyers per ad (14d / 30d / 60d / lifetime, by sale date)
aggregated by normalised ad name (same join the ladder builds use), then print:
  1. account window totals + how much 30d spend goes to ads that actually sell
  2. top spenders 30d with their buyer counts (🔴 = burning, no sales)
  3. top sellers with their CURRENT funding (💤 = proven seller, no spend now)
  4. the last-14d sale-by-sale detail (which ad + campaign closed each deal)
"""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 19)
WINDOWS = (("d14", 14), ("d30", 30), ("d60", 60))
ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))


def fmt_cpa(spend: float, n: int) -> str:
    if n:
        return f"{spend / n:5.0f}"
    return "    ∞" if spend > 0 else "    -"


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    buyers = {"MY": {}, "SG": {}}
    recent = {"MY": [], "SG": []}
    for s in sales:
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        key = s.ad or "(无 UTM ad)"
        d = buyers[label].setdefault(key, {"life": 0, "d60": 0, "d30": 0, "d14": 0})
        d["life"] += 1
        if s.date:
            age = (TODAY - s.date).days
            if age <= 60:
                d["d60"] += 1
            if age <= 30:
                d["d30"] += 1
            if age <= 14:
                d["d14"] += 1
                recent[label].append((s.date.isoformat(), key, s.campaign))

    for label, cfg in ACCTS:
        st = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        acct = st.meta.account_path
        token = result_action_type(st.meta.conversion_event)
        print(f"═══ [{label}] {acct} ═══")
        try:
            per, camps = {}, {}

            def add(win, rows):
                for r in rows:
                    name = cpa.norm(r.get("ad_name") or "")
                    if not name:
                        continue
                    m = per.setdefault(name, {})
                    m[f"sp_{win}"] = m.get(f"sp_{win}", 0.0) + float(r.get("spend") or 0)
                    m[f"ld_{win}"] = m.get(f"ld_{win}", 0.0) + extract_results(
                        r.get("actions"), token)
                    cn = r.get("campaign_name")
                    if cn:
                        camps.setdefault(name, set()).add(cn)

            for win, days in WINDOWS:
                since = (TODAY - dt.timedelta(days=days)).isoformat()
                add(win, g.account_insights(
                    acct, level="ad", fields="ad_id,ad_name,campaign_name,spend,actions",
                    time_range={"since": since, "until": TODAY.isoformat()}))
                time.sleep(2)
            add("max", g.account_insights(
                acct, level="ad", fields="ad_id,ad_name,campaign_name,spend,actions",
                date_preset="maximum"))
            time.sleep(2)

            names = set(per) | set(buyers[label])
            recs = []
            for n in names:
                m = per.get(n, {})
                b = buyers[label].get(n, {"life": 0, "d60": 0, "d30": 0, "d14": 0})
                recs.append({
                    "name": n, "b": b, "camps": sorted(camps.get(n, ())),
                    "sp14": m.get("sp_d14", 0.0), "sp30": m.get("sp_d30", 0.0),
                    "sp60": m.get("sp_d60", 0.0), "spmax": m.get("sp_max", 0.0),
                    "ld14": m.get("ld_d14", 0.0), "ld30": m.get("ld_d30", 0.0),
                    "ld60": m.get("ld_d60", 0.0), "on_meta": n in per,
                })

            for win, days in WINDOWS + (("max", None),):
                sp = sum(r[f"sp{win[1:]}" if win != "max" else "spmax"] for r in recs)
                ld = sum(r[f"ld{win[1:]}"] for r in recs) if win != "max" else None
                bw = sum(r["b"]["life" if win == "max" else win] for r in recs)
                cpl = f" CPL={sp/ld:5.1f}" if ld else ""
                lead_s = f" leads={ld:5.0f}" if ld is not None else ""
                print(f"  {win:>4}: spend={sp:8.0f}{lead_s}{cpl}  buyers={bw:3d}"
                      f"  CPA={fmt_cpa(sp, bw)}")

            sp30_all = sum(r["sp30"] for r in recs) or 1.0
            sp30_sell = sum(r["sp30"] for r in recs if r["b"]["d60"] > 0)
            sp30_never = sum(r["sp30"] for r in recs if r["b"]["life"] == 0)
            print(f"  30d 花费分布: {sp30_sell/sp30_all*100:4.1f}% 给了近60天有出单的广告 · "
                  f"{sp30_never/sp30_all*100:4.1f}% 给了从未出过单的广告\n")

            print("  ▍TOP SPEND 近30天  (花费/名单/CPL | 成交30d/60d/终身 | CPA60 | 名单→成交%)")
            for r in sorted(recs, key=lambda x: -x["sp30"])[:12]:
                if r["sp30"] <= 0:
                    continue
                b = r["b"]
                cpl = f"{r['sp30']/r['ld30']:5.1f}" if r["ld30"] else "    ∞"
                conv = f"{b['d30']/r['ld30']*100:4.1f}%" if r["ld30"] else "   - "
                flag = "🔴" if (r["sp30"] >= 300 and b["d60"] == 0) else "  "
                camp = (r["camps"][-1][:26] if r["camps"] else "")
                print(f"   {flag} {r['sp30']:7.0f} {r['ld30']:5.0f} {cpl} | "
                      f"{b['d30']:2d}/{b['d60']:2d}/{b['life']:3d} | {fmt_cpa(r['sp60'], b['d60'])} | "
                      f"{conv}  «{r['name'][:38]}» ({camp})")

            print("\n  ▍TOP SELLERS  (成交14d/30d/60d/终身 | 近14天花费 | 近30天花费(占比) | CPA60)")
            sellers = [r for r in recs if r["b"]["d60"] > 0 or r["b"]["life"] >= 3]
            for r in sorted(sellers, key=lambda x: (-x["b"]["d60"], -x["b"]["life"]))[:10]:
                b = r["b"]
                fund = "🔥" if r["sp14"] >= 50 else ("💤" if r["on_meta"] else "🌐非广告")
                print(f"   {fund} {b['d14']:2d}/{b['d30']:2d}/{b['d60']:2d}/{b['life']:3d} | "
                      f"14d {r['sp14']:6.0f} | 30d {r['sp30']:7.0f} ({r['sp30']/sp30_all*100:4.1f}%) | "
                      f"CPA60 {fmt_cpa(r['sp60'], b['d60'])}  «{r['name'][:40]}»")

            print("\n  ▍最近 14 天成交明细 (日期 · 广告 · campaign)")
            for date, ad, camp in sorted(recent[label], reverse=True)[:20]:
                print(f"    {date}  «{ad[:36]}»  ({camp[:30]})")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()

    print("AUDIT DONE (read-only)")


if __name__ == "__main__":
    main()
