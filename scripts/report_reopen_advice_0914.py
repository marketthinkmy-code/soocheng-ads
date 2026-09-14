# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-14 —「有些我关掉是因为被 restricted。look into it，
advice 哪些需要开，也要看星期四到现在的 cpl，高到离谱的不开」.

  For every recent-sale chain that is fully OFF (from the 0914 sold-vs-status
  sweep): per instance print effective_status + issues_info (restriction
  reason) + week-to-date (Thu 9/10 →) spend / regs / CPL. Plus the current
  status + week numbers of the 0911 HOOK 重拍 wave (the successors)."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.monitor_cpl import _mkey, _week_start_thursday, result_action_type, extract_results
from adbot.settings import REPO_ROOT, load_settings
from adbot.commands import graph_client

DAYS = 14
TOKEN = result_action_type("COMPLETE_REGISTRATION")
HOOK_CAMP = "120248807549960575"     # 0911 HOOK 重拍 (MY)


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s_sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    week0 = _week_start_thursday(today)
    cutoff = today - dt.timedelta(days=DAYS)
    rng = {"since": week0.isoformat(), "until": today.isoformat()}
    print(f"CPL 窗口：{week0} → {today}（星期四起）\n")

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    recent = [x for x in sales if x.date and x.date >= cutoff]

    pool, wk = [], {}
    for label, st in (("MY", s_my), ("SG", s_sg)):
        g = graph_client(st)
        rows = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "id,name,effective_status,issues_info,"
                       "adset{name,effective_status},campaign{id,name,effective_status}",
             "limit": "500"})
        pool.extend((label, r) for r in rows)
        time.sleep(1.2)
        for r in g.account_insights(st.meta.account_path, level="ad",
                                    fields="ad_id,spend,actions", time_range=rng):
            try:
                wk[r.get("ad_id")] = (float(r.get("spend") or 0),
                                      extract_results(r.get("actions"), TOKEN))
            except (TypeError, ValueError):
                continue
        time.sleep(1.2)

    def wkstr(ad_id):
        sp, n = wk.get(ad_id, (0.0, 0.0))
        if sp < 1:
            return "本周没花钱"
        cpl = f"CPL {sp / n:.0f}" if n else "0 注册"
        return f"本周 RM{sp:.0f} / {n:.0f} reg / {cpl}"

    def issues(r):
        ii = r.get("issues_info") or []
        if not ii:
            return "无 restriction 记录"
        return "; ".join((i.get("error_summary") or i.get("error_message") or "?")[:60]
                         for i in ii[:2])

    chains = {}
    for x in recent:
        key = (_mkey(x.campaign), cpa.norm(x.ad))
        c = chains.setdefault(key, {"dates": [], "campaign": x.campaign, "ad": x.ad})
        c["dates"].append(x.date)

    print("═══ 死链深挖（近 14 天有成交、全部位置没在跑）═══")
    for key, c in sorted(chains.items(), key=lambda kv: max(kv[1]["dates"]), reverse=True):
        inst = [(lb, r) for lb, r in pool
                if _mkey((r.get("campaign") or {}).get("name") or "") == key[0]
                and cpa.norm(r.get("name") or "") == key[1]]
        how = "strict"
        if not inst:
            inst = [(lb, r) for lb, r in pool if cpa.norm(r.get("name") or "") == key[1]]
            how = "ad-name"
        if not inst:
            continue
        if any(r.get("effective_status") in
               ("ACTIVE", "PENDING_REVIEW", "IN_PROCESS", "PREAPPROVED", "LIMITED")
               for _lb, r in inst):
            continue                      # alive — not our subject
        dates = "、".join(d.strftime("%-m/%-d") for d in sorted(c["dates"]))
        print(f"\n◆ «{c['ad'][:32]}»  成交 {dates}  (match={how})")
        for lb, r in inst[:5]:
            camp = r.get("campaign") or {}
            print(f"   [{lb}] {r.get('effective_status'):<16} @ «{(camp.get('name') or '')[:38]}»")
            print(f"        {issues(r)} · {wkstr(r.get('id'))}")

    print("\n═══ 0911 HOOK 重拍（接班位）状态 ═══")
    g = graph_client(s_my)
    for r in g._get_all(f"{HOOK_CAMP}/ads",
                        {"fields": "id,name,effective_status,issues_info", "limit": "10"}):
        print(f"  {r.get('effective_status'):<16} «{(r.get('name') or '')[:36]}» · "
              f"{issues(r)} · {wkstr(r.get('id'))}")
    print("\nREOPEN ADVICE DATA DONE (read-only)")


if __name__ == "__main__":
    main()
