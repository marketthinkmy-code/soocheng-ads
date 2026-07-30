# -*- coding: utf-8 -*-
"""新主题 vs 老将 — weekly CPA comparison report (read-only, emitted as Markdown).

新主题 = the campaigns launched 2026-07-30 (TRAVEL TOP3 / BEER ALCOHOL / DAY TRADING, on both
accounts). 老将 = every other campaign with spend in the window. Window = last DAYS days
(default 7), same window for both groups so the comparison is fair.

Joins live Meta spend/registrations (per campaign, both accounts) with real buyers from the
Paid Student List (utm_campaign match). Judged the owner's way: CPL is context, CPA decides.
"""
from __future__ import annotations

import datetime as dt
import math
import os
from collections import defaultdict

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

DAYS = int(os.environ.get("DAYS", "7"))
NEW_MARKERS = ("TRAVEL TOP3", "BEER ALCOHOL", "DAY TRADING")
ACCTS = [("SG", "act_893025326577600"), ("MY", "act_759339046918885")]
PRICE = 2399.0


def is_new(name: str) -> bool:
    return any(m in (name or "").upper() for m in NEW_MARKERS)


def cpa_text(v) -> str:
    if v is None:
        return "—"
    return "∞" if v == math.inf else f"RM{v:,.0f}"


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    reg_token = result_action_type(s.meta.conversion_event)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    since = today - dt.timedelta(days=DAYS)

    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _cols, _hdr = C.parse_sales(vals, PRICE)
    buyers = defaultdict(int)
    for x in sales:
        if x.date and x.date > since and x.campaign:
            buyers[x.campaign] += 1

    rows = []  # (group, acct_label, name, spend, regs, buyers)
    for label, acct in ACCTS:
        for r in g.account_insights(acct, level="campaign",
                                    fields="campaign_name,spend,actions",
                                    time_range={"since": since.isoformat(),
                                                "until": today.isoformat()}):
            name = r.get("campaign_name", "")
            spend = float(r.get("spend") or 0)
            reg = extract_results(r.get("actions"), reg_token)
            b = buyers.get(C.norm(name), 0)
            if spend <= 0 and b == 0:
                continue
            rows.append(("新主题" if is_new(name) else "老将", label, name, spend, reg, b))

    out = [
        "# 📊 新主题 vs 老将 · CPA 对比",
        f"{today:%a %d %b %Y} · window last {DAYS}d ({since} → {today}) · both accounts",
        "",
    ]
    for grp in ("新主题", "老将"):
        gr = [r for r in rows if r[0] == grp]
        sp = sum(r[3] for r in gr)
        rg = sum(r[4] for r in gr)
        by = sum(r[5] for r in gr)
        gcpa = C.cpa(sp, by)
        cpl = (sp / rg) if rg else None
        roas = (by * PRICE / sp) if sp else 0
        out += [
            f"## {'🆕' if grp == '新主题' else '🏆'} {grp} — RM{sp:,.0f} spend · {rg} reg "
            f"(CPL {cpa_text(cpl)}) · **{by} buyers · CPA {cpa_text(gcpa)}** · est ROAS {roas:.1f}x",
            "",
        ]
        for _g, label, name, spend, reg, b in sorted(gr, key=lambda r: (-r[5], -r[3])):
            cpl_c = (spend / reg) if reg else None
            out.append(f"- [{label}] {name} · RM{spend:,.0f} · {reg} reg (CPL {cpa_text(cpl_c)}) · "
                       f"**{b} buyers (CPA {cpa_text(C.cpa(spend, b))})**")
        out.append("")

    out += [
        "---",
        f"<sub>⚠️ 报名→成交平均要 {s.cpa.conversion_days} 天：新主题的 CPA 在首个对比里天然偏保守，"
        "还有一批报名在转化路上 — 连续两周对比后再下结论。判断口径：CPL 是过程，CPA 定生死。"
        "🤖 Auto-generated weekly (Thu 10:07 MYT) · cc @marketthinkmy-code</sub>",
    ]
    print("\n".join(out))


if __name__ == "__main__":
    main()
