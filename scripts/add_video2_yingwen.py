# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-11「ok」): add the new «Video 2：市场不考你的英文» (02#.mp4)
to all 8 campaigns built 2026-08-10 (6 interest waves + 2 PURCHASE LAL) — each 1-1-5.

Caption is the owner-approved final text (identical to the Notion row created today).
Video is the creatives-folder copy (the editor's original folder is invisible to the
service account). Idempotent: a campaign whose ad set already carries the ad is skipped.
Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from adbot.clients.drive import DriveClient
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0   # slow: the SG account hit "user request limit reached" on the first pass

VIDEO_FILE_ID = "1u6Cu8WF3yxm4bveTA69fOSciQJq43l39"   # SOOCHENG Video 02.mp4 (creatives copy)
AD_NAME = "Video 2：市场不考你的英文"
HEADLINE = "市场不考你的英文"

CAPTION = """🙊 想赚 MJ，却卡在「我英文不好」？
Soo Cheng 老师一句话：市场，从来不考英文。

你不是没想过接外国单。💭
但一想到要跟客户讲英文，你就缩回去了：
怕听不懂问题，怕答错话，😰
最怕对方突然开 Video Call，你一句都讲不出来。📵

其实不是你不行，
是你把「赚 MJ」和「讲英文」绑在了一起。🔗

💬 Soo Cheng 老师常说：
「MJ 市场不会要你做 presentation，
也不会因为 grammar 不好拒绝你——
它只看一件事：你的判断，对不对。」💡

😮 而且在这里，选择权不在客户手上：
要不要进场、什么时候出场，全部你自己决定。✅

你要学的只有一件事：
从价格变化里判断买卖力量、控制风险，📊
什么时候不该交易、什么时候及时止损。🚦

📍 英文不好，不代表你不能学 MJ 市场。
点击下方，报名免费的「1 分钟交易攻略」线上分享会，
看普通人怎么从最基础的交易判断开始。🎯

══════════

🧑🏻‍💻 大家好，我是 Soo Cheng
首席投资分析师，资深银行专业投资顾问，超过 12 年实盘经验。

🌍 这些年我已帮助超过 10,000 名学员入门交易，
从完全零基础，到能照着 SOP 稳定执行、
通过 Prop Firm 资金审核、用机构的资金操盘，本金一分不动。

💡 如果你：

👉 有资金、也有判断力，但成绩总是靠感觉、时好时坏
👉 想让钱多一条腿走路，又不想拿本金去赌
👉 没时间天天盯盘，又怕错过、怕判断错

🫂 放心，我自己也走过靠感觉、靠盯盘填补不安的阶段。

❌ 我不会叫你 24 小时盯盘
❌ 不会要你拿自己的本金去冒险
❌ 也不会丢给你 10 个看不懂的指标

✨ 相反，我会教你一套简单、可量化、风控优先的方法——
看到条件才动，没有就等；进、出、止损全部写死，不靠那天的心情。

💡 这堂免费课，你会学到：

🚦 红绿灯 SOP：进 / 出 / 止损全部写死，不靠感觉
⏱️ 1 分钟极速交易：从看到 signal 到关电脑的完整流程
🏦 Prop Firm funded account：怎么通过资金审核，本金不动
🔑 完全零基础也能照做的 checklist：不需要先懂 K 线
📊 市场不考英文：从价格变化判断买卖力量，几时进、几时出、几时止损

⚠️ 名额有限，别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

ACCTS = [
    {"label": "SG", "acct": "act_893025326577600", "campaigns": [
        ("OMAKASE WAGYU", "120248813518730521"),
        ("LUXURY WATCHES", "120248813694490521"),
        ("DIVING", "120248813772520521"),
        ("LUXURY AUTO", "120248813817180521"),
        ("PURCHASE LAL 5%", "120248816613950521")]},
    {"label": "MY", "acct": "act_759339046918885", "campaigns": [
        ("OMAKASE WAGYU", "120248230256120575"),
        ("FOOD DRINK PREMIUM", "120248230283090575"),
        ("PURCHASE LAL 5%", "120248233421210575")]},
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Add «{AD_NAME}» to yesterday's 8 campaigns — {mode}\n")

    video_path = None
    if CONFIRM:
        video_path = DriveClient(s.secrets.google_sa_json).download_file(
            VIDEO_FILE_ID, Path("/tmp/soocheng_video_02.mp4"))
        print(f"downloaded -> {video_path}\n")

    conv = s.meta.conversion_domain_bare or None
    for ac in ACCTS:
        print(f"══ {ac['label']}  {ac['acct']} ══")
        vid = thumb = None
        if CONFIRM:
            vid = g.upload_video(ac["acct"], str(video_path), AD_NAME)
            thumb = g.get_video_thumbnail(vid)
            print(f"  ✓ video uploaded id={vid}")
            time.sleep(PACE)
        for theme, cid in ac["campaigns"]:
            try:
                asets = g._get_all(f"{cid}/adsets", {"fields": "id", "limit": "5"})
                if not asets:
                    print(f"  ⛔ {theme}: campaign {cid} has no ad set — skip")
                    continue
                have = {a.get("name") for a in g._get_all(
                    f"{cid}/ads", {"fields": "name", "limit": "50"})}
                if AD_NAME in have:
                    print(f"  ✓ {theme}: already has the ad — skip")
                    continue
                if not CONFIRM:
                    print(f"  ▶ {theme}: would add «{AD_NAME}» (PAUSED)")
                    continue
                video_data = {"video_id": vid, "title": HEADLINE, "message": CAPTION,
                              "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                                 "value": {"link": s.meta.lead_destination.link_url}}}
                if thumb:
                    video_data["image_url"] = thumb
                spec = {"name": f"{ac['label']} | {theme} | {AD_NAME}",
                        "object_story_spec": {"page_id": s.meta.page_id,
                                              "video_data": video_data}}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(ac["acct"], **spec)
                ad = g.create_ad(ac["acct"], name=AD_NAME, adset_id=asets[0]["id"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"  ✓ {theme}: ad {ad['id']}  «{AD_NAME}»")
                time.sleep(PACE)
            except GraphError as e:
                print(f"  ❌ {theme}: {e} — continuing")
        print()

    print("DONE — all campaigns now 1-1-5, new ads PAUSED."
          if CONFIRM else "DRY-RUN — set CONFIRM=true to apply.")


if __name__ == "__main__":
    main()
