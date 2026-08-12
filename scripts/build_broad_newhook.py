# -*- coding: utf-8 -*-
"""Owner-approved 2026-08-12 (「10个新影片（都是 winning content 换掉 hook 的视频），
帮我全部跑 broad。1-1-3 / 1-1-3 / 1-1-4」): three pure-BROAD campaigns per account
carrying the 10 new re-cut videos.

  {prefix} | BROAD NEW HOOK A | 1-1-3   我跟你讲 EXTRA 1 · 盖电脑 EXTRA · 小白也可以用
  {prefix} | BROAD NEW HOOK B | 1-1-3   我跟你讲 EXTRA 2 · 你敢用60秒 · 不用看一大堆indicator
  {prefix} | BROAD NEW HOOK C | 1-1-4   FREESTYLE 1 EXTRA · trading 很难 · 以前要上下班 · 30秒测试

- Groupings spread the proven parents (我跟你讲 ×2, 盖电脑, 你敢吗, freestyle 1) across
  campaigns so each pool is diverse (Andromeda feeding).
- Captions: 马丁 Block A per video (anchored on the video's own title-hook) + the fixed
  Block B with one swapped curriculum bullet. House rules applied (两句一行 · 全角逗号 ·
  emoji · no income claims).
- Broad scaffold cloned from each account's converting BROAD ad set (flexible_spec and
  custom_audiences stripped); SG carries the Singapore regulated-category binding.
- RM50/day CBO · everything PAUSED · idempotent (existing campaigns get missing ads
  backfilled, video uploads cached per account). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy
import os
import time
from pathlib import Path

from adbot.clients.drive import DriveClient
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 5000    # RM50/day

SG = "act_893025326577600"
MY = "act_759339046918885"

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

SEP = "\n\n══════════\n\n"

BLOCK_B = """🧑🏻‍💻 大家好，我是 Soo Cheng
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
{bullet}

⚠️ 名额有限，别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

# (key, drive_file_id, ad_name, headline, bullet, part1)
VIDEOS = [
    ("xiaobai", "1Rj0tlUbM7j5rhQQ--giH8QLtmaWwZns9",
     "Video：小白也可以用", "小白也可以用的交易 SOP",
     "🧭 小白第一课：先学会「几时不进场」，比会看盘更重要",
     """🙋 完全没碰过交易的人，真的学得会吗？
Soo Cheng 老师的答案：会，因为你要学的不是「看盘」，是「照做」。

你不是没想过让钱动起来。💭
只是一打开行情软件，红红绿绿一大片，
你连该看哪里都不知道，更别说下单。😵

问身边的人，一人一个讲法，
上网查，越查越乱，
最后只敢把钱放回定存，安慰自己「至少不会亏」。⏳

💬 Soo Cheng 老师常说：
「小白学交易，不是先学会预测市场，
是先拿到一份写死的 checklist——
几时进、几时出、几时不动，照着做就好。」💡

😮 原来不是你学不会，
是从来没有人把步骤拆到「小白也可以用」。

📍 想看看零基础的人怎么从第一步开始，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("indicator", "17vXS_BvAflcoo_axo4tBF71i7JwqA8EW",
     "Video：不用看一大堆 indicator", "不用看一大堆 indicator",
     "📊 为什么 10 个指标不如 1 条写死的规则：只看买卖力量怎么判断",
     """📊 学交易，一定要先看懂 10 个 indicator？
Soo Cheng 老师一句话：指标越多，你越不敢下手。

你可能也试过：
MACD、RSI、布林线，一个一个加上去，🤯
结果图表越来越满，判断越来越慢，
这个说买、那个说卖，你反而不知道听谁的。😵‍💫

等你终于「确认」完，
行情早就走完了。⏳

💬 Soo Cheng 老师常说：
「指标是拿来辅助决定的，不是拿来代替决定的。
真正要看的只有一件事：价格变化背后的买卖力量。」💡

✅ 一套写死的 SOP，条件到了才动，
不用整天切来切去看一堆图。

📍 想知道怎么把交易简化到「看条件、照做」，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("test30s", "1EnHKWey60x44KRzuRXDf_MD_tZ9mlEQx",
     "Video：30秒测试", "30 秒，测你的交易漏洞",
     "⏱️ 现场 30 秒自测：你的交易漏洞在「进场」还是「止损」",
     """⏱️ 给你 30 秒，测一测：
你的交易，是有系统，还是靠感觉？

问自己三个问题：
进场前，你说得出「条件」吗？🤔
亏损时，你的止损是早就写死的吗？
还是——看心情、看感觉、看别人怎么讲？😬

如果三题里有一题答不出，
其实你不是在交易，是在猜。🎲

💬 Soo Cheng 老师常说：
「赚钱的交易可以很无聊：
条件到了就进，没到就等，错了就照规则离场。
刺激留给赌场，纪律留给自己。」💡

✅ 把「猜」换成「照做」，
从一套写死的红绿灯 SOP 开始。

📍 来测测你离系统化交易有多远，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("gaidiannao", "1TF_Q93NSKdcnibJxK6PS-pSnXUjiEq24",
     "Video：盖电脑 EXTRA", "敢不敢下完单就盖电脑？",
     "🧠 为什么盯盘越久反而越亏：「盖电脑」背后的纪律逻辑",
     """💻 敢不敢，下完单就把电脑盖起来？
不敢的话，你可能不是在交易，是在被盘面绑架。

你有没有过这种日子：
开着盘不敢关，吃饭在看，半夜也在看，📱
涨一点怕回调，跌一点怕爆掉，
盯了一整天，结果越看越乱手。😵

最累的不是亏钱，
是那种「一秒都不敢离开」的紧绷。😮‍💨

💬 Soo Cheng 老师常说：
「需要你 24 小时盯着的，不是策略，是赌注。
进、出、止损都写死了，你才有资格盖电脑。」💡

✅ 1 分钟做完决定，剩下交给规则，
时间还给生活。

📍 想知道「盖电脑」背后的完整 SOP，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("gan60s", "1bIqFlIyW2VMuPDyjawfATn7FTKXAMhHL",
     "Video：你敢用60秒做交易吗？", "你敢用 60 秒做交易吗？",
     "🚦 60 秒做完判断的 3 个写死条件：见齐才进场，缺一个就等",
     """⏱️ 你敢不敢，用 60 秒做完一笔交易？
看到条件、进场、设好止损、关电脑——整个过程，1 分钟。

你可能不信：
「交易不是要分析很久吗？」🤔
但你回想一下，那些让你亏钱的单，
往往就是「想太久」的那几笔——
犹豫到追高，纠结到不肯止损。😬

💬 Soo Cheng 老师常说：
「决定可以在 60 秒内做完，
因为功课早就做完了——
条件写死了，你只是核对，不是猜测。」💡

😮 快，不是鲁莽，
是准备好的人才有的速度。

✅ 一套红绿灯 SOP，
让你看到 signal 的那一刻就知道该不该动。

📍 敢来试的话，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("wgn1", "1AtCNf_QCSM_xg9K4xkpRgIlrJW6ilZF9",
     "Video：欸，我跟你讲！EXTRA 1", "欸，我跟你讲！",
     "💡 大部分人亏钱不是技术差，是没有「写死」的进出规则",
     """🗣️ 欸，我跟你讲，
你不是不会赚钱，你是留不住。

白天上班赚的，晚上乱操作亏回去，
朋友报的明牌，进场就套，😮‍💨
你自己心里其实清楚：
这样下去，几年后还是原地踏步。

你也想认真学，
但网上一人讲一套，
你根本分不清谁在教学、谁在演戏。🎭

💬 Soo Cheng 老师常说：
「方法对不对，看一个地方就够：
进、出、止损，敢不敢全部写死给你看。
写不死的，都是感觉派。」💡

✅ 我就把整套写死的 SOP，
一步一步摊开讲给你听。

📍 有兴趣的话，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("wgn2", "1Y-y7jeravVpXzfWQ5FE85NL4I4Tpi9AR",
     "Video：欸，我跟你讲！EXTRA 2", "欸，我跟你讲！",
     "🎯 一套 SOP 讲清楚：几时进、几时出、几时认错离场",
     """🗣️ 欸，我跟你讲，
钱放着不动，其实也是一种亏。

你算过吗：
物价一年一年涨，利息追不上，💸
你努力存下来的钱，购买力每年都在缩水。
最不敢冒险的选择，反而在慢慢亏。📉

但要你去「玩股票」，
你又怕：怕亏本金、怕看不懂、怕被割。😬

💬 Soo Cheng 老师常说：
「怕，是因为没规则。
风控写在进场之前，止损写在下单那一刻，
让钱多一条腿走路，不等于拿本金去赌。」💡

✅ 风控优先的 1 分钟交易法，
止损永远写在进场之前。

📍 想听懂的话，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("shangxiaban", "1sqPCxuwADUuINtICc9ub9dPNJfr3zIbl",
     "Video：以前要上下班", "上班族的 1 分钟交易流程",
     "🕐 上班族的执行流程：几点看、看多久、几时完全不用看",
     """🕐 以前要上下班的人，
现在用 1 分钟，做完一天的交易功课。

你是不是也这样：
朝九晚六，回到家只想躺，🛋️
想学一门新技能，却挤不出完整的时间，
「等我有空再说」，一说就是好几年。⏳

不是你懒，
是大部分方法，都默认你有大把时间盯盘。😮‍💨

💬 Soo Cheng 老师常说：
「上班族要的不是更多时间，
是一套不占时间的流程——
条件写死，1 分钟核对，做完就关电脑。」💡

✅ 不辞职、不盯盘、不熬夜，
交易安排在你的生活里，而不是反过来。

📍 想看这套流程长什么样，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("hennan", "1uALxzQmV2hhuVI-Cbi61eXaSvlXU_Xb0",
     "Video：很多人以为 trading 很难！", "trading 没有你想的难",
     "🧩 把交易拆成 3 步 checklist：核对、执行、离场，每步写死",
     """🧩 很多人以为 trading 很难，
难到要懂经济、会数学、盯一辈子的盘。

所以你一直不敢开始：
觉得那是专业人士的游戏，
自己「没那个天分」。😔

但你有没有想过，
你觉得难，可能只是因为——
从来没有人把它拆成你看得懂的步骤？🤔

💬 Soo Cheng 老师常说：
「交易不难，难的是没有 SOP。
把它拆成三步：核对条件、执行、离场，
每一步都写死，零基础也照做得来。」💡

😮 难的从来不是交易，
是你以为要靠聪明，其实只要靠纪律。

✅ 一套 checklist，把「难」拆成「照做」。

📍 想亲眼看这三步怎么拆，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),

    ("freestyle", "19YwvAqB4h3Ln8xU-4nOmYNGbxMnNccIV",
     "Video：FREESTYLE 1 EXTRA", "1 分钟，整套流程走完",
     "🗝️ 完整流程实拍：从开电脑到关电脑，每一步照 SOP 走",
     """🎥 不铺垫了，直接讲重点：
你的钱，需要一套会自己执行的规则。

你有判断力，也有一点资金，💼
偏偏成绩时好时坏，
好的时候不知道为什么好，
亏的时候也不知道错在哪。😮‍💨

这种「靠感觉」的状态，
才是最贵的成本。

💬 Soo Cheng 老师常说：
「感觉会累、会怕、会贪，
但写死的规则不会。
把进、出、止损交给 SOP，你只负责执行。」💡

✅ 从看到 signal 到关电脑，
整个流程 1 分钟，全部有规则可依。

📍 想看完整流程实拍，
点击下方，报名免费的「1 分钟交易攻略」线上分享会。🎯"""),
]

BY_KEY = {v[0]: v for v in VIDEOS}

CAMPAIGNS = [
    ("BROAD NEW HOOK A", ["wgn1", "gaidiannao", "xiaobai"]),
    ("BROAD NEW HOOK B", ["wgn2", "gan60s", "indicator"]),
    ("BROAD NEW HOOK C", ["freestyle", "hennan", "shangxiaban", "test30s"]),
]

ACCTS = [
    {"label": "SG", "acct": SG, "cfg": "config.sg.yaml", "sg": True,
     "prefix": "[SG] STOCKBLOOM", "ref_camp": "120248220658080521", "geo": ["SG"]},
    {"label": "MY", "acct": MY, "cfg": "config.yaml", "sg": False,
     "prefix": "STOCKBLOOM", "ref_camp": "120247522998960575", "geo": ["MY"]},
]


def caption(v) -> str:
    return v[5] + SEP + BLOCK_B.format(bullet=v[4])


def main() -> None:
    print(f"BROAD NEW HOOK × MY + SG · 1-1-3 / 1-1-3 / 1-1-4 · RM{DAILY/100:.0f}/day · "
          f"{'APPLY (CONFIRM=true)' if CONFIRM else 'DRY-RUN'}\n")

    paths: dict = {}
    if CONFIRM:
        base = load_settings(REPO_ROOT / "config" / "config.yaml")
        drive = DriveClient(base.secrets.google_sa_json)
        for v in VIDEOS:
            paths[v[0]] = drive.download_file(v[1], Path(f"/tmp/newhook_{v[0]}.mov"))
            print(f"  ⬇ {v[2]}  -> {paths[v[0]]}")
        print()

    for ac in ACCTS:
        s = load_settings(REPO_ROOT / "config" / ac["cfg"])
        g = graph_client(s)
        acct = ac["acct"]
        conv = s.meta.conversion_domain_bare or None
        print(f"══ {ac['label']}  {acct} ══")

        adsets = g._get_all(f"{ac['ref_camp']}/adsets",
                            {"fields": "id,targeting,promoted_object", "limit": "5"})
        if not adsets:
            print(f"  ‼️ reference campaign has no ad sets — skipping account")
            continue
        tgt = copy.deepcopy(adsets[0].get("targeting") or {})
        promo = adsets[0].get("promoted_object") or {}
        tgt.pop("flexible_spec", None)
        tgt.pop("custom_audiences", None)
        print(f"  scaffold adset {adsets[0]['id']} (broad)")

        existing = {c.get("name"): c.get("id") for c in
                    g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
        uploaded: dict = {}

        def media(key: str):
            if key not in uploaded:
                v = BY_KEY[key]
                vid = g.upload_video(acct, str(paths[key]), v[2])
                time.sleep(PACE)
                uploaded[key] = (vid, g.get_video_thumbnail(vid))
                print(f"     ⬆ video {vid}  «{v[2]}»")
            return uploaded[key]

        for camp_label, keys in CAMPAIGNS:
            camp_name = f"{ac['prefix']} | {camp_label} | 1-1-{len(keys)}"
            aset_name = f"AdSet ({camp_label.title()} | {ac['label']} 25+)"
            try:
                camp_id = existing.get(camp_name)
                if camp_id:
                    print(f"  · '{camp_name}' exists ({camp_id}) — checking for missing ads")
                    casets = g._get_all(f"{camp_id}/adsets", {"fields": "id", "limit": "5"})
                    if not casets:
                        print(f"    ‼️ no ad set inside — manual check needed, skipping")
                        continue
                    aset_id = casets[0]["id"]
                else:
                    if not CONFIRM:
                        print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO PAUSED"
                              + ("  · SG binding" if ac["sg"] else ""))
                        for k in keys:
                            print(f"       ad  «{BY_KEY[k][2]}»  headline «{BY_KEY[k][3]}»  (PAUSED)")
                        continue
                    camp = g.create_campaign(
                        acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                        daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                        special_ad_categories=s.meta.special_ad_categories,
                        special_ad_category_country=ac["geo"], status="PAUSED")
                    camp_id = camp["id"]
                    print(f"  ✓ campaign {camp_id}  '{camp_name}'")
                    time.sleep(PACE)
                    aset_kwargs = dict(
                        name=aset_name, campaign_id=camp_id,
                        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                        promoted_object=promo, targeting=tgt, status="PAUSED")
                    if ac["sg"]:
                        aset_kwargs.update(regional_regulated_categories=REGIONAL,
                                           regional_regulation_identities=REG_IDENTITIES)
                    aset = g.create_adset(acct, **aset_kwargs)
                    aset_id = aset["id"]
                    print(f"  ✓ adset {aset_id}")
                    time.sleep(PACE)

                if not CONFIRM:
                    continue
                have = {a.get("name") for a in g._get_all(
                    f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
                for k in keys:
                    v = BY_KEY[k]
                    if v[2] in have:
                        print(f"     ✓ «{v[2]}» already present — skip")
                        continue
                    vid, thumb = media(k)
                    video_data = {"video_id": vid, "title": v[3], "message": caption(v),
                                  "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                                     "value": {"link": s.meta.lead_destination.link_url}}}
                    if thumb:
                        video_data["image_url"] = thumb
                    spec = {"name": f"{ac['label']} | {camp_label} | {v[2]}",
                            "object_story_spec": {"page_id": s.meta.page_id,
                                                  "video_data": video_data}}
                    if s.meta.url_tags:
                        spec["url_tags"] = s.meta.url_tags
                    cr = g.create_adcreative(acct, **spec)
                    ad = g.create_ad(acct, name=v[2], adset_id=aset_id,
                                     creative={"creative_id": cr["id"]}, status="PAUSED",
                                     conversion_domain=conv)
                    print(f"     ✓ ad {ad['id']}  «{v[2]}»")
                    time.sleep(PACE)
            except GraphError as e:
                print(f"  ❌ {camp_name}: {e} — continuing")
        print()

    print("DONE — 3 BROAD NEW HOOK campaigns per account, all PAUSED; owner activates."
          if CONFIRM else "DRY-RUN — set confirm=true to build.")


if __name__ == "__main__":
    main()
