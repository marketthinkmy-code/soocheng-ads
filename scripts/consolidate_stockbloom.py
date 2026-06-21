"""Owner-chosen consolidation: pause STOCKBLOOM #1 entirely and move its daily
budget into STOCKBLOOM #2 (the lower-CPL winner). Total daily spend unchanged.
Run: python scripts/consolidate_stockbloom.py
"""
from __future__ import annotations

from adbot import state
from adbot.commands import graph_client
from adbot.settings import load_settings

C1 = "120245365310000688"  # STOCKBLOOM | 1-1-10        (pause)
C2 = "120245370911930688"  # STOCKBLOOM | 1-1-10 #2     (receive budget)


def main() -> None:
    g = graph_client(load_settings())

    c1 = g.get_object(C1, "name,daily_budget,configured_status")
    c2 = g.get_object(C2, "name,daily_budget,configured_status")
    b1 = int(c1.get("daily_budget") or 0)
    b2 = int(c2.get("daily_budget") or 0)
    new_b2 = b1 + b2
    print(f"#1 {c1.get('name')}: {c1.get('configured_status')} @ RM{b1/100:.2f}/day")
    print(f"#2 {c2.get('name')}: {c2.get('configured_status')} @ RM{b2/100:.2f}/day")
    print(f"-> move RM{b1/100:.2f} into #2; #2 new budget RM{new_b2/100:.2f}/day; #1 paused\n")

    # 1) grow #2 first (so total delivery never dips below target during the switch)
    g._request("POST", C2, data={"daily_budget": new_b2})
    # 2) pause #1 entirely
    if c1.get("configured_status") == "ACTIVE":
        g.update_status(C1, "PAUSED")
        state.append_pause_log(C1, "campaign", "consolidate_into_c2",
                               {"moved_budget_myr": b1 / 100, "c2_new_budget_myr": new_b2 / 100})

    # verify
    v1 = g.get_object(C1, "configured_status")
    v2 = g.get_object(C2, "daily_budget,configured_status")
    print(f"VERIFY #1: configured_status={v1.get('configured_status')}")
    print(f"VERIFY #2: configured_status={v2.get('configured_status')} "
          f"daily_budget=RM{int(v2.get('daily_budget') or 0)/100:.2f}/day")


if __name__ == "__main__":
    main()
