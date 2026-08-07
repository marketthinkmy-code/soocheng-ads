"""Read-only: find how a WORKING Singapore-targeted ad set represents its verified
advertiser, so we can mirror it exactly instead of guessing API fields. The manual
Ads Manager shows 'Beneficiary and payer: Siew Lai Yin'; we need the API shape.

Strategy: scan every ad account this token can see; on each, find ad sets whose
targeting geo includes SG and dump their transparency/advertiser fields. Also dump the
target SG account's own advertiser-related account fields. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

DST = "act_893025326577600"
# adset transparency / regulated-advertiser fields to inspect
ADSET_FIELDS = ("id,name,account_id,effective_status,dsa_payor,dsa_beneficiary,"
                "regional_regulated_categories,targeting")
# known SG adsets from earlier SG work (may or may not still be readable)
KNOWN = ["120248775849400115", "120248778395070115", "120248778394710115"]


def dump(g, aid: str) -> None:
    try:
        a = g.get_object(aid, ADSET_FIELDS)
        t = a.get("targeting") or {}
        geo = (t.get("geo_locations") or {}).get("countries")
        print(f"  ADSET {a.get('id')} [{a.get('effective_status')}] acct={a.get('account_id')} "
              f"geo={geo}")
        print(f"     dsa_payor={a.get('dsa_payor')!r}  dsa_beneficiary={a.get('dsa_beneficiary')!r}")
        print(f"     regional_regulated_categories={a.get('regional_regulated_categories')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ADSET {aid} -> {str(exc)[:110]}")


def main() -> None:
    g = graph_client(load_settings())

    print("=" * 80)
    print("1) KNOWN earlier SG adsets (from sg_execute) — how do THEY declare advertiser?")
    print("=" * 80)
    for aid in KNOWN:
        dump(g, aid)

    print("\n" + "=" * 80)
    print("2) SCAN all visible accounts for any SG-targeted adset with advertiser fields")
    print("=" * 80)
    try:
        accts = g._get_all("me/adaccounts", {"fields": "account_id,name", "limit": "200"})
    except Exception as exc:  # noqa: BLE001
        print("  adaccounts read failed:", exc)
        accts = []
    for a in accts:
        acct = "act_" + str(a.get("account_id"))
        try:
            sets = g._get_all(f"{acct}/adsets", {"fields": ADSET_FIELDS, "limit": "200"})
        except Exception as exc:  # noqa: BLE001
            print(f"  [{acct}] {a.get('name')}: adsets read failed {str(exc)[:60]}")
            continue
        sg = []
        for s in sets:
            t = s.get("targeting") or {}
            geo = (t.get("geo_locations") or {}).get("countries") or []
            if "SG" in geo:
                sg.append(s)
        print(f"\n  [{acct}] {a.get('name')}: {len(sets)} adsets · {len(sg)} target SG")
        for s in sg[:6]:
            print(f"     {s.get('id')} [{s.get('effective_status')}] "
                  f"dsa_payor={s.get('dsa_payor')!r} dsa_beneficiary={s.get('dsa_beneficiary')!r} "
                  f"regional={s.get('regional_regulated_categories')}")

    print("\n" + "=" * 80)
    print("3) TARGET SG account advertiser-related fields")
    print("=" * 80)
    for fld in ("business", "name,account_status,disable_reason",
                "user_tasks", "amount_spent,currency"):
        try:
            print(f"  {fld}: {g.get_object(DST, fld)}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {fld}: {str(exc)[:90]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
