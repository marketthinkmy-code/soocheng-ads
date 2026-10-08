# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08「明天看完第一天 CPL 告诉我」— SG 开回后的第一天成绩单。

每支在跑的 registration ad：昨天（账户时区整天）花费 / 报名 / CPL，今天到现在，载体预算，
对照 SG 线 RM95（monitor 的 0-reg 门槛 RM142）；账户合计；近 24h monitor / 人工的开关与预算
动作（看有没有被自动降 30% 或关掉）；禁跑素材是否仍 0 支在跑。只印 RM / 日期，无 PII。"""
from __future__ import annotations

import datetime as dt
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

LINE = 95.0          # SG CPL 线
ZERO_REG_SPEND = 142.0


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)
    banned = s.compliance.banned_creatives

    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,campaign{id,name,daily_budget},"
                  "adset{id,name,daily_budget,promoted_object}", "limit": "500"})
    time.sleep(1.2)
    y = {r.get("ad_id"): r for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend,actions", date_preset="yesterday")}
    time.sleep(1.2)
    t = {r.get("ad_id"): r for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend,actions", date_preset="today")}
    time.sleep(1.2)
    acc_y = g.account_insights(acct, level="account", fields="spend,actions", date_preset="yesterday")
    time.sleep(1.2)
    acc_t = g.account_insights(acct, level="account", fields="spend,actions", date_preset="today")

    def m(d, aid):
        r = d.get(aid) or {}
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        return sp, rg

    live = [a for a in ads if a.get("effective_status") == "ACTIVE"
            and (((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type") or "").upper()
            == "COMPLETE_REGISTRATION"]
    rows = []
    for a in live:
        sy, ry = m(y, a["id"])
        st, rt = m(t, a["id"])
        aset, camp = a.get("adset") or {}, a.get("campaign") or {}
        carrier = (f"adset RM{float(aset['daily_budget'])/100:.0f}" if aset.get("daily_budget")
                   else f"CBO RM{float(camp.get('daily_budget') or 0)/100:.0f}")
        rows.append((a, sy, ry, st, rt, carrier))
    rows.sort(key=lambda r: -r[1])

    yd = (acc_y[0].get("date_start") if acc_y else "昨天")
    print(f"═══ SG 第一天成绩单 — {yd}（账户时区整天）· 在跑 {len(live)} 支 ═══")
    print(f"{'素材 @ campaign':<58} {'载体':<12} {'昨天花费':>8} {'报名':>4} {'CPL':>6} | {'今天花费':>8} {'报名':>4}")
    for a, sy, ry, st, rt, carrier in rows:
        nm = f"{(a.get('name') or '')[:26]} @ {((a.get('campaign') or {}).get('name') or '')[16:44]}"
        cpl = f"{sy/ry:.0f}" if ry else ("∞" if sy else "—")
        flag = ""
        if ry and sy / ry > LINE:
            flag = " ⚠️ 超线"
        elif not ry and sy >= ZERO_REG_SPEND:
            flag = " ❌ 0 reg 花满"
        elif ry and sy / ry <= LINE and sy >= 50:
            flag = " ✅"
        print(f"{nm:<58} {carrier:<12} RM{sy:>6.0f} {ry:>4.0f} {cpl:>6} | RM{st:>6.0f} {rt:>4.0f}{flag}")
    if acc_y:
        sp = float(acc_y[0].get("spend") or 0); rg = extract_results(acc_y[0].get("actions"), token)
        print(f"\n  昨天合计 RM{sp:,.0f} · 报名 {rg:.0f} · CPL {sp/rg:.0f}" if rg else f"\n  昨天合计 RM{sp:,.0f} · 报名 0")
    if acc_t:
        sp = float(acc_t[0].get("spend") or 0); rg = extract_results(acc_t[0].get("actions"), token)
        print(f"  今天到现在 RM{sp:,.0f} · 报名 {rg:.0f}" + (f" · CPL {sp/rg:.0f}" if rg else ""))

    bad = [a for a in live if compliance.is_banned(a.get("name") or "", banned)]
    print(f"\n🚫 在跑的禁跑素材：{len(bad)} 支" + ("" if not bad else " ← 立刻停！"))

    since_ts = int(dt.datetime.utcnow().timestamp()) - 26 * 3600
    acts = g._get_all(acct + "/activities", {
        "fields": "event_time,event_type,actor_name,object_name,extra_data",
        "since": str(since_ts), "limit": "200"})
    evts = [x for x in acts if any(k in (x.get("event_type") or "")
                                   for k in ("run_status", "budget", "bid"))]
    print(f"\n═══ 近 26 小时 开/关/预算 动作（{len(evts)} 条，最新在前）═══")
    for x in evts[:40]:
        print(f"  {(x.get('event_time') or '')[5:16]}  {(x.get('actor_name') or '?')[:18]:<18}"
              f" {(x.get('event_type') or '')[:30]:<30} «{(x.get('object_name') or '')[:36]}»")
    print("\nDAY1 REPORT DONE (read-only)")


if __name__ == "__main__":
    main()
