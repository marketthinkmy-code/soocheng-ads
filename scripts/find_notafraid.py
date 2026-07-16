"""Locate the 不是怕交易 creative across MY + SG (any status) so it can be relaunched —
print id / status / campaign / adset + reusable post id. Read-only.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]
NEEDLE = "不是怕交易"


def main() -> None:
    g = graph_client(load_settings())
    for label, acct in ACCTS:
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "id,name,effective_status,campaign{name},adset{name},"
                          "creative{effective_object_story_id,object_story_id,video_id,image_hash}",
                          "limit": "800"})
        hits = [a for a in ads if NEEDLE in (a.get("name") or "")]
        print(f"\n[{label}] {acct}: {len(hits)} ad(s) matching «{NEEDLE}»")
        for a in hits:
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            kind = "vid" if cr.get("video_id") else ("img" if cr.get("image_hash") else "?")
            print(f"  {a.get('effective_status',''):10} id={a['id']}  {kind}  post={post}")
            print(f"       camp«{(a.get('campaign') or {}).get('name','')[:36]}»  "
                  f"set«{(a.get('adset') or {}).get('name','')[:28]}»  name«{a.get('name','')}»")
    print("\nDONE.")


if __name__ == "__main__":
    main()
