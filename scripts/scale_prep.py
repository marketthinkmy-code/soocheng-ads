"""Prep for scaling (read-only):
 1) reusable post ids for the champion creatives to inject (freestyle 1 / 盖电脑 / 我跟你讲),
 2) the 3 MY interest campaigns' adsets + current ad names (so injection doesn't duplicate),
 3) both accounts' ACTIVE campaigns with daily_budget + last-7d spend/results/CPL (to pick CBO raises).
No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

MY = "act_759339046918885"
SG = "act_893025326577600"
TOKEN = result_action_type("COMPLETE_REGISTRATION")
CHAMPS = ["freestyle 1", "盖电脑", "我跟你讲"]     # ad-name substrings
MY_INTEREST = ["120247585340620575", "120247585352100575", "120247585357770575"]  # Luxury/BizOwner/Investment


def main() -> None:
    g = graph_client(load_settings())

    print("=== champion reusable post ids (first match per creative) ===")
    seen: dict = {}
    for label, acct in [("MY", MY), ("SG", SG)]:
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,creative{effective_object_story_id,"
                          "object_story_id,video_id}", "limit": "800"})
        for a in ads:
            nm = a.get("name", "")
            for c in CHAMPS:
                if c in nm and c not in seen:
                    cr = a.get("creative") or {}
                    post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                    if post:
                        seen[c] = (post, label, a.get("effective_status"), nm)
    for c in CHAMPS:
        print(f"  {c:12} -> {seen.get(c)}")

    print("\n=== MY interest campaigns: adsets + current ads ===")
    for camp in MY_INTEREST:
        info = g.get_object(camp, "name,daily_budget,effective_status")
        print(f"  camp {camp} «{info.get('name')}»  budget={info.get('daily_budget')}  {info.get('effective_status')}")
        for aset in g._get_all(f"{camp}/adsets", {"fields": "id,name", "limit": "20"}):
            ads = g._get_all(f"{aset['id']}/ads", {"fields": "name,effective_status", "limit": "50"})
            print(f"    adset {aset['id']} «{aset.get('name')}»")
            for a in ads:
                print(f"        - [{a.get('effective_status')}] {a.get('name')}")

    for label, acct in [("MY", MY), ("SG", SG)]:
        print(f"\n=== {label} ACTIVE campaigns · budget · last-7d spend/results/CPL ===")
        ins = {r.get("campaign_id"): r for r in g.account_insights(
            acct, level="campaign", fields="campaign_id,spend,actions", date_preset="last_7d")}
        rows = []
        for c in g._get_all(f"{acct}/campaigns",
                            {"fields": "id,name,daily_budget,effective_status", "limit": "150"}):
            if c.get("effective_status") != "ACTIVE":
                continue
            r = ins.get(c["id"]) or {}
            try:
                sp = float(r.get("spend") or 0)
            except (TypeError, ValueError):
                sp = 0.0
            res = extract_results(r.get("actions"), TOKEN)
            bud = c.get("daily_budget")
            rows.append((res, sp / res if res > 0 else None, sp, bud, c["id"], c.get("name", "")))
        rows.sort(key=lambda x: (-x[0], x[1] if x[1] is not None else 9e9))
        for res, cpl, sp, bud, cid, nm in rows:
            b = f"RM{int(bud)/100:.0f}/d" if bud else "adset-bud"
            cpls = f"{cpl:5.1f}" if cpl is not None else "  -  "
            print(f"    {res:3.0f} res  CPL{cpls}  7d RM{sp:5.0f}  {b:>9}  {cid}  {nm[:40]}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
