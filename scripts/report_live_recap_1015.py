# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-15「成交 update 了，你看看，然后复盘」— the 14/10 live recap.

Paid Student List sales dated since 2026-09-26 (the sheet's previous last row was 09-25), split
SG / MY by utm_campaign, joined to Meta spend + registrations of the live funnel window
(2026-10-08 → 2026-10-15) per campaign / ad set / ad (strict name join, plus creative-only fallback).
Also: unattributed sales, sales by date, ROAS. Prints names, dates, counts and RM only — no buyer PII."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

SINCE = dt.date(2026, 9, 26)
WIN = {"since": "2026-10-08", "until": "2026-10-15"}
ACCTS = (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml"))


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(vals, 2399.0)
    dated = [x for x in sales if x.date]
    print(f"Paid Student List: {len(sales)} rows · 最新日期 {max(x.date for x in dated)} · 无日期 {len(sales) - len(dated)}")
    new = [x for x in dated if x.date >= SINCE]
    print(f"\n═══ {SINCE} 之后的成交：{len(new)} 笔 · RM{sum(x.amount for x in new):,.0f} ═══")
    by_day = Counter(x.date.isoformat() for x in new)
    print("  按日期: " + " · ".join(f"{d} {n}" for d, n in sorted(by_day.items())))
    mk = lambda x: "SG" if "[sg]" in (x.campaign or "") else ("无UTM" if not (x.campaign or x.ad) else "MY")
    for m in ("SG", "MY", "无UTM"):
        xs = [x for x in new if mk(x) == m]
        print(f"  {m}: {len(xs)} 笔 RM{sum(x.amount for x in xs):,.0f}")
    print("\n  campaign × 成交:")
    for c, n in Counter(x.campaign for x in new).most_common(25):
        print(f"    {n:>3}  {c[:70] or '(空)'}")
    print("\n  ad × 成交:")
    for a, n in Counter(x.ad for x in new).most_common(25):
        print(f"    {n:>3}  {a[:70] or '(空)'}")

    for label, cfg in ACCTS:
        st = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        token = result_action_type(st.meta.conversion_event)
        time.sleep(1.5)
        rows = g.account_insights(st.meta.account_path, level="ad",
                                  fields="campaign_name,adset_name,ad_name,spend,actions", time_range=WIN)
        tot_sp = sum(float(r.get("spend") or 0) for r in rows)
        tot_rg = sum(extract_results(r.get("actions"), token) for r in rows)
        mine = [x for x in new if mk(x) == ("SG" if label == "SG" else "MY")]
        rev = sum(x.amount for x in mine)
        print(f"\n═══ {label}：{WIN['since']}→{WIN['until']} 花费 RM{tot_sp:,.0f} · 报名 {tot_rg:.0f} · CPL {tot_sp / tot_rg if tot_rg else 0:.0f} "
              f"· 9/26 后成交 {len(mine)} 笔 RM{rev:,.0f} · CPA {tot_sp / len(mine) if mine else 0:,.0f} · ROAS {rev / tot_sp if tot_sp else 0:.1f}x ═══")
        sale_ca = Counter((x.campaign, x.ad) for x in mine)
        sale_c = Counter(x.campaign for x in mine)
        sale_a = Counter(cpa.creative_key(x.ad) for x in mine)
        camp = defaultdict(lambda: [0.0, 0.0])
        for r in rows:
            k = cpa.norm(r.get("campaign_name"))
            camp[k][0] += float(r.get("spend") or 0); camp[k][1] += extract_results(r.get("actions"), token)
        print(f"  {'campaign':<52} {'花费':>7} {'报名':>4} {'CPL':>5} {'成交':>4} {'CPA':>6}")
        for k, (sp, rg) in sorted(camp.items(), key=lambda kv: -kv[1][0]):
            if sp < 1 and not sale_c.get(k):
                continue
            n = sale_c.get(k, 0)
            print(f"  {k[:52]:<52} {sp:>7,.0f} {rg:>4.0f} {sp / rg if rg else 0:>5.0f} {n:>4} {sp / n if n else 0:>6,.0f}")
        unmatched = [c for c in sale_c if c not in camp]
        if unmatched:
            print("  成交 campaign 在这期间没有花费（旧位/别的账户/UTM 写法不同）：" + " | ".join(f"{c[:40]}×{sale_c[c]}" for c in unmatched))
        cre = defaultdict(lambda: [0.0, 0.0])
        for r in rows:
            k = cpa.creative_key(r.get("ad_name"))
            cre[k][0] += float(r.get("spend") or 0); cre[k][1] += extract_results(r.get("actions"), token)
        print(f"\n  {'素材（跨 campaign 合并）':<44} {'花费':>7} {'报名':>4} {'CPL':>5} {'成交':>4} {'CPA':>6}")
        for k, (sp, rg) in sorted(cre.items(), key=lambda kv: -kv[1][0]):
            n = sale_a.get(k, 0)
            if sp < 1 and not n:
                continue
            print(f"  {k[:44]:<44} {sp:>7,.0f} {rg:>4.0f} {sp / rg if rg else 0:>5.0f} {n:>4} {sp / n if n else 0:>6,.0f}")
        print("  成交 (campaign, ad)：" + " | ".join(f"{c[:28]} / {a[:24]}×{n}" for (c, a), n in sale_ca.most_common(12)))
    print("\nLIVE RECAP DONE (read-only)")


if __name__ == "__main__":
    main()
