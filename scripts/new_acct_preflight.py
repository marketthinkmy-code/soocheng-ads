"""Read-only preflight for the NEW ad account act_759339046918885 (business 769016565904540).
Confirms token access + account status + currency, lists pixels, checks the Page is
readable, and verifies each proven post id is reachable (so object_story_id ads will work).
No writes. Every check degrades to a printed error instead of crashing.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

NEW = "act_759339046918885"
BUSINESS = "769016565904540"
PAGE = "1001334883061622"

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          9: "IN_GRACE_PERIOD", 101: "CLOSED"}

POSTS = [
    ("freestyle 1", "1001334883061622_122097411579286543"),
    ("video 5：盖电脑，喂！", "1001334883061622_1788611461813837"),
    ("video 6：街头突击采访！", "1001334883061622_122108595957286543"),
    ("video 6：我跟你讲！", "1001334883061622_4377635152552494"),
    ("freestyle: korea", "1001334883061622_122109881127286543"),
    ("video 2：你敢吗？", "1001334883061622_122109020937286543"),
    ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),
    ("video 1: 用我的方法", "1001334883061622_122116445529286543"),
    ("Video 12：炒过那么多", "1001334883061622_122116264815286543"),
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    print("=" * 74)
    print("1) NEW ACCOUNT — token access + status")
    print("=" * 74)
    try:
        info = g.get_object(NEW, "name,account_status,disable_reason,currency,"
                                 "timezone_name,business")
        st = info.get("account_status")
        print(f"  ✅ token CAN read the account")
        print(f"  name={info.get('name')}  status={st} ({STATUS.get(st, '?')})  "
              f"disable_reason={info.get('disable_reason')}")
        print(f"  currency={info.get('currency')}  tz={info.get('timezone_name')}")
        print(f"  business={info.get('business')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ CANNOT read account — token not assigned to it yet: {exc}")

    print("\n" + "=" * 74)
    print("2) PIXELS / DATASETS on the new account")
    print("=" * 74)
    try:
        pix = g._get_all(f"{NEW}/adspixels", {"fields": "id,name", "limit": "50"})
        if pix:
            for p in pix:
                print(f"  pixel {p.get('id')}  {p.get('name')}")
        else:
            print("  ⚠ no pixel on this account — need one for conversion (Complete Registration) optimization")
    except Exception as exc:  # noqa: BLE001
        print(f"  pixel read failed: {exc}")

    print("\n" + "=" * 74)
    print("3) PAGE + IG readable? (needed for object_story_id ads)")
    print("=" * 74)
    try:
        pg = g.get_object(PAGE, "id,name,fan_count,instagram_business_account")
        print(f"  ✅ page {pg.get('id')} '{pg.get('name')}' fans={pg.get('fan_count')} "
              f"ig={pg.get('instagram_business_account')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ cannot read page {PAGE}: {exc}")
    # is the page promotable by THIS account? (client + owned pages of the business)
    for edge in ("promote_pages", "client_pages", "owned_pages"):
        try:
            path = (f"{NEW}/{edge}" if edge == "promote_pages" else f"{BUSINESS}/{edge}")
            pgs = g._get_all(path, {"fields": "id,name", "limit": "100"})
            hit = "✅ target page present" if any(str(p.get("id")) == PAGE for p in pgs) else "page NOT in this list"
            print(f"  {edge}: {len(pgs)} page(s) — {hit}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {edge}: n/a ({str(exc)[:80]})")

    print("\n" + "=" * 74)
    print("4) PROVEN POSTS reachable? (object_story_id reuse)")
    print("=" * 74)
    for label, pid in POSTS:
        try:
            g.get_object(pid, "id")
            print(f"  ✅ {pid}  {label}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ❌ {pid}  {label} — {str(exc)[:70]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
