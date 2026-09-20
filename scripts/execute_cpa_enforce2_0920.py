# -*- coding: utf-8 -*-
"""Owner 2026-09-20「我不希望我现在开着的广告，都是很久没有成交过的 / cpa 不合格的
（新广告例外）」— guarantee sweep over EVERY running registration ad, MY + SG.

Verdict per running ad:
  NEW        ad created ≤14 天 (conversion window)          -> keep（新广告例外）
  PASS       30d strict sales, CPA ≤ RM960                  -> keep（达标）
  WATCH      30d CPA 960-1200                               -> keep, flagged
  KILL-CPA   30d CPA > RM1,200                              -> pause
  FRESH      0 strict 30d sales BUT creative sold ≤7 天     -> keep（素材上周有单）
  KILL-STALE 0 strict 30d sales, old position, stale creative -> pause（很久没成交）
Conflict guard: ads the owner named-reopened today are never auto-killed —
printed as ⚠️CONFLICT for his call instead. CONFIRM gate; verify at the end."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
NEW_DAYS, FRESH_DAYS = 14, 7
PASS_MAX, HARD = 960.0, 1200.0
# owner-named reopens today — never auto-kill, surface as CONFLICT instead
PROTECT = {("video 1：用我的方法", "INVESTMENT"), ("freestyle: korea", "| BROAD |"),
           ("拼接：Video 1：用我的方法", "PURCHASE L"),
           ("video 5：trading 早就不是这样了！", "GOLF"), ("🌟 freestyle 1", "| BROAD |")}


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d30 = today - dt.timedelta(days=30)
    d7 = today - dt.timedelta(days=FRESH_DAYS)
    print(f"保证性清扫：达标 / 新 / 素材7天有单 才开着 — {mode}\n")

    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    strict30, fresh_ck = {}, set()
    for x in sales:
        if not x.date:
            continue
        if x.date >= d30:
            k = (_mkey(x.campaign), cpa.norm(x.ad))
            strict30[k] = strict30.get(k, 0) + 1
        if x.date >= d7:
            fresh_ck.add(cpa.creative_key(x.ad))

    kills = []
    for cfg in ("config.yaml", "config.sg.yaml"):
        label = "MY" if cfg == "config.yaml" else "SG"
        st = s_my if cfg == "config.yaml" else load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        ads = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,created_time,"
                       "campaign{name},adset{promoted_object}", "limit": "500"})
        time.sleep(1.2)
        sp30 = {r.get("ad_id"): float(r.get("spend") or 0) for r in g.account_insights(
            st.meta.account_path, level="ad", fields="ad_id,spend",
            time_range={"since": d30.isoformat(), "until": today.isoformat()})}
        time.sleep(1.2)

        print(f"═══ [{label}] 开着的逐支判定 ═══")
        for a in ads:
            if a.get("effective_status") != "ACTIVE":
                continue
            ev = ((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type")
            if (ev or "").upper() != "COMPLETE_REGISTRATION":
                continue
            name = (a.get("name") or "").strip()
            camp = (a.get("campaign") or {}).get("name") or "?"
            try:
                age = (today - dt.date.fromisoformat((a.get("created_time") or "")[:10])).days
            except ValueError:
                age = 999
            n = strict30.get((_mkey(camp), cpa.norm(name)), 0)
            sp = sp30.get(a["id"], 0.0)
            ck = cpa.creative_key(name)
            head = f"«{name[:32]}» @ «{camp[:26]}» ({age}天)"
            if n and sp / n <= PASS_MAX:
                print(f"  ✅ PASS   {head} — 30d {n} 单 CPA RM{sp / n:.0f}")
            elif n and sp / n <= HARD:
                print(f"  ⚠️ WATCH  {head} — 30d CPA RM{sp / n:.0f} (960-1200)")
            elif age <= NEW_DAYS and not n:
                print(f"  🆕 NEW    {head} — 30d RM{sp:.0f}，判决日 ~{today + dt.timedelta(days=NEW_DAYS - age)}")
            elif not n and ck in fresh_ck:
                print(f"  🔥 FRESH  {head} — 本位 30d 无单，但素材 {FRESH_DAYS} 天内有成交")
            elif any(name == pn and psub in camp for pn, psub in PROTECT):
                print(f"  ⚠️ CONFLICT {head} — 按规则该关，但你今天刚点名开回，留给你定")
            else:
                why = (f"30d CPA RM{sp / n:.0f} >1200" if n
                       else f"30d RM{sp:.0f} 无单且素材无近单")
                print(f"  ❌ KILL   {head} — {why}")
                kills.append((cfg, a["id"], name, camp, why))
        print()

    if kills:
        print("── 执行关 ──")
    for cfg, aid, name, camp, why in kills:
        st = s_my if cfg == "config.yaml" else load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        if CONFIRM:
            g.update_status(aid, "PAUSED")
            time.sleep(PACE)
            o = g.get_object(aid, fields="effective_status")
            print(f"  ✔ 关 «{name[:32]}» @ «{camp[:30]}» → {o.get('effective_status')}")
        else:
            print(f"  [dry] 关 «{name[:32]}» @ «{camp[:30]}»（{why}）")
    if not kills:
        print("（没有要关的——全部 达标/新/素材有近单）")
    print("\nENFORCE-2 DONE")


if __name__ == "__main__":
    main()
