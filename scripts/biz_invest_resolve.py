"""Read-only: resolve the extra targeting the owner asked to add —
  Business Owner: behaviors (Small business owners / Page admins) + job titles (CEO / Founder / Owner)
  Investment:     interests (Trading / Investing / Trading software / Forex)
Searches the right Meta targeting types (behaviors, work positions, interests). No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings


def search(g, typ, q, cls=None):
    params = {"type": typ, "q": q, "limit": "6"}
    if cls:
        params["class"] = cls
    return (g._request("GET", "search", params=params).get("data", []) or [])


def show(g, header, typ, terms, cls=None):
    print(f"\n=== {header} (type={typ}{'/'+cls if cls else ''}) ===")
    for t in terms:
        try:
            rows = search(g, typ, t, cls)
        except Exception as exc:  # noqa: BLE001
            print(f"# {t}: ERR {str(exc)[:70]}")
            continue
        if not rows:
            print(f"# {t}: (none)")
            continue
        print(f"# {t}")
        for it in rows[:4]:
            aud = it.get("audience_size_lower_bound") or it.get("audience_size")
            extra = it.get("path") or it.get("name")
            print(f"   id={it.get('id')}  «{it.get('name')}»  ~{aud}  {it.get('type','')}")


def main() -> None:
    g = graph_client(load_settings())
    show(g, "BUSINESS OWNER · behaviors", "adTargetingCategory",
         ["Small business owners", "Facebook page admins", "Business page admins",
          "Business owners"], cls="behaviors")
    show(g, "BUSINESS OWNER · job titles", "adworkposition",
         ["Chief Executive Officer", "Founder", "Owner", "Managing Director",
          "Director", "Co-Founder"])
    show(g, "INVESTMENT · interests", "adinterest",
         ["Trading", "Investing", "Trading software", "Forex", "Stock trader",
          "Foreign exchange market"])
    print("\nDONE.")


if __name__ == "__main__":
    main()
