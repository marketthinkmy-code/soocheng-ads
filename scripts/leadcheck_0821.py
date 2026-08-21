# -*- coding: utf-8 -*-
"""READ-ONLY (owner 8/21 «today & yesterday 广告跑到蛮贵，帮我看哪些需要关»):

Per ACTIVE-delivering ad, last-2-days (8/20-8/21) spend/leads/CPL joined with its
60d sheet sales + 60d spend (CPA60) so high-CPL-but-selling ads are rescued, not
flagged. Verdicts follow the CPL-monitor framework:
  🟢 留          CPL healthy for the account (MY ≤50 / SG ≤80)
  🛟 留(CPA救)   CPL high but sold in 60d at CPA ≤ 1200
  🔴 建议关       spend ≥ 80 with 0 leads, or CPL high with no 60d sales
                 (or CPA60 > 1200)
  🆕 新·再等     AUG NEW fleet (launched 8/20) — learning phase, judge ≥8/23
  ⏳ 太早        2d spend < 80 — not judgeable yet
No writes. Owner decides the 🔴 list."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 21)
SINCE2 = dt.date(2026, 8, 20)
D60 = TODAY - dt.timedelta(days=60)
MIN_SPEND = 80.0
HARD = 1200.0
CPL_HI = {"MY": 50.0, "SG": 80.0}
N = cpa.norm


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)
    sold60 = {"MY": {}, "SG": {}}
    for s in sales:
        if not s.ad or not s.date or s.date <= D60:
            continue
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        sold60[label][s.ad] = sold60[label].get(s.ad, 0) + 1

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══ [{label}] {acct} · 8/20-8/21 ═══")
        try:
            rows2 = g.account_insights(
                acct, level="ad", fields="ad_id,ad_name,campaign_name,spend,actions",
                time_range={"since": SINCE2.isoformat(), "until": TODAY.isoformat()})
            time.sleep(2)
            sp60 = {}
            for r in g.account_insights(
                    acct, level="ad", fields="ad_name,spend",
                    time_range={"since": D60.isoformat(), "until": TODAY.isoformat()}):
                k = N(r.get("ad_name") or "")
                sp60[k] = sp60.get(k, 0.0) + float(r.get("spend") or 0)
            time.sleep(2)
            eff = {a["id"]: a.get("effective_status") for a in g._get_all(
                f"{acct}/ads", {"fields": "id,effective_status", "limit": "300"})}
            time.sleep(1)

            tot_sp = tot_ld = 0.0
            flagged = []
            print("   近2天spend  leads   CPL | 60d成交  CPA60 | 判定")
            for r in sorted(rows2, key=lambda x: -float(x.get("spend") or 0)):
                sp = float(r.get("spend") or 0)
                if sp < 20:
                    continue
                ld = extract_results(r.get("actions"), token)
                tot_sp += sp
                tot_ld += ld
                name = r.get("ad_name") or ""
                camp = r.get("campaign_name") or ""
                nn = N(name)
                n60 = sold60[label].get(nn, 0)
                s60 = sp60.get(nn, 0.0)
                cpa60 = (s60 / n60) if n60 else None
                cpl = (sp / ld) if ld else None
                st = eff.get(r.get("ad_id"), "?")

                if "AUG NEW" in camp:
                    verdict = "🆕 新·再等(8/23判)"
                elif sp < MIN_SPEND:
                    verdict = "⏳ 太早"
                elif ld == 0:
                    verdict = ("🛟 留(CPA救)" if n60 and cpa60 <= HARD
                               else "🔴 建议关(烧钱0名单)")
                elif cpl <= CPL_HI[label]:
                    verdict = "🟢 留"
                elif n60 and cpa60 <= HARD:
                    verdict = "🛟 留(CPA救)"
                elif n60:
                    verdict = f"🔴 建议关(CPA60 {cpa60:.0f}>1200)"
                else:
                    verdict = "🔴 建议关(CPL高·60d没单)"
                if verdict.startswith("🔴") and st == "ACTIVE":
                    flagged.append(name)
                cpl_s = f"{cpl:5.1f}" if cpl else "    ∞"
                cpa_s = f"{cpa60:5.0f}" if cpa60 else "    -"
                print(f"   RM{sp:6.0f}  {ld:4.0f}  {cpl_s} | {n60:2d}  {cpa_s} |"
                      f" {verdict}  «{name[:34]}» ({camp[:24]}) [{st}]")
            cpl_t = f"{tot_sp/tot_ld:.1f}" if tot_ld else "-"
            print(f"   ── 合计 RM{tot_sp:.0f} · {tot_ld:.0f} 名单 · CPL {cpl_t}")
            print(f"   🔴 ACTIVE 建议关清单: {flagged if flagged else '（无）'}")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()
    print("LEADCHECK DONE (read-only — nothing was paused)")


if __name__ == "__main__":
    main()
