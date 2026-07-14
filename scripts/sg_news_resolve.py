"""Read-only prep for a '[SG] STOCKBLOOM | NEWS | 1-1-4' single-image campaign:
  1) inventory single-image ads (image_hash, no video_id) on every reachable account,
     with their reusable post id (effective_object_story_id) — esp. any '1-1-4' set;
  2) resolve the 'News' ad interest targeting id (+ audience size).
No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

REACH = ["act_759339046918885", "act_1263100565619799", "act_893025326577600"]


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    print("=" * 80)
    print("1) SINGLE-IMAGE ads on reachable accounts (reusable post ids)")
    print("=" * 80)
    for acct in REACH:
        try:
            ads = g._get_all(f"{acct}/ads", {
                "fields": "name,effective_status,campaign{name},"
                          "creative{effective_object_story_id,object_story_id,"
                          "image_hash,video_id}", "limit": "400"})
        except Exception as exc:  # noqa: BLE001
            print(f"  (skip {acct}: {str(exc)[:55]})")
            continue
        singles = []
        for a in ads:
            cr = a.get("creative") or {}
            if cr.get("image_hash") and not cr.get("video_id"):
                singles.append(a)
        print(f"\n  [{acct}] {len(ads)} ads · {len(singles)} single-image")
        for a in singles:
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            camp = (a.get("campaign") or {}).get("name", "")
            print(f"     post={post}  [{a.get('effective_status')}]  "
                  f"{a.get('name')}   «{camp}»")

    print("\n" + "=" * 80)
    print("2) 'News' ad interest targeting id")
    print("=" * 80)
    try:
        res = g._request("GET", "search",
                         params={"type": "adinterest", "q": "News", "limit": "10"})
        for it in res.get("data", []):
            path = " > ".join(it.get("path", []) or [])
            print(f"   id={it.get('id')}  name={it.get('name')}  "
                  f"audience={it.get('audience_size_lower_bound')}-"
                  f"{it.get('audience_size_upper_bound')}  topic={it.get('topic')}  [{path}]")
    except Exception as exc:  # noqa: BLE001
        print("  interest search failed:", exc)

    print("\nDONE.")


if __name__ == "__main__":
    main()
