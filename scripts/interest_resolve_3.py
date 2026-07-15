"""Read-only: resolve real Meta ad-interest IDs for News / Golf / Luxury Goods groups
(the top-converting ad sets), so the owner can approve a keyword list before we build.
Prints id / name / audience size / path per term. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

GROUPS = {
    "NEWS": ["News", "Online newspapers", "Newspapers", "Breaking news", "News media",
             "Financial news", "Bloomberg L.P.", "CNBC", "The Wall Street Journal",
             "The Business Times"],
    "GOLF / PICKLEBALL": ["Golf", "Pickleball", "Golf courses", "PGA Tour",
                          "Professional golfer", "Golf equipment", "Country club",
                          "Tennis"],
    "LUXURY GOODS": ["Luxury goods", "Luxury vehicles", "Luxury watches", "Rolex",
                     "Jewellery", "Luxury fashion", "Yacht", "Wealth management",
                     "Private banking", "Investment"],
}


def main() -> None:
    g = graph_client(load_settings())
    for grp, terms in GROUPS.items():
        print(f"\n{'='*84}\n{grp}\n{'='*84}")
        for t in terms:
            try:
                res = g._request("GET", "search",
                                 params={"type": "adinterest", "q": t, "limit": "3"})
            except Exception as exc:  # noqa: BLE001
                print(f"# {t}: ERR {str(exc)[:70]}")
                continue
            rows = res.get("data", []) or []
            if not rows:
                print(f"# {t}: (no interest)")
                continue
            print(f"# {t}")
            for it in rows:
                aud = it.get("audience_size_lower_bound") or it.get("audience_size")
                print(f"   id={it.get('id')}  «{it.get('name')}»  ~{aud}  topic={it.get('topic')}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
