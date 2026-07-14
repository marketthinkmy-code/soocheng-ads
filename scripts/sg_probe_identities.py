"""Read-only: hunt for the verified beneficiary/payer identity (the 'Siew Lai Yin'
advertiser) so we can reference it in an ad set's regional_regulation_identities.
Tries many candidate node-fields and edges on the SG account, its business, and page.
Whatever resolves tells us the identity id + shape to use. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

DST = "act_893025326577600"
BUSINESS = "769016565904540"
PAGE = "1001334883061622"


def try_node(g, node: str, fields: str) -> None:
    try:
        print(f"  NODE {node}?fields={fields}\n     -> {g.get_object(node, fields)}")
    except Exception as exc:  # noqa: BLE001
        print(f"  NODE {node}?fields={fields}\n     ERR {str(exc)[:130]}")


def try_edge(g, path: str, fields: str = "") -> None:
    params = {"limit": "50"}
    if fields:
        params["fields"] = fields
    try:
        rows = g._get_all(path, params)
        print(f"  EDGE {path}\n     -> {rows}")
    except Exception as exc:  # noqa: BLE001
        print(f"  EDGE {path}\n     ERR {str(exc)[:130]}")


def main() -> None:
    g = graph_client(load_settings())

    print("== account node fields ==")
    for f in ("regional_regulation_identities", "dsa_recommendations",
              "regulated_categories", "default_dsa_beneficiary", "default_dsa_payor"):
        try_node(g, DST, f)

    print("\n== account edges ==")
    for e in ("regional_regulation_identities", "dsa_recommendations",
              "beneficiary_payer", "regulatory_regions"):
        try_edge(g, f"{DST}/{e}", "id,name,beneficiary,payer,current")

    print("\n== business edges/fields (verified advertisers live at business level) ==")
    try_node(g, BUSINESS, "id,name")
    for e in ("regional_regulation_identities", "verified_advertisers",
              "business_advertiser_verifications", "owned_ad_accounts"):
        try_edge(g, f"{BUSINESS}/{e}", "id,name")

    print("\n== page node (advertiser could be the page identity) ==")
    try_node(g, PAGE, "id,name,verification_status")

    print("\nDONE.")


if __name__ == "__main__":
    main()
