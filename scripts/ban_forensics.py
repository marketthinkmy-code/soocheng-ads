"""Read-only ban forensics for the restricted account act_2282909119125229:

  1) account_status + disable_reason  — Meta's OFFICIAL account-level reason code
  2) every ad with issues_info / ad_review_feedback — the exact policy each rejected
     ad was cited under (this is the "why", per ad)
  3) recent account activity events related to review / rejection / disable

No writes. Restricted accounts normally still allow API reads; every section
degrades to an error line instead of crashing if Meta blocks it.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          8: "PENDING_SETTLEMENT", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE",
          101: "CLOSED"}
DISABLE = {0: "NONE", 1: "ADS_INTEGRITY_POLICY — ad policy violations",
           2: "ADS_IP_REVIEW", 3: "RISK_PAYMENT", 4: "GRAY_ACCOUNT_SHUT_DOWN",
           5: "AMBIGUOUS_NONEXISTENT_BUSINESS", 8: "UMBRELLA_AD_ACCOUNT",
           9: "BUSINESS_INTEGRITY_RAR", 10: "MISREPRESENTATION"}


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path

    print("=" * 78)
    print("1) ACCOUNT STATUS + OFFICIAL DISABLE REASON")
    print("=" * 78)
    try:
        info = g.get_object(acct, "name,account_status,disable_reason")
        st, dr = info.get("account_status"), info.get("disable_reason")
        print(f"  name={info.get('name')}")
        print(f"  account_status={st} ({STATUS.get(st, 'unknown')})")
        print(f"  disable_reason={dr} ({DISABLE.get(dr, 'unknown code')})")
    except Exception as exc:  # noqa: BLE001
        print("  account read failed:", exc)

    print("\n" + "=" * 78)
    print("2) ADS WITH REVIEW REJECTIONS — official policy citations per ad")
    print("=" * 78)
    ads = []
    try:
        ads = g._get_all(f"{acct}/ads", {
            "fields": "name,effective_status,issues_info,ad_review_feedback,campaign{name}",
            "limit": "400"})
    except Exception as exc:  # noqa: BLE001
        print("  ads read failed:", exc)
    bad = [a for a in ads if a.get("issues_info") or a.get("ad_review_feedback")
           or a.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED")]
    print(f"  {len(ads)} ads scanned · {len(bad)} with rejection/issues\n")
    for a in bad:
        camp = (a.get("campaign") or {}).get("name", "?")
        print(f"■ {a.get('name')}   [{a.get('effective_status')}]  {camp}  (ad {a.get('id')})")
        fb = a.get("ad_review_feedback") or {}
        glob = fb.get("global") or {}
        for policy, desc in glob.items():
            print(f"    POLICY: {policy}")
            print(f"      {str(desc)[:300]}")
        ps = fb.get("placement_specific") or {}
        for placement, policies in ps.items():
            for policy, desc in (policies or {}).items():
                print(f"    POLICY[{placement}]: {policy} — {str(desc)[:200]}")
        for iss in a.get("issues_info") or []:
            print(f"    issue: level={iss.get('level')} code={iss.get('error_code')} "
                  f"{iss.get('error_summary')}")
        print()

    print("=" * 78)
    print("3) RECENT ACCOUNT ACTIVITY — review / reject / disable events")
    print("=" * 78)
    try:
        evs = g._get_all(f"{acct}/activities",
                         {"fields": "event_type,event_time,object_name,extra_data",
                          "limit": "200"})
        keys = ("review", "reject", "disable", "flag", "policy", "restrict", "ban")
        hits = [e for e in evs if any(k in (e.get("event_type") or "").lower() for k in keys)]
        print(f"  {len(evs)} recent events · {len(hits)} review/disable-related\n")
        for e in hits[:40]:
            print(f"  {e.get('event_time')}  {e.get('event_type')}  {e.get('object_name')}")
            if e.get("extra_data"):
                print(f"      {str(e.get('extra_data'))[:220]}")
    except Exception as exc:  # noqa: BLE001
        print("  activities read failed:", exc)

    print("\nDONE.")


if __name__ == "__main__":
    main()
