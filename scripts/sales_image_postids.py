"""Read-only: recover reusable post IDs (object_story_id) for the 16 single-image ads
that closed sales. Their old ad accounts are banned/unreadable, so we try:
  1) exact/loose ad-name match on every reachable account, and
  2) the Page's own posts (dark + published) — posts survive an ad-account ban.
Prints, per winner, any post id found; then a Page image-post inventory for manual match.
No writes.
"""
from __future__ import annotations

from collections import defaultdict

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import load_settings

PAGE = "1001334883061622"
EXTRA = ["act_1263100565619799", "act_2285351942292267",
         "act_1017936814163755", "act_893025326577600", "act_2262468824239770"]

WINNERS = [
    "single image: 每天 1 分钟就能盈利", "single image 5: moomoo",
    "single image 5: moomoo - copy", "single image ah 20：期权兴趣者",
    "single image: 如何在最短时间", "single image: 每天只用 1 分钟",
    "single image 3", "single image 2", "single image 1：只需 1 分钟",
    "single image 2: 你的钱在等利息", "single image 6: 你的钱在等利息",
    "single image：prop firm 不是提款机", "image 1：快狠准 1分钟决策",
    "image：fd · 等利息还是复利 ②", "single image ah 11：有资金但不敢用的人（第二版）",
    "single image ah 19：forex / cfd 兴趣者",
]


def _nrm(x):
    return (cpa.norm(x or "").replace("：", ":").replace("！", "!")
            .replace("？", "?").replace("｜", "|").replace(" ", ""))


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    # 1) reachable-account ad-name -> post id / image_hash
    idx = {}
    accts = [s.meta.account_path] + [a for a in EXTRA if a != s.meta.account_path]
    for acct in accts:
        try:
            ads = g._get_all(f"{acct}/ads", {
                "fields": "name,effective_status,creative{effective_object_story_id,"
                          "object_story_id,image_hash,video_id}", "limit": "400"})
        except Exception as exc:  # noqa: BLE001
            print(f"  (skip {acct}: {str(exc)[:55]})")
            continue
        for a in ads:
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            idx.setdefault(_nrm(a.get("name", "")), (post, cr.get("image_hash"),
                                                     cr.get("video_id"), acct,
                                                     a.get("effective_status")))
    print()

    print("=" * 78)
    print("A · WINNER SINGLE-IMAGES → post id (from any reachable account)")
    print("=" * 78)
    found = 0
    for name in WINNERS:
        k = _nrm(name)
        hit = idx.get(k)
        if not hit:  # loose contains-match
            for ik, v in idx.items():
                if ik and (k in ik or ik in k):
                    hit = v
                    break
        if hit:
            post, img, vid, acct, st = hit
            found += 1
            print(f"  ✓ {name}\n      post={post}  image_hash={img}  [{st}] {acct}")
        else:
            print(f"  ✗ {name}  — not on any reachable account")
    print(f"\n{found}/{len(WINNERS)} found on reachable accounts")

    # 2) Page posts (survive account bans) — inventory for manual match
    print("\n" + "=" * 78)
    print("B · PAGE image posts (id + caption preview) — the surviving source")
    print("=" * 78)
    for edge, params in (
        ("promotable_posts", {"is_inline": "true",
                              "fields": "id,message,created_time,type", "limit": "100"}),
        ("posts", {"fields": "id,message,created_time,type", "limit": "100"}),
    ):
        try:
            rows = g._get_all(f"{PAGE}/{edge}", params)
            print(f"\n[{edge}] {len(rows)} posts")
            for p in rows:
                if p.get("type") and p.get("type") not in ("photo", "share", "link"):
                    continue
                msg = (p.get("message") or "").replace("\n", " ")[:56]
                print(f"   {p.get('id')}  {p.get('created_time','')[:10]}  "
                      f"{p.get('type','')}  {msg}")
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[{edge}] failed: {str(exc)[:90]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
