"""Read-only: which system user is this token, and EXACTLY which ad accounts +
pixels it can see (id ↔ name). Resolves which account is 759339046918885.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          9: "IN_GRACE_PERIOD", 101: "CLOSED"}
TARGET = "759339046918885"


def main() -> None:
    g = graph_client(load_settings())
    try:
        me = g.get_object("me", "id,name")
        print(f"TOKEN identity: id={me.get('id')} name={me.get('name')}")
    except Exception as exc:  # noqa: BLE001
        print("me read failed:", exc)

    print("\nAD ACCOUNTS visible to this token:")
    try:
        accts = g._get_all("me/adaccounts",
                           {"fields": "id,account_id,name,account_status,currency", "limit": "200"})
        for a in accts:
            aid = str(a.get("account_id") or a.get("id", "")).replace("act_", "")
            star = "  ⭐ THIS IS 759339046918885" if aid == TARGET else ""
            st = a.get("account_status")
            print(f"  act_{aid:16} {STATUS.get(st, st):>8}  {a.get('currency','?'):>4}  "
                  f"{a.get('name')}{star}")
        if not any(str(a.get('account_id') or a.get('id','')).replace('act_','') == TARGET for a in accts):
            print(f"\n  ⚠ {TARGET} is NOT in this token's visible accounts — not assigned to this system user.")
    except Exception as exc:  # noqa: BLE001
        print("  adaccounts read failed:", exc)

    print("\nPIXELS visible via the business (for the new account's conversion tracking):")
    try:
        # pixels are listed per-account; try the target then fall back to any visible account
        for probe in (f"act_{TARGET}",):
            try:
                px = g._get_all(f"{probe}/adspixels", {"fields": "id,name", "limit": "50"})
                for p in px:
                    print(f"  [{probe}] pixel {p.get('id')}  {p.get('name')}")
            except Exception as exc:  # noqa: BLE001
                print(f"  [{probe}] pixel read failed: {str(exc)[:80]}")
    except Exception as exc:  # noqa: BLE001
        print("  pixel probe failed:", exc)

    print("\nDONE.")


if __name__ == "__main__":
    main()
