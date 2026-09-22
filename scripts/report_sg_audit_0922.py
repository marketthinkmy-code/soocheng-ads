# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-22「也看看 SG 的」— SG closed-ads audit:

  1. ads carrying issues_info (rejections / delivery errors) — esp. the 🌟GOLF
     campaign now showing "No ads + Ad errors" in Ads Manager;
  2. closed ads whose 30d strict CPA actually PASSES (≤960) or sits 960-1200;
  3. run-status activity of the last 30h — who closed korea @ BROAD A.
Prints dates/UTM/RM only — no student PII."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d30 = today - dt.timedelta(days=30)

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    strict30 = {}
    for x in sales:
        if x.date and x.date >= d30:
            k = (_mkey(x.campaign), cpa.norm(x.ad))
            strict30[k] = strict30.get(k, 0) + 1

    for label in ("MY", "SG"):
        st = s_my if label == "MY" else s
        g = graph_client(st)
        ads = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,issues_info,"
                       "campaign{name,status},adset{name,status}", "limit": "500"})
        time.sleep(1.2)
        sp30 = {r.get("ad_id"): float(r.get("spend") or 0) for r in g.account_insights(
            st.meta.account_path, level="ad", fields="ad_id,spend",
            time_range={"since": d30.isoformat(), "until": today.isoformat()})}
        time.sleep(1.2)

        print(f"═══ [{label}] 有 issues 的 ads（拒审/投放错误）═══")
        n_iss = 0
        for a in ads:
            for iss in a.get("issues_info") or []:
                n_iss += 1
                print(f"  ⛔ «{(a.get('name') or '')[:34]}» @ «{((a.get('campaign') or {}).get('name') or '')[:34]}»"
                      f" [{a.get('effective_status')}]")
                print(f"      {iss.get('error_summary', '')[:70]} — {iss.get('error_message', '')[:100]}")
        if not n_iss:
            print("  （没有）")
        print()

        print(f"═══ [{label}] 已关但 30 天 CPA 其实达标 / 边缘 ═══")
        found = 0
        for a in ads:
            if a.get("effective_status") == "ACTIVE":
                continue
            camp = (a.get("campaign") or {}).get("name") or "?"
            n = strict30.get((_mkey(camp), cpa.norm(a.get("name") or "")), 0)
            if not n:
                continue
            c = sp30.get(a["id"], 0.0) / n
            tag = "✅ 达标(≤960)" if c <= 960 else ("⚠️ 边缘(960-1200)" if c <= 1200 else "❌ 超硬线")
            if c <= 1200:
                found += 1
                print(f"  {tag}  «{(a.get('name') or '')[:34]}» @ «{camp[:32]}»"
                      f" [{a.get('effective_status')}] — 30d {n} 单 CPA RM{c:.0f}")
        if not found:
            print("  （没有——关着的要么无单要么超硬线）")
        print()

        since_ts = int(dt.datetime.utcnow().timestamp()) - 30 * 3600
        acts = g._get_all(
            f"{st.meta.account_path}/activities",
            {"fields": "event_time,event_type,actor_name,object_name",
             "since": str(since_ts), "limit": "120"})
        evts = [x for x in acts if "run_status" in (x.get("event_type") or "")]
        print(f"═══ [{label}] 近 30 小时 开/关 动作（{len(evts)} 条）═══")
        for x in evts[:40]:
            print(f"  {(x.get('event_time') or '')[5:16]}  {(x.get('actor_name') or '?')[:18]:<18} "
                  f"{(x.get('event_type') or '')[:26]:<26} «{(x.get('object_name') or '')[:36]}»")
        print()
    print("\nAUDIT DONE (read-only)")


if __name__ == "__main__":
    main()
