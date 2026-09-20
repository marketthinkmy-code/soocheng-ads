# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-19「看下 MY SG 从星期五到现在的广告，哪些要开/scale/关，
要根据 CPL CPA」.

Per ad (MY + SG), window Fri 2026-09-18 → today (account-TZ dates):
  window spend + registrations (exact Results bucket, same as the monitor) → CPL,
  fresh sheet sales in the window, 60d strict sales + spend → CPA context,
  current delivery status + budget carrier. Ads that spent in the window but are
  no longer delivering are flagged (who closed them shows in the activity tail).
Prints dates/UTM/RM only — no student PII."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

SINCE = "2026-09-18"                    # 星期五 (MYT)
FRI = dt.date(2026, 9, 18)


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s_sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d60 = today - dt.timedelta(days=30)   # owner 2026-09-20:「以 30 day cpa 为标准」
    rng_w = {"since": SINCE, "until": today.isoformat()}
    rng60 = {"since": d60.isoformat(), "until": today.isoformat()}
    token = result_action_type(s_my.meta.conversion_event)

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    fresh_strict, fresh_pool = {}, {}
    strict60, sp_needed = {}, None
    for x in sales:
        if not x.date:
            continue
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        ck = cpa.creative_key(x.ad)
        if x.date >= d60:
            strict60[k] = strict60.get(k, 0) + 1
        if x.date >= FRI:
            fresh_strict[k] = fresh_strict.get(k, 0) + 1
            fresh_pool[ck] = fresh_pool.get(ck, 0) + 1
    n_fresh = sum(fresh_pool.values())
    print(f"窗口 {SINCE} → {today}（星期五起）· sheet 新成交 {n_fresh} 单\n")
    if fresh_pool:
        for ck, n in sorted(fresh_pool.items(), key=lambda x: -x[1]):
            print(f"  🎉 新成交 «{ck[:40]}» × {n}")
        print()

    for label, st, line, min_sp in (("MY", s_my, 60.0, 60.0), ("SG", s_sg, 95.0, 142.0)):
        g = graph_client(st)
        ads = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,"
                       "campaign{name,status,daily_budget},"
                       "adset{name,status,daily_budget,promoted_object}",
             "limit": "500"})
        time.sleep(1.2)
        win = {r.get("ad_id"): r for r in g.account_insights(
            st.meta.account_path, level="ad", fields="ad_id,spend,actions",
            time_range=rng_w)}
        time.sleep(1.2)
        sp60 = {r.get("ad_id"): float(r.get("spend") or 0) for r in g.account_insights(
            st.meta.account_path, level="ad", fields="ad_id,spend", time_range=rng60)}
        time.sleep(1.2)

        rows, tot_sp, tot_rg = [], 0.0, 0.0
        for a in ads:
            ev = ((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type")
            if (ev or "").upper() != "COMPLETE_REGISTRATION":
                continue
            r = win.get(a["id"]) or {}
            sp = float(r.get("spend") or 0)
            live = a.get("effective_status") == "ACTIVE"
            if sp <= 0 and not live:
                continue
            rg = extract_results(r.get("actions"), token)
            tot_sp, tot_rg = tot_sp + sp, tot_rg + rg
            camp = (a.get("campaign") or {}).get("name") or "?"
            aset = a.get("adset") or {}
            bud = aset.get("daily_budget") or (a.get("campaign") or {}).get("daily_budget")
            n_f = fresh_strict.get((_mkey(camp), cpa.norm(a.get("name") or "")), 0)
            n60 = strict60.get((_mkey(camp), cpa.norm(a.get("name") or "")), 0)
            s60 = sp60.get(a["id"], 0.0)
            rows.append((sp, rg, live, a, camp, bud, n_f, n60, s60))
        rows.sort(key=lambda x: -x[0])

        cpl_all = f"RM{tot_sp / tot_rg:.0f}" if tot_rg else "∞"
        print(f"═══ [{label}] 周五起花 RM{tot_sp:,.0f} · {tot_rg:.0f} regs · 整体 CPL {cpl_all}"
              f"（线 RM{line:.0f}，花满 RM{min_sp:.0f} 才判）═══")
        for sp, rg, live, a, camp, bud, n_f, n60, s60 in rows:
            cpl = f"RM{sp / rg:.0f}" if rg else "∞"
            state = "" if live else f"  ⛔已停({a.get('effective_status')})"
            if sp < min_sp:
                v = "⏳ 未花满"
            elif rg == 0:
                v = "❌ 0-reg 到线"
            elif sp / rg > line:
                v = "⚠️ CPL 超线"
            else:
                v = "✅ CPL 达标"
            cpa_s = ""
            if n60:
                cpa_s = f" · 30天 {n60} 单 CPA RM{s60 / n60:.0f}"
            elif s60 >= 1000:
                cpa_s = f" · 30天 RM{s60:.0f} 无单"
            fresh_s = f" · 🎉周五起 {n_f} 单" if n_f else ""
            bud_s = f" · 预算 RM{int(bud) / 100:.0f}/天" if bud else ""
            print(f"  {v:<10} «{(a.get('name') or '')[:34]}» @ «{camp[:28]}»{state}")
            print(f"      花 RM{sp:,.0f} / {rg:.0f} regs / CPL {cpl}{fresh_s}{cpa_s}{bud_s}")
        print()

        since_ts = int(dt.datetime(2026, 9, 17, 16, 0).timestamp())  # ≈Fri 00:00 MYT
        acts = g._get_all(
            f"{st.meta.account_path}/activities",
            {"fields": "event_time,event_type,actor_name,object_name",
             "since": str(since_ts), "limit": "150"})
        time.sleep(1.2)
        evts = [x for x in acts if "run_status" in (x.get("event_type") or "")
                or "budget" in (x.get("event_type") or "")]
        print(f"── [{label}] 周五起 开/关/预算 动作 {len(evts)} 条 ──")
        for x in evts[:45]:
            t = (x.get("event_time") or "")[5:16]
            print(f"  {t}  {(x.get('actor_name') or '?')[:18]:<18} "
                  f"{(x.get('event_type') or '')[:26]:<26} «{(x.get('object_name') or '')[:34]}»")
        print()
    print("CPL×CPA FRI-REPORT DONE (read-only)")


if __name__ == "__main__":
    main()
