# -*- coding: utf-8 -*-
"""Add the 13th single image (Image 35：先有方法再掏钱 · 关键顺序) — owner-approved.

Same 先有方法/别先掏钱 angle as Image 32; placed in BROAD (Image 32 already covers this
angle in Luxury) to diversify the top-converting pool instead of doubling it. Simplified
Chinese image — no 繁/简 issue.

Does two things, both idempotent, PAUSED (owner activates in Ads Manager):
  1) create the Notion Content Pipeline row (image_35) if it doesn't exist — Notion stays
     the durable source of truth for the copy.
  2) upload the image to EACH account (image_hash per-account) and add ONE single-image ad
     into each existing BROAD ad set (MY + SG) → Broad becomes 1-1-5.

Dry-run unless CONFIRM=true. The build uses the same in-script caption text it writes to
Notion (byte-identical), so there is no create-then-read race.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from adbot import state
from adbot.build_1_1_10 import display_ad_name
from adbot.clients.drive import DriveClient
from adbot.clients.notion import rich_text_property, title_property
from adbot.commands import graph_client, notion_client
from adbot.notion_captions import _title_text, content_id_from_title
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
DL_DIR = Path(REPO_ROOT) / "build_downloads"
MEDIA_KEY = "media_cache_1_1_4"

N = 35
FILE_ID = "138UPqlBj20edEWNLVhQnz1dztSRwpGJD"
TITLE = "Image 35：先有方法再掏钱 · 关键顺序"
HOOK = "开始交易的第一步，不是先掏钱"
BULLET = "🧭 交易的关键顺序：先有方法 → 验证 → 资金配合 → 执行优化，一步都别跳"

PART1 = """💰 有资金、也决定要开始交易，第一个念头却是「我要先放多少本」？顺序，就错在这一步。
钱你准备得最快，方法却一片空白——本金一进场靠的还是感觉，最后亏的还是自己。

Soo Cheng 老师常说：交易做得成，靠的是顺序——先有方法，再验证，然后资金配合，最后才是执行和优化。
第一步从来不是掏钱，是先把方法找对；方法对了，资金反而是最容易解决的那一环。

📍 这套「关键顺序」的第一步怎么走，Soo Cheng 老师会在免费线上分享会里免费教你。"""

TAIL = """══════════

🧑🏻‍💻 大家好，我是 Soo Cheng
首席投资分析师，
资深银行专业投资顾问，
超过 12 年实盘经验。

🌍 这些年我已帮助超过 10,000 名学员入门交易，
从完全零基础，
到能照着 SOP 稳定执行、
通过 Prop Firm 资金审核、用机构的资金操盘，
本金一分不动。

💡 如果你：

👉 有资金、也有判断力，但成绩总是靠感觉、时好时坏
👉 想让钱多一条腿走路，又不想拿本金去赌
👉 没时间天天盯盘，又怕错过、怕判断错

🫂 放心，我自己也走过靠感觉、靠盯盘填补不安的阶段。

❌ 我不会叫你 24 小时盯盘
❌ 不会要你拿自己的本金去冒险
❌ 也不会丢给你 10 个看不懂的指标

✨ 相反，我会教你一套简单、可量化、风控优先的方法——
看到条件才动，没有就等；
进、出、止损全部写死，不靠那天的心情。

💡 这堂免费课，你会学到：

🚦 红绿灯 SOP：进 / 出 / 止损全部写死，不靠感觉
⏱️ 1 分钟极速交易：从看到 signal 到关电脑的完整流程
🏦 Prop Firm funded account：怎么通过资金审核，本金不动
🔑 完全零基础也能照做的 checklist：不需要先懂 K 线
___BULLET___

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

CAPTION = PART1.rstrip() + "\n\n" + TAIL.replace("___BULLET___", BULLET)

# existing BROAD ad sets from the 1-1-4 build
BROAD_ADSETS = [
    ("MY", "act_759339046918885", "120247753945560575"),
    ("SG", "act_893025326577600", "120248429314250521"),
]


def ensure_notion_row(n, db) -> None:
    cid = f"image_{N}"
    for page in n.query_database(db):
        if content_id_from_title(_title_text(page.get("properties", {}))) == cid:
            print(f"· Notion row {cid} already exists — skip")
            return
    if not CONFIRM:
        print(f"WOULD CREATE Notion row «{TITLE}»  caption={len(CAPTION)} chars")
        return
    props = {"Title": title_property(TITLE), "Hook": rich_text_property(HOOK),
             "Caption": rich_text_property(CAPTION)}
    page = n._request("POST", "pages",
                      json_body={"parent": {"database_id": db}, "properties": props})
    print(f"✓ Notion row {cid} -> {page.get('id')}")


def image_hash_for(g, drive, cache, acct) -> str:
    key = f"{acct}:{FILE_ID}"
    if cache.get(key):
        return cache[key]
    DL_DIR.mkdir(parents=True, exist_ok=True)
    dest = DL_DIR / f"image_{N}.png"
    if not dest.exists():
        drive.download_file(FILE_ID, dest)
    h = g.upload_image(acct, str(dest))
    cache[key] = h
    state.save(MEDIA_KEY, cache)
    print(f"   [uploaded] image_{N} -> {acct} hash {h}")
    time.sleep(PACE)
    return h


def creative_spec(s, image_hash) -> dict:
    link = s.meta.lead_destination.link_url
    cta = {"type": s.meta.call_to_action, "value": {"link": link}}
    story = {"page_id": s.meta.page_id, "link_data": {
        "link": link, "image_hash": image_hash,
        "message": CAPTION, "name": HOOK, "call_to_action": cta}}
    spec = {"name": f"{s.naming.prefix} | image_{N}", "object_story_spec": story}
    if s.meta.instagram_user_id:
        spec["instagram_user_id"] = s.meta.instagram_user_id
    if s.meta.url_tags:
        spec["url_tags"] = s.meta.url_tags
    return spec


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    drive = DriveClient(s.secrets.google_sa_json)
    n = notion_client(s)
    cache = state.load(MEDIA_KEY)
    ad_name = display_ad_name(TITLE)

    print(f"CONFIRM={CONFIRM}  ·  add Image {N} -> Notion + both BROAD ad sets (PAUSED)  ·  ad «{ad_name}»\n")
    ensure_notion_row(n, s.notion.database_id)
    print()

    conv = s.meta.conversion_domain_bare or None
    for label, acct, adset in BROAD_ADSETS:
        present = {(a.get("name") or "") for a in
                   g._get_all(f"{adset}/ads", {"fields": "name", "limit": "200"})}
        if ad_name in present:
            print(f"· {label} BROAD ({adset}): «{ad_name}» already there — skip")
            continue
        if not CONFIRM:
            print(f"WOULD ADD {label} BROAD ({adset}): ad «{ad_name}»  [image_{N} ↔ {FILE_ID}]")
            continue
        h = image_hash_for(g, drive, cache, acct)
        cr = g.create_adcreative(acct, **creative_spec(s, h))
        ad = g.create_ad(acct, name=ad_name, adset_id=adset,
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"✓ {label} BROAD: ad {ad['id']}  «{ad_name}»")
        time.sleep(PACE)

    print("\nDONE — Image 35 added PAUSED; owner activates in Ads Manager."
          if CONFIRM else "\nDRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
