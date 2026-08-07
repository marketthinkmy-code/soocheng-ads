"""Read-only permission probe before any SG build.

Two facts we must KNOW (not guess) before creating campaigns on the SG account:
  1. Does this token hold MANAGE/ADVERTISE tasks on act_893025326577600 (=can it create
     campaigns there)?  -> read user_tasks + the /me/adaccounts tasks for that account.
  2. Where does the owner-linked campaign/adset/ad (12024819744409/10/11 0521) actually
     live?  -> read each object's account_id; if #10, it's outside this token's reach.
No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

SG = "act_893025326577600"
LINK_CAMP = "120248197444090521"
LINK_ADSET = "120248197444100521"
LINK_AD = "120248197444110521"


def probe(g, node: str, fields: str) -> None:
    try:
        obj = g.get_object(node, fields)
        print(f"  OK  {node} -> {obj}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ERR {node} -> {str(exc)[:120]}")


def main() -> None:
    g = graph_client(load_settings())

    print("=" * 80)
    print("1) TASK-LEVEL ACCESS on the SG account (can we create campaigns?)")
    print("=" * 80)
    probe(g, SG, "id,name,account_status,currency,user_tasks,capabilities")

    print("\n  /me/adaccounts tasks (the account's granted tasks for this system user):")
    try:
        accts = g._get_all("me/adaccounts",
                           {"fields": "account_id,name,account_status,tasks", "limit": "200"})
        for a in accts:
            aid = str(a.get("account_id") or "").replace("act_", "")
            mark = "  <-- SG DEST" if aid == SG.replace("act_", "") else ""
            print(f"    act_{aid:16} tasks={a.get('tasks')}  {a.get('name')}{mark}")
    except Exception as exc:  # noqa: BLE001
        print("    adaccounts read failed:", exc)

    print("\n" + "=" * 80)
    print("2) WHERE do the owner-linked objects actually live? (account_id)")
    print("=" * 80)
    probe(g, LINK_CAMP, "id,name,account_id,effective_status,objective")
    probe(g, LINK_ADSET, "id,name,account_id,campaign_id,effective_status")
    probe(g, LINK_AD, "id,name,account_id,adset_id,effective_status")

    print("\nDONE.")


if __name__ == "__main__":
    main()
