# -*- coding: utf-8 -*-
"""READ-ONLY (owner: «thursday till today 很多被关了，哪些需要关？哪些需要开？»):

Window = 2026-08-20 (Thu) → today (MYT). Every ad that spent ≥ RM20 in the
window, split into 已被关 vs 还在跑, each judged with the CPA-rescue framework:

  已被关 →  🔓 建议开回   sold in 60d at CPA60 ≤ 1200, or ran at healthy CPL
            ⚰️ 留着别开   spent ≥150 with 0 leads / terrible CPL, no sales
            🤷 太早说     window spend < 80
  还在跑 →  🔴 建议关     spend ≥150 & 0 leads (no rescue), or CPL >2×基线 no sales
            🟢/🛟 留      healthy CPL, or CPA-rescued
Baselines: MY CPL 45 · SG 70. No writes."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
SINCE = dt.date(2026, 8, 20)
D60 = TODAY - dt.timedelta(days=60)
BASE = {"MY": 45.0, "SG": 70.0}
HARD = 1200.0
N = cpa.norm


def main() -> None:
    print(f"window {SINCE} → {TODAY} (MYT)\n")
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
        print(f"═══ [{label}] {acct} ═══")
        try:
            rows = g.account_insights(
                acct, level="ad", fields="ad_id,ad_name,campaign_name,spend,actions",
                time_range={"since": SINCE.isoformat(), "until": TODAY.isoformat()})
            time.sleep(2)
            sp60 = {}
            for r in g.account_insights(
                    acct, level="ad", fields="ad_name,spend",
                    time_range={"since": D60.isoformat(), "until": TODAY.isoformat()}):
                k = N(r.get("ad_name") or "")
                sp60[k] = sp60.get(k, 0.0) + float(r.get("spend") or 0)
            time.sleep(2)
            meta = {a["id"]: a for a in g._get_all(
                f"{acct}/ads", {"fields": "id,status,effective_status", "limit": "300"})}
            time.sleep(1)

            closed, running = [], []
            for r in rows:
                sp = float(r.get("spend") or 0)
                if sp < 20:
                    continue
                m = meta.get(r.get("ad_id"), {})
                eff = m.get("effective_status", "?")
                item = {"sp": sp, "ld": extract_results(r.get("actions"), token),
                        "name": r.get("ad_name") or "", "camp": r.get("campaign_name") or "",
                        "eff": eff, "stored": m.get("status", "?")}
                (running if eff == "ACTIVE" else closed).append(item)

            def judge(it, is_closed: bool) -> str:
                nn = N(it["name"])
                n60 = sold60[label].get(nn, 0)
                s60 = sp60.get(nn, 0.0)
                cpa60 = (s60 / n60) if n60 else None
                it["n60"], it["cpa60"] = n60, cpa60
                cpl = (it["sp"] / it["ld"]) if it["ld"] else None
                aug = "AUG NEW" in it["camp"]
                if is_closed:
                    if n60 and cpa60 <= HARD:
                        return "🔓 建议开回(CPA救)"
                    if cpl and cpl <= BASE[label] and it["ld"] >= 3:
                        return "🔓 建议开回(名单便宜)" + ("·新" if aug else "")
                    if it["sp"] < 80:
                        return "🤷 太早说"
                    if it["ld"] == 0 or (cpl and cpl > 2 * BASE[label]):
                        return "⚰️ 留着别开"
                    return "🤔 边缘(CPL " + f"{cpl:.0f})" if cpl else "🤔 边缘"
                if n60 and cpa60 <= HARD:
                    return "🛟 留(CPA救)"
                if it["sp"] >= 150 and it["ld"] == 0:
                    return "🔴 建议关(0名单)"
                if cpl and cpl > 2 * BASE[label] and it["sp"] >= 150:
                    return "🔴 建议关(CPL " + f"{cpl:.0f})"
                if cpl and cpl <= BASE[label]:
                    return "🟢 留"
                return "🟡 观察" + ("·新" if aug else "")

            for title, items, is_closed in (
                    ("已被关（开不开？）", closed, True), ("还在跑（关不关？）", running, False)):
                print(f"  ▍{title} — {len(items)} 支")
                for it in sorted(items, key=lambda x: -x["sp"]):
                    v = judge(it, is_closed)
                    cpl_s = f"{it['sp']/it['ld']:5.1f}" if it["ld"] else "    ∞"
                    cpa_s = f"{it['cpa60']:5.0f}" if it.get("cpa60") else "    -"
                    print(f"   RM{it['sp']:6.0f} {it['ld']:4.0f} {cpl_s} |"
                          f" {it.get('n60',0):2d} {cpa_s} | {v}"
                          f"  «{it['name'][:34]}» ({it['camp'][:24]}) [{it['eff']}]")
                print()
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()
    print("REVIEW DONE (read-only)")


if __name__ == "__main__":
    main()
