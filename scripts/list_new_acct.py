"""Read-only: full campaign→ad state of the configured account, with effective_status
+ created_time, to separate my new PAUSED build from any pre-existing ads and spot dupes.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from adbot.commands import graph_client
from adbot.settings import load_settings


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    ads = g._get_all(f"{acct}/ads", {
        "fields": "id,name,effective_status,created_time,campaign{name},adset{name}",
        "limit": "400"})
    print(f"ACCOUNT {acct} — {len(ads)} ads total")
    print("status counts:", dict(Counter(a.get("effective_status") for a in ads)))

    bycamp = defaultdict(list)
    for a in ads:
        bycamp[(a.get("campaign") or {}).get("name", "?")].append(a)
    for camp in sorted(bycamp):
        lst = bycamp[camp]
        print(f"\n■ {camp}   ({len(lst)} ads)")
        for a in sorted(lst, key=lambda x: x.get("created_time", "")):
            print(f"   {a['id']} [{a.get('effective_status'):14}] "
                  f"{(a.get('created_time') or '')[:16]}  {a.get('name')}")

    # duplicate names across ACTIVE vs my new PAUSED
    byname = defaultdict(list)
    for a in ads:
        byname[a.get("name", "")].append(a.get("effective_status"))
    dupes = {n: v for n, v in byname.items() if len(v) > 1}
    print("\nDUPLICATE ad names (name → [statuses]):")
    for n, v in dupes.items():
        print(f"   {n} → {v}")
    if not dupes:
        print("   none")
    print("\nDONE.")


if __name__ == "__main__":
    main()
