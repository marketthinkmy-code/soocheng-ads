# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08「我现在要你开回 SG 的广告，下个星期三 14/10 就是直播
… 你告诉我 你会开哪一个？原因是什么？」

SG 复盘盘面（不写任何东西）：
  1. 两个账户的 account_status（MY 是否仍 DISABLED、SG 是否仍 ACTIVE）；
  2. 每一支 SG ad：禁跑旗标（adbot.compliance）· 自身审核状态 / issues ·
     status 链（ad / adset / campaign）· 建立日 · 30d 花费+报名 → CPL ·
     30d / 60d strict 成交 → CPA · 素材池（creative_key）7d / 30d / 60d 成交；
  3. campaign + adset 清单（status / daily_budget）= 开回时要动的预算载体；
  4. 近 7 天 开/关 动作（谁关的）。
只印日期 / UTM / RM — 不印学员 PII。"""
from __future__ import annotations

import collections
import datetime as dt
import time

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    banned = s.compliance.banned_creatives
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d7, d30, d60 = (today - dt.timedelta(days=n) for n in (7, 30, 60))
    token = result_action_type(s.meta.conversion_event)

    # ── 1. 账户状态 ───────────────────────────────────────────────────────────
    print("═══ 账户状态 ═══")
    for label, st in (("MY", s_my), ("SG", s)):
        g = graph_client(st)
        try:
            info = g._request("GET", st.meta.account_path, params={
                "fields": "name,account_status,disable_reason,currency,"
                          "amount_spent,spend_cap,business_country_code"})
            print(f"  [{label}] «{info.get('name')}» status={info.get('account_status')}"
                  f" disable_reason={info.get('disable_reason')}"
                  f" {info.get('currency')} 累计花费 {float(info.get('amount_spent') or 0)/100:,.0f}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  [{label}] 读不到：{str(exc)[:120]}")
        time.sleep(1.0)
    print()

    # ── 2. 成交（sheet）────────────────────────────────────────────────────────
    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    strict30, strict60 = {}, {}
    pool7, pool30, pool60 = {}, {}, {}
    last_sale = {}                      # creative_key -> 最近成交日
    for x in sales:
        if not x.date:
            continue
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        ck = cpa.creative_key(x.ad)
        if x.date >= d60:
            strict60[k] = strict60.get(k, 0) + 1
            pool60[ck] = pool60.get(ck, 0) + 1
        if x.date >= d30:
            strict30[k] = strict30.get(k, 0) + 1
            pool30[ck] = pool30.get(ck, 0) + 1
        if x.date >= d7:
            pool7[ck] = pool7.get(ck, 0) + 1
        if ck not in last_sale or x.date > last_sale[ck]:
            last_sale[ck] = x.date

    g = graph_client(s)
    acct = s.meta.account_path
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,created_time,issues_info,"
                  "campaign{id,name,status,effective_status,daily_budget},"
                  "adset{id,name,status,effective_status,daily_budget,promoted_object}",
        "limit": "500"})
    time.sleep(1.2)
    ins30 = {r.get("ad_id"): r for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend,actions",
        time_range={"since": d30.isoformat(), "until": today.isoformat()})}
    time.sleep(1.2)
    sp60 = {r.get("ad_id"): float(r.get("spend") or 0) for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend",
        time_range={"since": d60.isoformat(), "until": today.isoformat()})}
    time.sleep(1.2)
    ins7 = {r.get("ad_id"): r for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend,actions",
        time_range={"since": d7.isoformat(), "until": today.isoformat()})}
    time.sleep(1.2)

    def row(a: dict) -> dict:
        camp = a.get("campaign") or {}
        aset = a.get("adset") or {}
        nm = a.get("name") or ""
        r30 = ins30.get(a["id"]) or {}
        sp30 = float(r30.get("spend") or 0)
        rg30 = extract_results(r30.get("actions"), token)
        r7 = ins7.get(a["id"]) or {}
        k = (_mkey(camp.get("name") or ""), cpa.norm(nm))
        ck = cpa.creative_key(nm)
        n30, n60 = strict30.get(k, 0), strict60.get(k, 0)
        created = (a.get("created_time") or "")[:10]
        try:
            age = (today - dt.date.fromisoformat(created)).days
        except ValueError:
            age = -1
        return {
            "id": a["id"], "name": nm, "camp": camp, "aset": aset, "ck": ck,
            "eff": a.get("effective_status"), "st": a.get("status"),
            "ban": compliance.banned_reason(nm, banned),
            "iss": a.get("issues_info") or [],
            "created": created, "age": age,
            "sp30": sp30, "rg30": rg30,
            "cpl30": (sp30 / rg30) if rg30 else None,
            "sp7": float(r7.get("spend") or 0),
            "rg7": extract_results(r7.get("actions"), token),
            "n30": n30, "n60": n60,
            "cpa30": (sp30 / n30) if n30 else None,
            "cpa60": (sp60.get(a["id"], 0.0) / n60) if n60 else None,
            "p7": pool7.get(ck, 0), "p30": pool30.get(ck, 0), "p60": pool60.get(ck, 0),
            "last": last_sale.get(ck),
            "reg": ((aset.get("promoted_object") or {}).get("custom_event_type") or "").upper()
                   == "COMPLETE_REGISTRATION",
        }

    rows = [row(a) for a in ads]
    rows.sort(key=lambda r: (-(r["p30"]), -(r["n30"]), r["cpa30"] or 9e9))

    def line(r: dict) -> None:
        chain = f"{r['st']}/{(r['aset'].get('status') or '?')[:6]}/{(r['camp'].get('status') or '?')[:6]}"
        flag = "⛔禁跑" if r["ban"] else ("❗有issue" if r["iss"] else "  ")
        cpl = f"CPL {r['cpl30']:.0f}" if r["cpl30"] else ("0reg" if r["sp30"] else "—")
        c30 = f"CPA30 {r['cpa30']:.0f}({r['n30']}单)" if r["cpa30"] else f"30d无单"
        c60 = f"CPA60 {r['cpa60']:.0f}({r['n60']}单)" if r["cpa60"] else "60d无单"
        pool = f"素材池 7d:{r['p7']} 30d:{r['p30']} 60d:{r['p60']}"
        lastd = f"最近成交 {r['last']}" if r["last"] else "从无成交"
        print(f"  {flag} «{r['name'][:36]}»")
        print(f"        @ «{(r['camp'].get('name') or '')[:46]}» / «{(r['aset'].get('name') or '')[:26]}»")
        print(f"        eff={r['eff']:<22} 链 {chain:<22} 建 {r['created']}({r['age']}d)")
        print(f"        30d 花 RM{r['sp30']:>7.0f} 报名 {r['rg30']:>4.0f} {cpl:<12} | {c30:<22} {c60}")
        print(f"        {pool} · {lastd}")
        if r["ban"]:
            print(f"        ⛔ 禁跑命中：「{r['ban']}」— 永久不投（CPA 再好也不开）")
        for i in r["iss"]:
            print(f"        ❗ {i.get('error_summary','')[:60]} / {i.get('error_message','')[:80]}")

    for title, pred in (
        ("A. 目前仍在跑 (ACTIVE)", lambda r: r["eff"] == "ACTIVE"),
        ("B. 关着的 — 干净可考虑开回", lambda r: r["eff"] != "ACTIVE" and not r["ban"]),
        ("C. 关着的 — ⛔ 禁跑名单（永远不开，建议删）", lambda r: r["eff"] != "ACTIVE" and r["ban"]),
    ):
        sel = [r for r in rows if r["reg"] and pred(r)]
        print(f"═══ {title}（{len(sel)} 支）═══")
        for r in sel:
            line(r)
            print()
        if not sel:
            print("  （没有）\n")

    other = [r for r in rows if not r["reg"]]
    if other:
        print(f"═══ D. 非 registration 目标的 ads（{len(other)} 支，仅列名）═══")
        for r in other:
            print(f"  «{r['name'][:34]}» @ «{(r['camp'].get('name') or '')[:34]}» [{r['eff']}]")
        print()

    # ── 3. 预算载体 ───────────────────────────────────────────────────────────
    camps = g._get_all(acct + "/campaigns", {
        "fields": "id,name,status,effective_status,daily_budget,bid_strategy,created_time",
        "limit": "500"})
    time.sleep(1.2)
    asets = g._get_all(acct + "/adsets", {
        "fields": "id,name,status,effective_status,daily_budget,campaign_id,"
                  "targeting{age_min,age_max,targeting_automation},created_time",
        "limit": "500"})
    time.sleep(1.2)
    by_camp = collections.defaultdict(list)
    for a in asets:
        by_camp[a.get("campaign_id")].append(a)
    ads_by_camp = collections.defaultdict(list)
    for r in rows:
        ads_by_camp[(r["camp"] or {}).get("id")].append(r)

    print("═══ 预算载体：campaign → ad set（开回时要动的层）═══")
    for c in sorted(camps, key=lambda c: (c.get("status") != "ACTIVE", c.get("name") or "")):
        kids = ads_by_camp.get(c["id"], [])
        if not kids and not by_camp.get(c["id"]):
            continue
        cb = f"CBO RM{float(c['daily_budget'])/100:.0f}/d" if c.get("daily_budget") else "ABO"
        nlive = sum(1 for r in kids if r["eff"] == "ACTIVE")
        nclean = sum(1 for r in kids if not r["ban"])
        print(f"  [{c.get('status')}] «{(c.get('name') or '')[:52]}» {cb}"
              f" — ads {len(kids)}（在跑 {nlive} / 干净 {nclean}）")
        for a in by_camp.get(c["id"], []):
            t = a.get("targeting") or {}
            adv = ((t.get("targeting_automation") or {}).get("advantage_audience"))
            ab = f"RM{float(a['daily_budget'])/100:.0f}/d" if a.get("daily_budget") else "—"
            print(f"      · [{a.get('status')}] «{(a.get('name') or '')[:34]}» {ab}"
                  f" age {t.get('age_min')}-{t.get('age_max')} adv+={adv}")
    print()

    since_ts = int(dt.datetime.utcnow().timestamp()) - 7 * 24 * 3600
    acts = g._get_all(acct + "/activities", {
        "fields": "event_time,event_type,actor_name,object_name,extra_data",
        "since": str(since_ts), "limit": "300"})
    evts = [x for x in acts if "run_status" in (x.get("event_type") or "")
            or "update_ad_run_status" in (x.get("event_type") or "")]
    print(f"═══ SG 近 7 天 开/关 动作（{len(evts)} 条，最新在前）═══")
    for x in evts[:60]:
        print(f"  {(x.get('event_time') or '')[5:16]}  {(x.get('actor_name') or '?')[:20]:<20}"
              f" {(x.get('event_type') or '')[:28]:<28} «{(x.get('object_name') or '')[:38]}»")
    print("\nSG REOPEN REPORT DONE (read-only)")


if __name__ == "__main__":
    main()
