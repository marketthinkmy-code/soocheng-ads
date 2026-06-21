"""Daily whole-account performance report (read-only), emitted as Markdown on stdout.

Posted by the adbot-daily-report workflow to the "Daily Ads Report" tracking issue at
~22:00 MYT. Shows today's spend/CPL per campaign plus the monitor's current over-ceiling
watchlist (the ads the hourly monitor would pause), so the owner can track performance
without having to ask.
"""
from __future__ import annotations

import datetime as dt
import math

from adbot.clients.graph import GraphClient
from adbot.monitor_cpl import evaluate_account, extract_results, result_action_type
from adbot.settings import load_settings


def _cpl(spend: float, reg: float) -> str:
    if reg > 0:
        return f"RM{spend / reg:.1f}"
    return "∞" if spend else "—"


def _sort_key(spend: float, reg: float) -> float:
    return spend / reg if reg else (math.inf if spend else 0.0)


def main() -> None:
    s = load_settings()
    g = GraphClient(s.secrets.meta_token, "")  # unsigned read; app doesn't enforce proof
    acct = s.meta.account_path
    reg_token = result_action_type(s.meta.conversion_event)
    ceiling = s.kpi.cpl_threshold_myr
    myt = dt.datetime.utcnow() + dt.timedelta(hours=8)  # Asia/Kuala_Lumpur, no DST

    # ── today, per active campaign ──────────────────────────────────────────────
    camps = [c for c in g.list_campaigns(acct) if c.get("effective_status") == "ACTIVE"]
    rows, tot_spend, tot_reg = [], 0.0, 0.0
    for c in camps:
        ins = g._get_all(f"{c['id']}/insights",
                         {"fields": "spend,actions", "date_preset": "today", "limit": 1})
        spend = float(ins[0].get("spend", 0)) if ins else 0.0
        reg = extract_results(ins[0].get("actions") if ins else None, reg_token)
        rows.append((c["name"], spend, reg))
        tot_spend, tot_reg = tot_spend + spend, tot_reg + reg
    rows.sort(key=lambda r: -_sort_key(r[1], r[2]))

    # ── monitor watchlist: ads it would pause right now (per-ad, last 3 days) ────
    over = [d for d in evaluate_account(g, s) if d.should_pause]
    over.sort(key=lambda d: -(d.cpl if d.cpl and d.cpl != math.inf else math.inf))

    # ── render markdown ─────────────────────────────────────────────────────────
    out = [
        f"## 📊 Daily Ads Report — {myt:%a %d %b %Y}",
        f"_Whole account (MTC + STOCKBLOOM) · generated {myt:%H:%M} MYT · ceiling RM{ceiling:.0f}_",
        "",
        f"**Today:** RM{tot_spend:,.0f} spend · {tot_reg:.0f} regs · "
        f"blended CPL **{_cpl(tot_spend, tot_reg)}**",
        "",
        "| Campaign | Spend | Reg | CPL |",
        "|---|--:|--:|--:|",
    ]
    for name, spend, reg in rows:
        out.append(f"| {name[:42]} | RM{spend:,.0f} | {reg:.0f} | {_cpl(spend, reg)} |")
    out.append("")

    if over:
        out.append(f"### ⚠️ Over ceiling — monitor would pause {len(over)} ad(s) _(last 3 days)_")
        for d in over:
            c = "∞" if (d.cpl is None or d.cpl == math.inf) else f"RM{d.cpl:.1f}"
            out.append(f"- **{d.name[:55]}** — CPL {c} · RM{d.spend:,.0f} spent · {d.results:.0f} reg")
    else:
        out.append(f"### ✅ All active ads within RM{ceiling:.0f} — nothing to pause")

    out += ["", "_Auto-generated daily. Reply here or ping me to act on anything._",
            "", "cc @marketthinkmy-code"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
