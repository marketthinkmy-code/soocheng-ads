"""Read-only ad-level snapshot for the daily routine — BOTH accounts (MY + SG).

Prints, per account:
  · every ad's last_3d spend / registrations / CPL + live effective_status + created_time
  · campaign-level last_3d roll-up, plus each campaign's status, created_time and 60d spend

Nothing is written to Meta. Registrations are reported two ways so the routine can cross-check
the nightly report: `reg` = the exact optimized-event bucket the monitor uses (= Ads Manager
"Results"), `omni` = omni_complete_registration.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]


def _cpl(spend: float, regs: float) -> str:
    if regs > 0:
        return f"RM{spend / regs:6.1f}"
    return "     ∞" if spend > 0 else "      -"


def _omni(actions) -> float:
    total = 0.0
    for a in actions or []:
        if a.get("action_type") == "omni_complete_registration":
            total += float(a.get("value") or 0)
    return total


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    token = result_action_type(s.meta.conversion_event)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    print(f"snapshot generated (MYT) {today}  ·  reg bucket = {token}")

    for label, acct in ACCTS:
        print("\n" + "=" * 100)
        print(f"ACCOUNT {label}  {acct}")
        print("=" * 100)

        # ── live entity meta (status + created_time) ──────────────────────────
        ad_meta, camp_meta = {}, {}
        try:
            for a in g._get_all(f"{acct}/ads", {
                    "fields": "id,name,effective_status,created_time,campaign{name},adset{name}",
                    "limit": "500"}):
                ad_meta[a["id"]] = a
            for c in g._get_all(f"{acct}/campaigns", {
                    "fields": "id,name,effective_status,created_time,daily_budget",
                    "limit": "300"}):
                camp_meta[c["id"]] = c
        except GraphError as e:
            print(f"  ⚠ entity read failed: {e}")

        # ── last_3d ad-level insights ────────────────────────────────────────
        try:
            rows = g._get_all(f"{acct}/insights", {
                "level": "ad",
                "fields": "ad_id,ad_name,campaign_id,campaign_name,adset_name,spend,actions",
                "date_preset": "last_3d", "limit": "500"})
        except GraphError as e:
            print(f"  ⚠ last_3d insights failed: {e}")
            rows = []

        by_camp = defaultdict(lambda: [0.0, 0.0, 0.0])
        print(f"\n-- ADS · last_3d ({len(rows)} rows with delivery) --")
        print(f"  {'spend':>9} {'reg':>4} {'omni':>5} {'CPL':>8}  {'status':<18} {'created':<10} ad / adset / campaign")
        for r in sorted(rows, key=lambda r: -float(r.get("spend") or 0)):
            sp = float(r.get("spend") or 0)
            rg = extract_results(r.get("actions"), token)
            om = _omni(r.get("actions"))
            m = ad_meta.get(r.get("ad_id"), {})
            st = m.get("effective_status", "?")
            created = (m.get("created_time") or "")[:10]
            c = by_camp[r.get("campaign_name", "?")]
            c[0] += sp
            c[1] += rg
            c[2] += om
            print(f"  RM{sp:8.2f} {rg:4.0f} {om:5.0f} {_cpl(sp, rg)}  {st:<18} {created:<10} "
                  f"«{r.get('ad_name','?')[:42]}» / {r.get('adset_name','?')[:26]} / {r.get('campaign_name','?')[:34]}")

        print(f"\n-- CAMPAIGNS · last_3d roll-up --")
        for name, (sp, rg, om) in sorted(by_camp.items(), key=lambda kv: -kv[1][0]):
            print(f"  RM{sp:8.2f} {rg:4.0f} reg {om:4.0f} omni  CPL {_cpl(sp, rg)}  {name[:60]}")

        # ── every campaign: status, created, 60d spend ───────────────────────
        try:
            spend60 = {r.get("campaign_id"): float(r.get("spend") or 0)
                       for r in g._get_all(f"{acct}/insights", {
                           "level": "campaign", "fields": "campaign_id,campaign_name,spend",
                           "date_preset": "last_90d", "limit": "300"})}
        except GraphError as e:
            print(f"  ⚠ 90d campaign spend failed: {e}")
            spend60 = {}

        print(f"\n-- CAMPAIGNS · status / created / 90d spend --")
        for cid, c in sorted(camp_meta.items(), key=lambda kv: -spend60.get(kv[0], 0)):
            created = (c.get("created_time") or "")[:10]
            age = ""
            if created:
                try:
                    age = f"{(today - dt.date.fromisoformat(created)).days}d"
                except ValueError:
                    age = ""
            budget = c.get("daily_budget")
            budget_s = f"RM{int(budget)/100:.0f}/day" if budget else "-"
            print(f"  RM{spend60.get(cid, 0):9.2f} 90d  {c.get('effective_status','?'):<16} "
                  f"created {created} ({age:>4})  {budget_s:>10}  {c.get('name','?')[:56]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
