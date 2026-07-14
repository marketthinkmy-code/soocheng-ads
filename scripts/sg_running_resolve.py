"""Read-only: resolve real Meta ad-interest IDs for the running-club targeting group,
so we can build an ad set with valid interest ids (never invented). Prints id / name /
audience size / path per term. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

TERMS = [
    "Running", "Marathon", "Half marathon", "Long-distance running", "Trail running",
    "Jogging", "Triathlon", "Ironman Triathlon", "Strava", "Nike Run Club", "Parkrun",
    "Garmin", "Hoka", "On Running", "ASICS", "Physical fitness",
    "Standard Chartered Singapore Marathon", "Sundown Marathon",
]


def main() -> None:
    g = graph_client(load_settings())
    for t in TERMS:
        try:
            res = g._request("GET", "search",
                             params={"type": "adinterest", "q": t, "limit": "5"})
        except Exception as exc:  # noqa: BLE001
            print(f"# {t}: ERR {str(exc)[:80]}")
            continue
        rows = res.get("data", []) or []
        print(f"\n# {t}  ({len(rows)} hits)")
        for it in rows:
            path = " > ".join(it.get("path", []) or [])
            aud = it.get("audience_size_lower_bound") or it.get("audience_size")
            print(f"   id={it.get('id')}  «{it.get('name')}»  ~{aud}  topic={it.get('topic')}  [{path}]")
    print("\nDONE.")


if __name__ == "__main__":
    main()
