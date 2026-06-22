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
import sys
from urllib.parse import quote

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import (MANUAL_HOLD, _mkey, evaluate_account, extract_results,
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


def _cpa_text(c) -> str:
    if c is None:
        return "—"
    return "∞" if c == math.inf else f"RM{c:,.0f}"


def _cpa_dot(c, tiers):
    """(status dot, shields colour) for a CPA against the tiers."""
    if c is None:
        return "⚪", "lightgrey"
    if c == math.inf:
        return "🔴", "red"
    if c <= tiers.healthy_max:
        return "🟢", "brightgreen"
    if c <= tiers.max_acceptable:
        return "🟡", "yellow"
    if c <= tiers.hard_stop:
        return "🟠", "orange"
    return "🔴", "red"


def cpa_money_map(graph, settings, today):
    """Per-campaign 60-day CPA (display, spend60, sales60, cpa) + blended, joined by UTM name."""
    from adbot.clients.sheets import SheetsClient
    values = SheetsClient(settings.secrets.google_sa_json).read_tab(
        settings.cpa.spreadsheet_id, settings.cpa.sales_tab)
    sales, _cols, _hdr = cpa.parse_sales(values, settings.cpa.price_myr)
    _by_ad, _by_adset, by_campaign = cpa.attribute(sales, today)
    since, until = (today - dt.timedelta(days=60)).isoformat(), today.isoformat()
    spend = {}
    for r in graph.account_insights(settings.meta.account_path, level="campaign",
                                    fields="campaign_name,spend",
                                    time_range={"since": since, "until": until}):
        try:
            spend[_mkey(r.get("campaign_name", ""))] = (r.get("campaign_name", ""), float(r.get("spend") or 0))
        except (TypeError, ValueError):
            continue
    rows = []
    for k in set(by_campaign) | set(spend):
        disp = spend.get(k, (k, 0))[0] or k
        sp = spend.get(k, (None, 0.0))[1]
        sa = by_campaign.get(k, {}).get("60d", 0)
        if sp <= 0 and sa == 0:
            continue
        rows.append((disp, sp, sa, cpa.cpa(sp, sa)))
    rows.sort(key=lambda r: -(r[1] or 0))
    tot_sp, tot_sa = sum(r[1] for r in rows), sum(r[2] for r in rows)
    return rows, cpa.cpa(tot_sp, tot_sa)


def render_report(now_myt: dt.datetime, rows, decisions, ceiling: float,
                  cpa_rows=None, blended_cpa=None, cpa_tiers=None) -> str:
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

    if cpa_rows is not None and cpa_tiers is not None:
        _, bcol = _cpa_dot(blended_cpa, cpa_tiers)
        out += ["## 💰 Real-sales CPA · last 60 days",
                f"From the Paid Student List · target RM{cpa_tiers.healthy_max:.0f} · "
                f"hard-stop RM{cpa_tiers.hard_stop:.0f}",
                "",
                _badge("Blended CPA", _cpa_text(blended_cpa), bcol),
                ""]
        for disp, sp, sa, c in cpa_rows[:12]:
            dot, color = _cpa_dot(c, cpa_tiers)
            out.append(f"{dot} **{_short(disp)}** &nbsp; {_badge('CPA', _cpa_text(c), color)}"
                       f" &nbsp; <sub>RM{sp:,.0f} · {sa:.0f} sale</sub>")

        cut = [d for d in decisions if d.reason == cpa.HARD_STOP]
        rescued = [d for d in decisions if d.reason == cpa.CPL_RESCUED]
        out += ["", "### CPA decisions _(folded into the monitor)_", ""]
        if not cut and not rescued:
            out += ["> [!TIP]", "> CPA and CPL agree today — no overrides. ✅", ""]
        else:
            for d in cut:
                out.append(f"- ✂️ **{d.name[:46]}** &nbsp; <sub>CPA {_cpa_text(d.cpa)} on "
                           f"{d.cpa_sales} sale · auto-paused (over hard-stop)</sub>")
            for d in rescued:
                out.append(f"- 🛟 **{d.name[:46]}** &nbsp; <sub>CPA {_cpa_text(d.cpa)} on "
                           f"{d.cpa_sales} sale · kept despite high CPL</sub>")
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

    decisions = evaluate_account(g, s)

    cpa_rows = blended_cpa = tiers = None
    if s.cpa.enabled:
        try:  # the report must never fail on the CPA add-on
            tiers = cpa.CpaTiers(s.cpa.healthy_max_myr, s.cpa.max_acceptable_myr, s.cpa.hard_stop_myr)
            cpa_rows, blended_cpa = cpa_money_map(g, s, now_myt.date())
        except Exception as exc:  # noqa: BLE001
            print(f"<!-- CPA section skipped: {type(exc).__name__}: {exc} -->", file=sys.stderr)
            cpa_rows = tiers = None

    print(render_report(now_myt, rows, decisions, ceiling, cpa_rows, blended_cpa, tiers))


if __name__ == "__main__":
    main()
