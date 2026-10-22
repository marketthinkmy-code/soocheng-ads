# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-22「看看最新成交纪录，复盘，告诉我 what's next」.

Paid Student List (and the tab the owner linked, gid 1805763216): sales since 2026-10-08, by day / account /
campaign / ad set / ad — with a Webinarkit split (campaign name contains «webinarkit», launched 10/17).
Joined to Meta spend + registrations of the Webinarkit window (10/17 → today) for CPA / ROAS, per campaign,
ad set and creative. Rows with a date but no UTM are counted (they're invisible to the CPA join).
Prints names, dates, counts and RM only — no buyer PII."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

SINCE = dt.date(2026, 10, 8)
WK = dt.date(2026, 10, 17)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
WIN = {"since": WK.isoformat(), "until": TODAY.isoformat()}
GID = 1805763216
ACCTS = (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml"))


def mk(x) -> str:
    c = x.campaign or ""
    if not (c or x.ad):
        return "无UTM"
    return "SG" if "[sg]" in c or " sg" in (x.adset or "") or "| sg" in c else "MY"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    sc = SheetsClient(s.secrets.google_sa_json)
    meta = sc._svc.spreadsheets().get(spreadsheetId=s.cpa.spreadsheet_id, fields="sheets.properties(sheetId,title)").execute()
    tabs = {p["properties"]["sheetId"]: p["properties"]["title"] for p in meta.get("sheets", [])}
    linked = tabs.get(GID, "?")
    print(f"tabs: {list(tabs.values())}\nowner 链接的 tab (gid {GID}) = «{linked}» · CPA 用的 tab = «{s.cpa.sales_tab}»")
    tab = linked if linked != "?" else s.cpa.sales_tab
    vals = sc.read_tab(s.cpa.spreadsheet_id, tab)
    sales, cols, header = cpa.parse_sales(vals, 2399.0)
    print(f"«{tab}» 栏位映射 {cols} · 表头: {[h for h in header][:30]}")
    # rows with a date but no UTM (parse_sales drops them)
    di = cols.get("date", -1)
    hidx = vals.index(header) if header in vals else 0
    no_utm = Counter()
    for row in vals[hidx + 1:]:
        d = cpa.parse_date(row[di]) if 0 <= di < len(row) else None
        c = row[cols["campaign"]] if 0 <= cols.get("campaign", -1) < len(row) else ""
        a = row[cols["ad"]] if 0 <= cols.get("ad", -1) < len(row) else ""
        if d and d >= SINCE and not (c.strip() or a.strip()):
            no_utm[d.isoformat()] += 1
    dated = [x for x in sales if x.date]
    print(f"rows {len(sales)} · 最新日期 {max(x.date for x in dated)} · 无日期 {len(sales) - len(dated)}")
    new = [x for x in dated if x.date >= SINCE]
    print(f"\n═══ {SINCE} 之后（有 UTM）：{len(new)} 笔 · RM{sum(x.amount for x in new):,.0f} · 另有无 UTM {sum(no_utm.values())} 笔 {dict(sorted(no_utm.items()))} ═══")
    print("  按日期: " + " · ".join(f"{d} {n}" for d, n in sorted(Counter(x.date.isoformat() for x in new).items())))
    wk = [x for x in new if "webinarkit" in (x.campaign or "")]
    print(f"  其中 Webinarkit campaign：{len(wk)} 笔 RM{sum(x.amount for x in wk):,.0f} · 按日期 "
          + " · ".join(f"{d} {n}" for d, n in sorted(Counter(x.date.isoformat() for x in wk).items())))
    for m in ("SG", "MY"):
        xs = [x for x in new if mk(x) == m]
        print(f"  {m}: {len(xs)} 笔 RM{sum(x.amount for x in xs):,.0f}")
    print("\n  每笔（日期 · 金额 · campaign / ad set / ad）:")
    for x in sorted(new, key=lambda x: x.date):
        print(f"    {x.date} RM{x.amount:,.0f} · {x.campaign[:55]} / {x.adset[:28]} / {x.ad[:34]}")

    for label, cfg in ACCTS:
        st = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        token = f"offsite_conversion.custom.{st.meta.custom_conversions[0]}" if st.meta.custom_conversions else result_action_type(st.meta.conversion_event)
        time.sleep(1.5)
        rows = g.account_insights(st.meta.account_path, level="ad",
                                  fields="campaign_name,adset_name,ad_name,spend,actions", time_range=WIN)
        rows = [r for r in rows if "webinarkit" in cpa.norm(r.get("campaign_name"))]
        tot_sp = sum(float(r.get("spend") or 0) for r in rows)
        tot_rg = sum(extract_results(r.get("actions"), token) for r in rows)
        mine = [x for x in new if x.date >= WK and mk(x) == ("SG" if label == "SG" else "MY")]
        mwk = [x for x in mine if "webinarkit" in (x.campaign or "")]
        rev = sum(x.amount for x in mwk)
        print(f"\n═══ {label} Webinarkit {WIN['since']}→{WIN['until']}：花 RM{tot_sp:,.0f} · 报名 {tot_rg:.0f} · CPL {tot_sp / tot_rg if tot_rg else 0:.0f} "
              f"· 成交 {len(mwk)} 笔 RM{rev:,.0f} · CPA {tot_sp / len(mwk) if mwk else 0:,.0f} · ROAS {rev / tot_sp if tot_sp else 0:.1f}x "
              f"（另 {len(mine) - len(mwk)} 笔 10/17 后成交挂在旧 campaign UTM）═══")
        for lvl, key in (("campaign", lambda r: cpa.norm(r.get("campaign_name"))),
                         ("ad set", lambda r: f"{cpa.norm(r.get('campaign_name'))[13:40]} › {cpa.norm(r.get('adset_name'))}"),
                         ("素材", lambda r: cpa.creative_key(r.get("ad_name")))):
            agg = defaultdict(lambda: [0.0, 0.0])
            for r in rows:
                k = key(r)
                agg[k][0] += float(r.get("spend") or 0); agg[k][1] += extract_results(r.get("actions"), token)
            if lvl == "campaign":
                sc_ = Counter(x.campaign for x in mwk)
            elif lvl == "ad set":
                sc_ = Counter(f"{x.campaign[13:40]} › {x.adset}" for x in mwk)
            else:
                sc_ = Counter(cpa.creative_key(x.ad) for x in mwk)
            print(f"\n  {lvl:<58} {'花费':>6} {'报名':>4} {'CPL':>5} {'成交':>4} {'CPA':>6}")
            for k, (sp, rg) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
                n = sc_.get(k, 0)
                if sp < 1 and not n:
                    continue
                print(f"  {k[:58]:<58} {sp:>6,.0f} {rg:>4.0f} {sp / rg if rg else 0:>5.0f} {n:>4} {sp / n if n else 0:>6,.0f}")
            miss = [k for k in sc_ if k not in agg]
            if miss:
                print("   成交但名字对不上 Meta：" + " | ".join(f"{k[:50]}×{sc_[k]}" for k in miss))
    print("\nSALES RECAP DONE (read-only)")


if __name__ == "__main__":
    main()
