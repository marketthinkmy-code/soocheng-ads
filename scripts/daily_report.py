"""Daily whole-account performance report (read-only), emitted as rich Markdown.

Designed for the GitHub-issue + mobile-email view: colour comes from shields.io
badges and 🟢/🟡/🔴 status dots, layout is card-style (no wide tables, which reflow
badly on phones). render_report() is a pure function so the look can be previewed
and unit-tested without hitting the API.
"""
from __future__ import annotations

import datetime as dt
import math
import re
from urllib.parse import quote

from adbot.commands import graph_client
from adbot.monitor_cpl import (MANUAL_HOLD, evaluate_account, extract_results,
                               result_action_type)
from adbot.settings import load_settings


def _cpl(spend: float, reg: float):
    if reg > 0:
        return spend / reg
    return math.inf if spend > 0 else None


def _tier(cpl, ceiling: float):
    """(status dot, shields colour) for a CPL against the ceiling."""
    if cpl is None:
        return "⚪", "lightgrey"
    if cpl == math.inf:
        return "🔴", "red"
    ratio = cpl / ceiling
    if ratio <= 0.85:
        return "🟢", "brightgreen"
    if ratio <= 1.0:
        return "🟢", "green"
    if ratio <= 1.25:
        return "🟡", "orange"
    return "🔴", "red"


def _cpl_text(cpl) -> str:
    if cpl is None:
        return "—"
    if cpl == math.inf:
        return "∞"
    return f"RM{cpl:.1f}"


def _badge(label: str, message: str, color: str) -> str:
    lab, msg = quote(str(label), safe=""), quote(str(message), safe="")
    return f"![{label}](https://img.shields.io/badge/{lab}-{msg}-{color})"


def _short(name: str) -> str:
    """Trim a trailing ' - d/m/yyyy' date so campaign names read cleanly."""
    return re.sub(r"\s*-\s*\d+/\d+/\d+\s*$", "", name).strip()


def render_report(now_myt: dt.datetime, rows, decisions, ceiling: float) -> str:
    tot_spend = sum(r[1] for r in rows)
    tot_reg = sum(r[2] for r in rows)
    blended = _cpl(tot_spend, tot_reg)
    _, bcolor = _tier(blended, ceiling)
    over_ceiling = blended is not None and blended != math.inf and blended > ceiling

    out = [
        "# 📊 Daily Ads Report",
        f"### {now_myt:%a %d %b %Y} · {now_myt:%H:%M} MYT",
        f"Whole account · MTC + STOCKBLOOM · ceiling RM{ceiling:.0f}",
        "",
        " &nbsp; ".join([
            _badge("Spend", f"RM{tot_spend:,.0f}", "0969da"),
            _badge("Regs", f"{tot_reg:.0f}", "8250df"),
            _badge("Blended CPL", _cpl_text(blended), bcolor),
        ]),
        "",
        "> [!WARNING]" if over_ceiling else "> [!TIP]",
        (f"> Blended CPL **{_cpl_text(blended)}** is over the RM{ceiling:.0f} ceiling today."
         if over_ceiling else
         f"> Blended CPL **{_cpl_text(blended)}** is within the RM{ceiling:.0f} ceiling. ✅"),
        "",
        "## 🏆 Campaigns · best → worst",
        "",
    ]
    for name, spend, reg in sorted(rows, key=lambda r: (lambda c: math.inf if c is None else c)(_cpl(r[1], r[2]))):
        cpl = _cpl(spend, reg)
        dot, color = _tier(cpl, ceiling)
        out.append(f"{dot} **{_short(name)}** &nbsp; {_badge('CPL', _cpl_text(cpl), color)}"
                   f" &nbsp; <sub>RM{spend:,.0f} · {reg:.0f} reg</sub>")
    out.append("")

    over = [d for d in decisions if d.cpl is not None and (d.cpl == math.inf or d.cpl > ceiling)]
    held = [d for d in over if d.reason == MANUAL_HOLD]
    to_pause = [d for d in over if d.should_pause]
    out += ["## ⚠️ Over ceiling · monitor watchlist _(last 3 days)_", ""]
    if not over:
        out += ["> [!TIP]", "> No ads over the ceiling — nothing to pause. ✅", ""]
    else:
        out += [f"> [!{'CAUTION' if to_pause else 'NOTE'}]",
                f"> **{len(over)}** ad(s) over RM{ceiling:.0f} — 🔒 {len(held)} held · "
                f"✂️ {len(to_pause)} to auto-pause.", ""]
        for d in sorted(over, key=lambda x: -(x.cpl if x.cpl != math.inf else 1e9)):
            held_one = d.reason == MANUAL_HOLD
            icon = "🔒" if held_one else ("✂️" if d.should_pause else "👀")
            note = "held by you" if held_one else ("would auto-pause" if d.should_pause else "watch")
            _, color = _tier(d.cpl, ceiling)
            out.append(f"- {icon} **{d.name[:48]}** &nbsp; {_badge('CPL', _cpl_text(d.cpl), color)}"
                       f" &nbsp; <sub>{note}</sub>")
        out.append("")

    out += ["---",
            "<sub>🤖 Auto-generated daily · reply here or ping me to act · cc @marketthinkmy-code</sub>"]
    return "\n".join(out)


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    reg_token = result_action_type(s.meta.conversion_event)
    ceiling = s.kpi.cpl_threshold_myr
    now_myt = dt.datetime.utcnow() + dt.timedelta(hours=8)  # Asia/Kuala_Lumpur, no DST

    rows = []
    for c in g.list_campaigns(acct):
        if c.get("effective_status") != "ACTIVE":
            continue
        ins = g._get_all(f"{c['id']}/insights",
                         {"fields": "spend,actions", "date_preset": "today", "limit": 1})
        spend = float(ins[0].get("spend", 0)) if ins else 0.0
        reg = extract_results(ins[0].get("actions") if ins else None, reg_token)
        rows.append((c["name"], spend, reg))

    print(render_report(now_myt, rows, evaluate_account(g, s), ceiling))


if __name__ == "__main__":
    main()
