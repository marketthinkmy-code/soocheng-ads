"""Read-only: mint a Page access token from the system-user token, then list the Page's
ad posts (dark + published) and keyword-match the distinctive winning single images to
recover their reusable post ids (object_story_id = {page}_{postid}). No writes.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import requests

TOKEN = os.environ["META_SYSTEM_USER_TOKEN"]
SECRET = os.environ.get("META_APP_SECRET", "")
PAGE = "1001334883061622"
BASE = "https://graph.facebook.com/v21.0"

# distinctive caption keyword -> which winner it points to
KEYS = [
    ("moomoo", "single image 5: moomoo (+copy)"),
    ("期权", "single image ah 20：期权兴趣者"),
    ("prop firm", "single image：prop firm 不是提款机"),
    ("propfirm", "single image：prop firm 不是提款机"),
    ("提款机", "single image：prop firm 不是提款机"),
    ("forex", "single image ah 19：forex / cfd 兴趣者"),
    ("cfd", "single image ah 19：forex / cfd 兴趣者"),
    ("复利", "利息/复利 (FD 系列)"),
    ("等利息", "你的钱在等利息 (FD 系列)"),
    ("最短时间", "single image: 如何在最短时间"),
    ("快狠准", "image 1：快狠准 1分钟决策"),
    ("不敢用", "single image ah 11：有资金但不敢用"),
    ("每天只用", "single image: 每天只用 1 分钟"),
    ("就能盈利", "single image: 每天 1 分钟就能盈利"),
    ("只需 1 分钟", "single image 1：只需 1 分钟"),
]


def prf(tok):
    return hmac.new(SECRET.encode(), tok.encode(), hashlib.sha256).hexdigest() if SECRET else None


def get(path, tok, **params):
    params["access_token"] = tok
    p = prf(tok)
    if p:
        params["appsecret_proof"] = p
    return requests.get(f"{BASE}/{path}", params=params, timeout=30).json()


def main() -> None:
    info = get(PAGE, TOKEN, fields="name,access_token")
    pt = info.get("access_token")
    print(f"page: {info.get('name')}  page_token={'yes' if pt else 'NO'}")
    if info.get("error"):
        print("  error:", str(info["error"])[:120])
    tok = pt or TOKEN

    for edge in ("ads_posts", "published_posts"):
        print(f"\n===== {PAGE}/{edge} =====")
        page = get(f"{PAGE}/{edge}", tok,
                   fields="id,message,created_time", limit=200)
        if page.get("error"):
            print("  error:", str(page["error"])[:130])
            continue
        rows, pages = [], 0
        while True:
            rows.extend(page.get("data", []))
            nxt = (page.get("paging") or {}).get("next")
            pages += 1
            if not nxt or pages >= 6:
                break
            page = requests.get(nxt, timeout=30).json()
        print(f"  {len(rows)} posts scanned")
        seen = set()
        for p in rows:
            msg = (p.get("message") or "")
            low = msg.lower()
            for kw, who in KEYS:
                if kw.lower() in low and (p["id"], who) not in seen:
                    seen.add((p["id"], who))
                    print(f"   ► {who}\n       post={p['id']}  {p.get('created_time','')[:10]}"
                          f"  «{msg.replace(chr(10),' ')[:50]}»")
        if not seen:
            print("   (no keyword matches)")

    print("\nDONE.")


if __name__ == "__main__":
    main()
