"""SG actions (owner-authorized 2026-07-10), dry-run unless CONFIRM=true:

  A) pause the one still-live SG waster (Single Image AH 20 期权, RM56/0 reg).
  B) rebuild the 3 rejected SG ads with COMPLIANT copy (income claims stripped, approved
     马丁/Andromeda format) as new PAUSED ads, reusing the same video/image, in the same ad set.

Task C (port video 5/6/2 to SG) is a no-op: they are already live in [SG] 1-1-9.
Everything created is PAUSED — the owner reviews + requests review in Ads Manager.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

# ── A) pause ──────────────────────────────────────────────────────────────────
PAUSE_ADS = [("120248778394710115", "Single Image AH 20：期权兴趣者 [SG] — RM56 / 0 reg")]

# ── B) compliant rebuilds ─────────────────────────────────────────────────────
# fixed 下半段 (verbatim approved block); only {bullet} changes per angle.
LOWER = """══════════

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
{bullet}

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

P_BUZHIPA = """你一看到「交易」两个字，
心里第一反应就是：太难、太危险、一不小心就亏光。

所以你连了解都不敢了解，
就先把自己劝退了。

Soo Cheng 老师常说：
交易本身不可怕，
真正让人吃亏的，是你对它的误解——
没有系统、只靠感觉，才是风险的来源。

其实你需要的不是胆量，
而是一套「看到条件才动、没有就等」的清楚流程。

📍 怎么从零开始、用规则代替感觉，
Soo Cheng 老师会在免费线上分享会里讲给你听。

"""

P_MOOMOO = """你用 MooMoo 交易好几年了，
账户有对有错，但始终不稳定——
好行情来了仓位太小，
出手总是慢半拍，看对方向却不知道几时进。

Soo Cheng 老师常说：
很多有经验的人卡住，不是不懂市场，
是从来没有人教你，把「经验」变成一套可以重复执行的 SOP。

进出场有依据、风控是量化的，
不再靠那天的感觉做单。

📍 怎么把经验整理成一套长期能执行的系统，
Soo Cheng 老师会在免费线上分享会里讲给你听。

"""

P_YANJUAN = """你厌倦了那种感觉——
天天盯着屏幕，等一个不知道会不会来的机会，
错过了怕，追进去又常常买在最高点。

Soo Cheng 老师常说：
真正懂交易的人，不是守得最久的那个，
是出手最精准的那个。

与其一直等、一直盯，
不如学会一套「看到 signal 才动、没有就关电脑」的流程。

📍 怎么用 1 分钟看懂进出场、不再靠盯盘填补不安，
Soo Cheng 老师会在免费线上分享会里讲给你听。

"""

REBUILDS = [
    {"adset": "120248775849400115", "kind": "video", "media": "2770424979983940",
     "name": "Video：不是怕交易（合规重建）",
     "headline": "🔴 怕交易？你缺的不是胆量，是一套系统",
     "caption": P_BUZHIPA + LOWER.format(bullet="🧠 为什么「怕交易」其实是缺一套系统，不是缺胆量")},
    {"adset": "120248775849400115", "kind": "image", "media": "38371d44c3ee5492f5eba9160d3c311b",
     "name": "Image：MooMoo · 有经验但不稳定（合规重建）",
     "headline": "🔴 有经验却总是时好时坏？你缺的是一套 SOP",
     "caption": P_MOOMOO + LOWER.format(bullet="🎯 怎么把「靠经验」升级成「靠系统」——进出场都有依据")},
    {"adset": "120248778395070115", "kind": "video", "media": "1615514406147821",
     "name": "Video：厌倦了等待（合规重建）",
     "headline": "🔴 厌倦了盯盘和等待？出手精准，比守得久更重要",
     "caption": P_YANJUAN + LOWER.format(bullet="⏱️ 为什么盯盘越久反而越乱——出手精准比守得久更重要")},
]


def story(s, r):
    page = s.meta.page_id
    cta = {"type": s.meta.call_to_action, "value": {"link": s.meta.lead_destination.link_url}}
    if r["kind"] == "video":
        return {"page_id": page, "video_data": {
            "video_id": r["media"], "title": r["headline"], "message": r["caption"],
            "call_to_action": cta}}
    return {"page_id": page, "link_data": {
        "link": s.meta.lead_destination.link_url, "image_hash": r["media"],
        "message": r["caption"], "name": r["headline"], "call_to_action": cta}}


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"CONFIRM={CONFIRM}  ({'LIVE' if CONFIRM else 'DRY RUN — prints only'})\n")

    print("=== TASK A · pause dead SG ad ===")
    for ad_id, label in PAUSE_ADS:
        st = g.get_object(ad_id, "effective_status").get("effective_status")
        print(f"  {ad_id} [{st}] {label}")
        if st != "ACTIVE":
            print("   skip — not ACTIVE")
            continue
        if not CONFIRM:
            print("   WOULD PAUSE")
            continue
        g.update_status(ad_id, "PAUSED")
        print("   PAUSED ✓")

    print("\n=== TASK B · rebuild rejected ads (compliant, PAUSED) ===")
    for r in REBUILDS:
        st = story(s, r)
        if r["kind"] == "video":
            thumb = g.get_video_thumbnail(r["media"])
            if thumb:
                st["video_data"]["image_url"] = thumb
        spec = {"name": f"{s.naming.prefix} | rebuild {r['name']}", "object_story_spec": st}
        if s.meta.instagram_user_id:
            spec["instagram_user_id"] = s.meta.instagram_user_id
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        print(f"\n  {r['name']} ({r['kind']}, media={r['media']}) → adset {r['adset']}")
        print(f"    headline: {r['headline']}")
        print(f"    caption : {r['caption'][:70].replace(chr(10),' / ')} …  ({len(r['caption'])} chars)")
        if not CONFIRM:
            print("    WOULD CREATE creative + PAUSED ad")
            continue
        cid = g.create_adcreative(acct, **spec)["id"]
        ad = g.create_ad(acct, name=r["name"], adset_id=r["adset"],
                         creative={"creative_id": cid}, status="PAUSED",
                         conversion_domain=s.meta.conversion_domain_bare or None)
        print(f"    CREATED creative {cid} → ad {ad['id']} [PAUSED] ✓")

    print("\nDONE.")


if __name__ == "__main__":
    main()
