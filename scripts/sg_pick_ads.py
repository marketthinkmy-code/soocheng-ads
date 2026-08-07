"""Read-only: rank the currently-ACTIVE ads (accounts 3.0 + 4.0) by CPL (cost per
COMPLETE_REGISTRATION), with each ad's reusable post id — so we can pick the best 3
to drop into the SG RUNNING ad set. Uses the monitor's exact result bucket. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

ACCTS = ["act_759339046918885", "act_1263100565619799"]   # 3.0, 4.0
EVENT = "COMPLETE_REGISTRATION"


def main() -> None:
    g = graph_client(load_settings())
    token = result_action_type(EVENT)

    for acct in ACCTS:
        try:
            ins = {r.get("ad_id"): r for r in g.account_insights(
                acct, level="ad", fields="ad_id,spend,actions", date_preset="maximum")}
        except Exception as exc:  # noqa: BLE001
            print(f"\n=== {acct}: insights failed {str(exc)[:60]} ===")
            continue
        try:
            ads = g._get_all(f"{acct}/ads", {
                "fields": "id,name,effective_status,creative{effective_object_story_id,"
                          "object_story_id,image_hash,video_id}", "limit": "400"})
        except Exception as exc:  # noqa: BLE001
            print(f"\n=== {acct}: ads failed {str(exc)[:60]} ===")
            continue

        rows = []
        for a in ads:
            if a.get("effective_status") != "ACTIVE":
                continue
            r = ins.get(a["id"]) or {}
            try:
                spend = float(r.get("spend") or 0)
            except (TypeError, ValueError):
                spend = 0.0
            regs = extract_results(r.get("actions"), token)
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            kind = "vid" if cr.get("video_id") else ("img" if cr.get("image_hash") else "?")
            rows.append((spend / regs if regs > 0 else None, spend, regs, a.get("name", ""),
                         post, kind, a["id"]))

        withreg = sorted([x for x in rows if x[0] is not None], key=lambda x: x[0])
        noreg = sorted([x for x in rows if x[0] is None and x[1] > 0],
                       key=lambda x: -x[1])
        print(f"\n{'='*90}\n{acct} — {len(rows)} ACTIVE ads · {len(withreg)} with ≥1 registration\n{'='*90}")
        print("  CPL(RM)  reg  spend   type  post_id                         name")
        for cpl, spend, regs, name, post, kind, adid in withreg:
            print(f"  {cpl:7.1f}  {regs:3.0f}  {spend:6.0f}  {kind:>4}  {str(post):30}  {name[:44]}")
        if noreg:
            print(f"  -- spent but 0 reg (skip): "
                  + " · ".join(f"{n[3][:22]}(RM{n[1]:.0f})" for n in noreg[:8]))

    print("\nDONE.")


if __name__ == "__main__":
    main()
