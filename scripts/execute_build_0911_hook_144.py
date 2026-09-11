# -*- coding: utf-8 -*-
"""Owner 2026-09-11: 4 支新 HOOK 重拍 → 1-4-4, MY.

  Campaign «STOCKBLOOM | BROAD MY 25+ | 0911 HOOK 重拍» — ABO, 4 ad sets ×
  RM50/day «Broad MY 25+», 每格 1 支视频, ad set 全 PAUSED（owner 审后自行开启;
  campaign ACTIVE but inert）。Broad targeting cloned from «BROAD | 1-1-3 A»
  scaffold（custom audiences + interests stripped）。No special ad category
  (owner untick direction 2026-09-10).

  Captions: ALL-NEW clean rewrites (owner:「文案重新帮我写，担心之前的文案是被
  banned 原因」) — 马丁/Andromeda two-part format, Part 1 anchored to each
  video's actual script, fixed 下半段 with one angle bullet swapped; zero income
  figures / promises / banned wording.

  Idempotent at (campaign, ad-name). Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time
from pathlib import Path

from adbot import cpa
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 5000                     # RM50/day per ad set
N = cpa.norm

CAMP_NAME = "STOCKBLOOM | BROAD MY 25+ | 0911 HOOK 重拍"
ASET_NAME = "Broad MY 25+"
SCAFFOLD = "BROAD | 1-1-3 A"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"

SEP = "\n\n══════════\n\n"

FIXED_TAIL = """🧑🏻‍💻 大家好，我是 Soo Cheng
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
{bullet}

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

P1_V5 = """一单，你用了 15 分钟，
还是一个小时？

盯着屏幕不敢走开，
以为多看一点，就多一点把握——
结果越看越乱，越坐越累。

你知道不对，
却不知道从哪调起。

💬 Soo Cheng 老师常说：
「你一直看盘，不代表你勤劳，
只代表你的方法，
还不能让你安心关电脑。」

真正该练的，
是让每一单在 1 分钟内做完该做的事——
进场、出场、止损，清清楚楚，
然后合上电脑，去过你的生活。

📍 这套「1 分钟交易 SOP」，
免费线上分享会里完整讲给你听。"""

P1_V12F = """外汇做过，黄金碰过，股票也套过——
每天追新闻、看几十个 indicator，
猜明天是起还是跌。

不是你不努力，
是「靠猜」这件事，
本来就没有终点。

💬 Soo Cheng 老师常说：
「交易不该是五十五十的猜。
看到什么条件买涨、什么条件买跌，
要清清楚楚写出来。」

为什么他只做期货？
因为涨和跌，两个方向都有机会，
不用赌市场只能往一边走。

📍 条件怎么定、方向怎么判，
免费线上分享会里一步步拆给你看。"""

P1_V8 = """「诶，做么你 trading 不用看盘的？」

因为该做的判断，
在进场之前就做完了。

每天一分钟，set up 好，
进场、出场、退路，全部照公式走——
剩下的时间，是你自己的。

💬 Soo Cheng 老师常说：
「交易靠的不是盯，
是一套看得懂、照得做的 SOP。」

更重要的是：
本钱不用自己押上去。
通过 Prop Firm 的资金审核，
用机构的资金去执行你的交易——
本金一分不动。

📍 这套一分钟公式怎么运作，
免费线上分享会里讲清楚。"""

P1_V12C = """黄金炒过，外汇炒过，股票也买过。
共同点只有两个：
累，而且不稳定。

黄金波动看心情，
外汇半夜爆新闻，你来不及反应，
股票买了不懂几时卖，钱卡在里面。

你不是没努力——
是工具本身，
就让你很难滚起来。

💬 Soo Cheng 老师常说：
「你要的不是刺激，是稳定。
方向看得清、规则写得死的工具，
才给得到你。」

所以他只做期货：
涨跌两个方向都有机会，
一天二十多个小时都有市场，
下班后照样轮得到你。

📍 工具怎么选、SOP 怎么套，
免费线上分享会里一次讲明白。"""

VIDEOS = [
    {"name": "HOOK：Video 5：盖电脑，喂！",
     "file": "1RNEfz2DtrGfWT3S4euyy7QP-Ie4yp_bU",
     "cap": P1_V5 + SEP + FIXED_TAIL.format(
         bullet="🧠 为什么盯盘越久，反而越难做对决定")},
    {"name": "HOOK：Video 12：不选 forex 不选黄金",
     "file": "1miH1QzLo5EQell0PIXktdlFqf65QTSI5",
     "cap": P1_V12F + SEP + FIXED_TAIL.format(
         bullet="📈 为什么选期货：涨跌两个方向，都有机会")},
    {"name": "HOOK：Video 8：做么你 Trading 不用看盘的？",
     "file": "1EHkz9GNZuiumJJFi5C-jqmhmm6h7HblT",
     "cap": P1_V8 + SEP + FIXED_TAIL.format(
         bullet="📋 上班族的交易节奏：每天一分钟，什么时候看、什么时候动")},
    {"name": "HOOK：Video 12：炒过那么多，累而且不稳定",
     "file": "1XCT43R98SQS74H4BWzc-SBSlmOf_65NA",
     "cap": P1_V12C + SEP + FIXED_TAIL.format(
         bullet="📉 黄金 vs 外汇 vs 股票 vs 期货：为什么工具决定你累不累")},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-4-4 HOOK build · «{CAMP_NAME}» · 4 ad sets × RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    link = s.meta.lead_destination.link_url

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1.2)
    sc_camp = next((c for c in camps if SCAFFOLD in (c.get("name") or "")), None)
    if not sc_camp:
        print(f"⛔ scaffold «{SCAFFOLD}» 找不到")
        return
    sc = (g._get_all(f"{sc_camp['id']}/adsets",
                     {"fields": "id,name,targeting,promoted_object", "limit": "5"})
          or [None])[0]
    time.sleep(1)
    tgt0 = _copy.deepcopy(sc.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences", "flexible_spec"):
        tgt0.pop(k, None)
    promo = sc.get("promoted_object") or {}
    print(f"scaffold ✓ «{(sc.get('name') or '')[:40]}» → broad")

    if not CONFIRM:
        print(f"\n▶ would create campaign(ABO ACTIVE, special_ad_categories=[]) + 4 × "
              f"[adset «{ASET_NAME}» RM50 PAUSED + 1 video ad ACTIVE]")
        for v in VIDEOS:
            print(f"   · «{v['name']}»  drive={v['file']}  caption={len(v['cap'])} chars")
        return

    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=[], status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO ACTIVE, no special category — ad set 全 PAUSED 是闸门)")
        time.sleep(PACE)

    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
    drive = None
    for i, v in enumerate(VIDEOS):
        if N(v["name"]) in have:
            print(f"· «{v['name']}» 已在 — skip")
            continue
        aset = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
            targeting=_copy.deepcopy(tgt0), status="PAUSED")
        time.sleep(PACE)
        if drive is None:
            drive = DriveClient(s.secrets.google_sa_json)
        p = drive.download_file(v["file"], Path(f"/tmp/hook_{i}.mp4"))
        vid = g.upload_video(acct, str(p), v["name"])
        time.sleep(PACE)
        thumb = g.get_video_thumbnail(vid)
        print(f"   ⬆ video {vid}  thumb={'✓' if thumb else '—'}")
        video_data = {"video_id": vid, "title": HEADLINE, "message": v["cap"],
                      "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                         "value": {"link": link}}}
        if thumb:
            video_data["image_url"] = thumb
        spec = {"name": f"MY | 0911 HOOK | {v['name']}",
                "object_story_spec": {"page_id": s.meta.page_id,
                                      "video_data": video_data}}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=v["name"], adset_id=aset["id"],
                         creative={"creative_id": cr["id"]},
                         status="ACTIVE", conversion_domain=conv)
        print(f"✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{v['name']}»")
        time.sleep(PACE)

    print("\nBUILD 0911 HOOK 1-4-4 DONE — 全部 ad set PAUSED，owner 在 Ads Manager 审后自行开启。")


if __name__ == "__main__":
    main()
