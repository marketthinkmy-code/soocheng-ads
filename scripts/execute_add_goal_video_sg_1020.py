# -*- coding: utf-8 -*-
"""owner 2026-10-20: «我只有一个目的» = Drive Ads-Video-02.mp4 (owner-confirmed file, owner-supplied caption + headline).
Download from Drive, upload to the SG ad account, build a video creative (Webinarkit -wed link, SG url_tags),
add it to SG WINNERS «Golf | SG 28+», rename the campaign 1-4-5. Campaign stays as it is (PAUSED until the owner
activates). Ban gate. CONFIRM=true writes; dry-run only checks Drive access + targets."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from adbot import compliance
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
FILE_ID = "1biTVqmldkJrIdltI89IVuhN0AgrarqvZ"          # Ads-Video-02.mp4
CAMP = "120249964890710521"
AD_NAME = "Video：我只有一个目的"
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
PAGE, IG = "1001334883061622", "17841480427751602"
URL_TAGS = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
MESSAGE = """🔎 你不是不会投资，而是还没遇到真正高效率的系统。
很多人用 3 年学习技术分析、K线、基本面……
但却有人，用【1分钟交易系统】，每天只花几分钟，就能稳定执行高胜率策略。
📉 不是猜方向，不靠运气。
📈 是看得懂、测得出、执行率高的“可量化系统”。

—

🧠 这场免费线上公开课
由资深交易系统导师 Soo Cheng 主讲，
课程内容源自：
✅ 数十万实盘数据验证
✅ 从散户视角出发，但用的是专业级交易逻辑

适合这些人：
✔️ 有正职但不想熬夜盯盘
✔️ 想为资金打造“第二条现金流”
✔️ 有一定理财/副业经验，寻求更高效模型
✔️ 曾学过技术分析、指标交易但效果不稳定

—
📌 为什么是「1分钟交易系统」？
📍 因为交易逻辑极简
📍 因为可量化、可回测
📍 因为“用得久、做得稳”，才是关键

—
🎁 本次为【少量公开席位】，限额开放：
📅 Zoom直播，仅此一晚
🎯 免费入门，不讲废话
💰 到场者可申请模拟账户 × 交易补贴

👇 如果你是认真想靠交易系统化管理资产的人，
点击下方按钮报名，不用试错，我们实证给你看。
错过这个晚上，也许你就要继续靠感觉投资、靠新闻追单。

#期货交易 #1分钟系统 #被动现金流 #交易者成长 #MrSooCheng #交易系统课 #资金管理 #量化投资 #金融课程 #Zoom公开课"""


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    assert not compliance.is_banned(AD_NAME, s.compliance.banned_creatives), "banned"
    drive = DriveClient(s.secrets.google_sa_json)
    meta = drive._svc.files().get(fileId=FILE_ID, fields="id,name,size,mimeType", supportsAllDrives=True).execute()
    print(f"  Drive: {meta}")
    assert meta["name"] == "Ads-Video-02.mp4"
    c = g.get_object(CAMP, "name,status")
    golf = next(a for a in g._get_all(CAMP + "/adsets", {"fields": "id,name", "limit": "10"}) if a["name"].startswith("Golf"))
    have = [x["name"] for x in g._get_all(golf["id"] + "/ads", {"fields": "name", "limit": "10"})]
    print(f"  campaign «{c['name']}» {c['status']} · Golf set {golf['id']} ads {have}")
    if AD_NAME in have:
        print("  already there — nothing to do"); return
    if not CONFIRM:
        print("DRY RUN — CONFIRM=true 才会写。"); return
    dest = Path("/tmp/ads-video-02.mp4")
    drive.download_file(FILE_ID, dest)
    print(f"  downloaded {dest.stat().st_size} bytes")
    vid = g.upload_video(acct, str(dest), "Ads-Video-02 我只有一个目的 (webinarkit)")
    print(f"  uploaded video {vid}")
    thumb = None
    for _ in range(12):
        th = g._get_all(vid + "/thumbnails", {"fields": "uri,is_preferred"})
        if th:
            thumb = next((t["uri"] for t in th if t.get("is_preferred")), th[0]["uri"]); break
        time.sleep(5)
    assert thumb, "no thumbnail yet"
    cr = g.create_adcreative(acct, name=f"{AD_NAME} · webinarkit-wed · headline", url_tags=URL_TAGS,
                             object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": {
                                 "video_id": vid, "image_url": thumb, "message": MESSAGE, "title": HEADLINE,
                                 "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}})["id"]
    ad = g.create_ad(acct, name=AD_NAME, adset_id=golf["id"], creative={"creative_id": cr}, status="ACTIVE")["id"]
    g._request("POST", CAMP, data={"name": re.sub(r"\| 1-\d+-\d+ \|", "| 1-4-5 |", c["name"])})
    time.sleep(2)
    st = g.get_object(ad, "status,effective_status")
    print(f"  ✅ creative {cr} · ad {ad} {st} · campaign «{g.get_object(CAMP, 'name')['name']}»")
    print("GOAL VIDEO DONE")


if __name__ == "__main__":
    main()
