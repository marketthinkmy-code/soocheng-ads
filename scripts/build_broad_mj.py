# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-11「帮我开 campaign BROAD for Video 1 & Video 2」): one pure
BROAD campaign per account carrying ONLY the two new MJ videos — no interests, no
custom audiences; the videos' self-selecting hooks do the targeting (Andromeda).

  [SG] STOCKBLOOM | BROAD MJ | 1-1-2   (scaffold: converting SG BROAD A ad set)
  STOCKBLOOM | BROAD MJ | 1-1-2        (scaffold: MY BROAD 1-1-3 A ad set)

Videos are re-used by per-account media id (uploaded 8/10-8/11); captions are the
owner-approved final texts. RM50/day CBO, PAUSED, idempotent, PACE 8s (SG throttled
yesterday). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy
import os
import time

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0

V1_NAME = "Video 1：赚美金，一定要接美国客户？"
V1_HEADLINE = "赚 MJ，不需要美国客户"
V2_NAME = "Video 2：市场不考你的英文"
V2_HEADLINE = "市场不考你的英文"

V1_CAPTION = """🙅 不会英文、没有人脉、一个客户都不用找
MJ 市场照样为你开门。
Soo Cheng 老师用一套 SOP，把这条路走给你看。🗝️

💰 你有没有发现，钱没少赚，却越来越不经用？💸
📱 iPhone 是 MJ 价，✈️ 孩子的留学费是 MJ 价，
连你退休金的购买力，都被汇率一年一年吃掉。📉

你也想过要赚 MJ。。。😭
但一直以为要接美国客户、要会英文、要熬时差，🤯
就觉得那不是你的世界。
一拖，又是一年。⏳

💬 Soo Cheng 老师常说：
「你不需要美国客户，美国市场本来就开放给所有人交易——
盈亏，本来就是 MJ 计价的。」💡

😮 原来卡住你的，从来不是英文，不是人脉，
是没人告诉你：还有一条不用接单的路。🛣️

💻 一台电脑，一套写死的 SOP，
看到条件才进场，1 分钟做完决定，关电脑走人。✅

📍 想知道普通人怎么从零开始、不接客户，
直接参与 MJ 计价的市场，
来听 Soo Cheng 老师的免费线上分享会。🎯

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
💵 不接美国客户、不用英文：怎么直接参与 MJ 计价的市场

⚠️ 名额有限，别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

V2_CAPTION = """🙊 想赚 MJ，却卡在「我英文不好」？
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

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

ACCTS = [
    {"label": "SG", "acct": "act_893025326577600", "sg": True,
     "prefix": "[SG] STOCKBLOOM", "ref_camp": "120248220658080521", "geo": ["SG"],
     "v1": "1397401099009914", "v2": "1336717308449971"},
    {"label": "MY", "acct": "act_759339046918885", "sg": False,
     "prefix": "STOCKBLOOM", "ref_camp": "120247522998960575", "geo": ["MY"],
     "v1": "1569053221675935", "v2": "2040235940700033"},
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"BROAD MJ campaigns × MY + SG · 1-1-2 (Video 1 + Video 2) · RM50/day — {mode}\n")
    conv = s.meta.conversion_domain_bare or None

    for ac in ACCTS:
        acct = ac["acct"]
        adsets = g._get_all(f"{ac['ref_camp']}/adsets",
                            {"fields": "id,name,targeting,promoted_object", "limit": "5"})
        if not adsets:
            raise SystemExit(f"‼️ {ac['label']} reference campaign has no ad sets")
        tgt = copy.deepcopy(adsets[0].get("targeting") or {})
        promo = adsets[0].get("promoted_object") or {}
        geo = (tgt.get("geo_locations") or {}).get("countries")
        if geo != ac["geo"]:
            raise SystemExit(f"‼️ {ac['label']} ref geo={geo}, expected {ac['geo']}")
        tgt.pop("flexible_spec", None)
        tgt.pop("custom_audiences", None)
        print(f"══ {ac['label']}  {acct} ══  (scaffold adset {adsets[0]['id']}, broad)")

        camp_name = f"{ac['prefix']} | BROAD MJ | 1-1-2"
        aset_name = f"AdSet (Broad MJ | {ac['label']} 25+)"
        existing = {c.get("name"): c.get("id") for c in
                    g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
        if camp_name in existing:
            print(f"  · '{camp_name}' already exists — skip\n")
            continue
        if not CONFIRM:
            print(f"  WOULD CREATE '{camp_name}'  RM50/day CBO PAUSED (pure broad)")
            print(f"     adset '{aset_name}'"
                  + ("  · SG binding" if ac["sg"] else ""))
            print(f"       ad  «{V1_NAME}»  (video {ac['v1']} reuse, PAUSED)")
            print(f"       ad  «{V2_NAME}»  (video {ac['v2']} reuse, PAUSED)\n")
            continue

        try:
            camp = g.create_campaign(
                acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                daily_budget=5000, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                special_ad_categories=s.meta.special_ad_categories,
                special_ad_category_country=ac["geo"], status="PAUSED")
            print(f"  ✓ campaign {camp['id']}")
            time.sleep(PACE)

            aset_kwargs = dict(
                name=aset_name, campaign_id=camp["id"],
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object=promo, targeting=tgt, status="PAUSED")
            if ac["sg"]:
                aset_kwargs.update(regional_regulated_categories=REGIONAL,
                                   regional_regulation_identities=REG_IDENTITIES)
            aset = g.create_adset(acct, **aset_kwargs)
            print(f"  ✓ adset {aset['id']}")
            time.sleep(PACE)

            for name, headline, caption, vid in (
                    (V1_NAME, V1_HEADLINE, V1_CAPTION, ac["v1"]),
                    (V2_NAME, V2_HEADLINE, V2_CAPTION, ac["v2"])):
                thumb = g.get_video_thumbnail(vid)
                video_data = {"video_id": vid, "title": headline, "message": caption,
                              "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                                 "value": {"link": s.meta.lead_destination.link_url}}}
                if thumb:
                    video_data["image_url"] = thumb
                spec = {"name": f"{ac['label']} | BROAD MJ | {name}",
                        "object_story_spec": {"page_id": s.meta.page_id,
                                              "video_data": video_data}}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **spec)
                ad = g.create_ad(acct, name=name, adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"     ✓ ad {ad['id']}  «{name}»")
                time.sleep(PACE)
            print()
        except GraphError as e:
            print(f"  ❌ [{ac['label']}] {e} — continuing\n")

    print("DONE — BROAD MJ campaigns built PAUSED; owner activates."
          if CONFIRM else "DRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
