# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08 问两支的 lifetime ad spend（他要决定关 / 加预算）：
  · 拼接：Video 1：用我的方法 @ PURCHASE LAL 1-5% 0910 重拍（RM100 adset）— 要不要关
  · HOOK：Video 12：不选 forex 不选黄金 @ BROAD SG 25+ 0911（RM50 adset）— 要不要加到 RM100
每支先给「这个位」的 lifetime 花费 / 报名 / CPL / 成交 / CPA，再给「同一支素材在 SG 所有位」的
合计（sheet 只取 [SG] 的 campaign）。顺带复查 🚫 改名有没有全部落地。只印日期/RM，无 PII。"""
from __future__ import annotations

import datetime as dt
import time

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

TARGETS = {
    "120249406487260521": "拼接：Video 1：用我的方法 @ PURCHASE LAL 1-5% | 0910 重拍（RM100 adset）",
    "120249390893070521": "HOOK：Video 12：不选 forex 不选黄金 @ BROAD SG 25+ | 0911（RM50 adset）",
}


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    strict, by_ck = {}, {}
    for x in sales:
        if "[sg]" not in (x.campaign or "").casefold():
            continue
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        strict[k] = strict.get(k, 0) + 1
        ck = cpa.creative_key(x.ad)
        by_ck.setdefault(ck, []).append(x.date)

    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,created_time,"
                  "campaign{name},adset{name,daily_budget}", "limit": "500"})
    time.sleep(1.2)
    life = {r.get("ad_id"): r for r in g.account_insights(
        acct, level="ad", fields="ad_id,spend,actions", date_preset="maximum")}
    by_id = {a["id"]: a for a in ads}

    def line(a):
        r = life.get(a["id"]) or {}
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        camp = (a.get("campaign") or {}).get("name") or ""
        n = strict.get((_mkey(camp), cpa.norm(a.get("name") or "")), 0)
        cpl = f"CPL {sp/rg:.0f}" if rg else ("0 reg" if sp else "—")
        c = f"CPA {sp/n:.0f}" if n else "无单"
        ab = (a.get("adset") or {}).get("daily_budget")
        ab = f"RM{float(ab)/100:.0f}/d" if ab else "CBO"
        return sp, rg, n, (f"RM{sp:>7.0f}  报名 {rg:>3.0f}  {cpl:<8} 成交 {n}  {c:<9} "
                           f"[{a.get('effective_status')}] {ab}  建 {(a.get('created_time') or '')[:10]}"
                           f"  @ «{camp[:40]}»")

    for aid, label in TARGETS.items():
        a = by_id.get(aid)
        print(f"═══ {label} ═══")
        if not a:
            print("  找不到这个 ad id\n")
            continue
        sp, rg, n, txt = line(a)
        print(f"  这个位 lifetime：{txt}")
        ck = cpa.creative_key(a.get("name") or "")
        sib = [b for b in ads if cpa.creative_key(b.get("name") or "") == ck
               and not compliance.is_banned(b.get("name") or "", s.compliance.banned_creatives)]
        tsp = trg = tn = 0.0
        print(f"  同一支素材在 SG 全部 {len(sib)} 个位：")
        for b in sorted(sib, key=lambda b: -float((life.get(b['id']) or {}).get('spend') or 0)):
            bsp, brg, bn, btxt = line(b)
            if bsp == 0 and bn == 0:
                continue
            tsp += bsp; trg += brg; tn += bn
            print(f"      «{(b.get('name') or '')[:34]}» {btxt}")
        dates = sorted(d for d in by_ck.get(ck, []) if d)
        last = dates[-1].isoformat() if dates else "从无"
        print(f"  ── 素材合计 lifetime：RM{tsp:,.0f}  报名 {trg:.0f}"
              f"  {'CPL ' + format(tsp/trg, '.0f') if trg else ''}  成交 {tn:.0f}"
              f"  {'CPA ' + format(tsp/tn, '.0f') if tn else '无单'}  最近成交 {last}\n")

    unmarked = [a for a in ads
                if compliance.banned_reason(a.get("name") or "", s.compliance.banned_creatives)
                and not compliance.is_marked(a.get("name") or "")]
    armed = [a for a in ads if compliance.is_banned(a.get("name") or "", s.compliance.banned_creatives)
             and a.get("status") == "ACTIVE"]
    print(f"🚫 复查：禁跑素材未带 🚫 的 {len(unmarked)} 支；ad 层仍 ACTIVE 的禁跑 {len(armed)} 支")
    print("LIFETIME DONE (read-only)")


if __name__ == "__main__":
    main()
