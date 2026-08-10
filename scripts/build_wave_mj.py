# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-10): 6 new interest campaigns, each 1-1-4 = 3 proven winner
posts (theme-matched) + the NEW video ad «Video 1：赚美金，一定要接美国客户？» (01-A02.mp4).

  SG: OMAKASE WAGYU · LUXURY WATCHES · DIVING · LUXURY AUTO
  MY: OMAKASE WAGYU · FOOD DRINK PREMIUM

- RM50/day CBO · OUTCOME_SALES · everything PAUSED; owner activates.
- Interests are the ids verified 2026-08-10 via act targetingsearch (run #31364609569),
  the exact list the owner approved — no live re-guessing.
- Targeting scaffold copied verbatim from each account's converting Travel ad set;
  only flexible_spec is swapped.
- The new video is downloaded from Drive and uploaded per account; its caption is the
  owner-approved final text (identical to the Notion row «Video 1：赚美金，一定要接美国
  客户？» updated today — embedded here verbatim because TWO pipeline rows parse as
  video_1, so a content_id lookup would be ambiguous).
- Idempotent per campaign name. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy
import os
import time
from pathlib import Path

from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
CAMP_GAP = 10.0
DAILY = 5000    # RM50/day (cents)

SG = "act_893025326577600"
MY = "act_759339046918885"
VIDEO_FILE_ID = "1p_V5577TXLHWgJnEb21nSnPIyYKj8L38"   # SOOCHENG Video 01-A02.mp4 — copy
# inside the shared creatives folder (the editor's original lives in a folder the
# service account can't read; copied 2026-08-10 via Drive)
NEW_AD_NAME = "Video 1：赚美金，一定要接美国客户？"
NEW_HEADLINE = "赚 MJ，不需要美国客户"

CAPTION = """🙅 不会英文、没有人脉、一个客户都不用找
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

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

# verified interest ids (targetingsearch 2026-08-10)
I = lambda i, n: {"id": i, "name": n}
INTERESTS = {
    "OMAKASE WAGYU": [
        I("6002998123892", "Japanese cuisine"), I("6003374311125", "Sushi"),
        I("6003329638606", "Michelin"), I("6003721862097", "Wagyu"),
        I("6003173382014", "Steakhouse")],
    "LUXURY WATCHES": [
        I("6002893385022", "luxury watches"), I("6003587678073", "Rolex"),
        I("6003306942514", "Patek Philippe & Co."), I("6003382700604", "Audemars Piguet"),
        I("6003011259419", "TAG Heuer"), I("6004952336421", "Richard Mille"),
        I("6003762134517", "Cartier"), I("6003148796436", "Omega SA")],
    "DIVING": [
        I("6003210306830", "Scuba diving"), I("6003115850542", "Freediving"),
        I("6002868453910", "Snorkeling"), I("6003366140256", "Diving"),
        I("6002955429650", "Underwater diving")],
    "LUXURY AUTO": [
        I("6004048615096", "Luxury vehicle"), I("6003293721530", "Mercedes-Benz"),
        I("6003257785488", "BMW"), I("6003161093178", "Porsche"),
        I("6003069363782", "Ferrari"), I("6003456879344", "Lamborghini"),
        I("6003702639291", "Bentley"), I("6003241598211", "Rolls-Royce Motor Cars")],
    "FOOD DRINK PREMIUM": [
        I("6003292124828", "Whisky"), I("6003133619014", "Scotch whisky"),
        I("6003278978380", "Single malt whisky"), I("6003148544265", "Wine"),
        I("6003322500097", "wine tasting"), I("6003329638606", "Michelin")],
}

# theme -> the 3 proven winner posts to reuse (matched against live ads)
LINEUPS = {
    "OMAKASE WAGYU":      ["盖电脑", "freestyle 1", "早就不是这样"],
    "LUXURY WATCHES":     ["korea", "不选 forex", "你敢吗"],
    "DIVING":             ["korea", "盖电脑", "你敢吗"],
    "LUXURY AUTO":        ["freestyle 1", "korea", "早就不是这样"],
    "FOOD DRINK PREMIUM": ["我跟你讲", "你没有本钱", "不选 forex"],
}
DISPLAY = {
    "盖电脑": "video 5：盖电脑，喂！", "freestyle 1": "freestyle 1",
    "早就不是这样": "video 5：trading 早就不是这样了！", "korea": "freestyle: korea",
    "不选 forex": "video 12：不选 forex 不选黄金", "你敢吗": "video 2：你敢吗？",
    "我跟你讲": "video 6：我跟你讲！", "你没有本钱": "video 5: 你没有本钱",
}

ACCTS = [
    {"label": "SG", "acct": SG, "sg": True, "prefix": "[SG] STOCKBLOOM",
     "ref_camp": "120248220646980521", "geo": ["SG"],
     "themes": ["OMAKASE WAGYU", "LUXURY WATCHES", "DIVING", "LUXURY AUTO"]},
    {"label": "MY", "acct": MY, "sg": False, "prefix": "STOCKBLOOM",
     "ref_camp": "120247524817830575", "geo": ["MY"],
     "themes": ["OMAKASE WAGYU", "FOOD DRINK PREMIUM"]},
]


def _norm(s: str) -> str:
    return " ".join((s or "").replace("：", ":").split()).casefold()


def resolve_posts(g) -> dict:
    """key -> object_story_id, preferring ACTIVE instances (either account)."""
    pools = []
    for acct in (SG, MY):
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
                          "limit": "200"})
        pools.append(ads)
    out = {}
    for key in {k for lineup in LINEUPS.values() for k in lineup}:
        cands = []
        for ads in pools:
            for a in ads:
                if _norm(key) not in _norm(a.get("name") or ""):
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    cands.append((0 if a.get("effective_status") == "ACTIVE" else 1, post))
        if not cands:
            raise SystemExit(f"‼️ no live ad found matching «{key}»")
        cands.sort()
        out[key] = cands[0][1]
        print(f"  «{DISPLAY[key]}»  post={cands[0][1]}")
    return out


def ref_targeting(g, ac) -> tuple:
    adsets = g._get_all(f"{ac['ref_camp']}/adsets",
                        {"fields": "id,name,targeting,promoted_object", "limit": "20"})
    if not adsets:
        raise SystemExit(f"‼️ {ac['label']} reference campaign has no ad sets")
    ref = adsets[0]
    tgt, promo = ref.get("targeting") or {}, ref.get("promoted_object") or {}
    geo = (tgt.get("geo_locations") or {}).get("countries")
    if geo != ac["geo"]:
        raise SystemExit(f"‼️ {ac['label']} ref geo={geo}, expected {ac['geo']}")
    print(f"  [{ac['label']}] scaffold from adset {ref['id']}  geo={geo}  "
          f"pixel={promo.get('pixel_id')}")
    return tgt, promo


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM} · 6 campaigns (SG×4 + MY×2) · 1-1-4 · RM{DAILY/100:.0f}/day · PAUSED\n")

    print("== winner posts ==")
    posts = resolve_posts(g)

    print("\n== targeting scaffolds ==")
    scaffolds = {ac["label"]: ref_targeting(g, ac) for ac in ACCTS}

    video_path = None
    if CONFIRM:
        print("\n== download new video from Drive ==")
        video_path = DriveClient(s.secrets.google_sa_json).download_file(
            VIDEO_FILE_ID, Path("/tmp/soocheng_video_01_a02.mp4"))
        print(f"  downloaded -> {video_path}")

    vids = {}   # acct -> (video_id, thumb)
    for ac in ACCTS:
        base_tgt, promo = scaffolds[ac["label"]]
        existing = {c.get("name") for c in
                    g._get_all(f"{ac['acct']}/campaigns", {"fields": "id,name", "limit": "500"})}
        print(f"\n══ {ac['label']}  {ac['acct']} ══")

        if CONFIRM and ac["acct"] not in vids:
            vid = g.upload_video(ac["acct"], str(video_path), NEW_AD_NAME)
            thumb = g.get_video_thumbnail(vid)
            vids[ac["acct"]] = (vid, thumb)
            print(f"  ✓ video uploaded id={vid}")
            time.sleep(PACE)

        for theme in ac["themes"]:
            camp_name = f"{ac['prefix']} | {theme} | 1-1-4"
            aset_name = f"AdSet ({theme.title()} | {ac['label']} 25+)"
            if camp_name in existing:
                print(f"  · '{camp_name}' already exists — skip")
                continue
            tgt = copy.deepcopy(base_tgt)
            tgt["flexible_spec"] = [{"interests": INTERESTS[theme]}]

            if not CONFIRM:
                names = ", ".join(i["name"] for i in INTERESTS[theme])
                print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO PAUSED")
                print(f"     adset '{aset_name}'  interests: {names}"
                      + ("  · SG binding" if ac["sg"] else ""))
                for key in LINEUPS[theme]:
                    print(f"       ad  «{DISPLAY[key]}»  (post reuse, PAUSED)")
                print(f"       ad  «{NEW_AD_NAME}»  (new video + approved MJ caption, PAUSED)")
                continue

            camp = g.create_campaign(
                ac["acct"], name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                special_ad_categories=s.meta.special_ad_categories,
                special_ad_category_country=ac["geo"], status="PAUSED")
            print(f"  ✓ campaign {camp['id']}  {camp_name}")
            time.sleep(PACE)

            aset_kwargs = dict(
                name=aset_name, campaign_id=camp["id"],
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object=promo, targeting=tgt, status="PAUSED")
            if ac["sg"]:
                aset_kwargs.update(regional_regulated_categories=REGIONAL,
                                   regional_regulation_identities=REG_IDENTITIES)
            aset = g.create_adset(ac["acct"], **aset_kwargs)
            print(f"  ✓ adset {aset['id']}")
            time.sleep(PACE)

            conv = s.meta.conversion_domain_bare or None
            for key in LINEUPS[theme]:
                disp = DISPLAY[key]
                spec = {"name": f"{ac['label']} | {theme} | {disp}", "object_story_id": posts[key]}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(ac["acct"], **spec)
                ad = g.create_ad(ac["acct"], name=disp, adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"     ✓ ad {ad['id']}  «{disp}»")
                time.sleep(PACE)

            vid, thumb = vids[ac["acct"]]
            video_data = {"video_id": vid, "title": NEW_HEADLINE, "message": CAPTION,
                          "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                             "value": {"link": s.meta.lead_destination.link_url}}}
            if thumb:
                video_data["image_url"] = thumb
            story = {"page_id": s.meta.page_id, "video_data": video_data}
            if s.meta.instagram_user_id:
                story["instagram_actor_id"] = s.meta.instagram_user_id
            spec = {"name": f"{ac['label']} | {theme} | {NEW_AD_NAME}",
                    "object_story_spec": story}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(ac["acct"], **spec)
            ad = g.create_ad(ac["acct"], name=NEW_AD_NAME, adset_id=aset["id"],
                             creative={"creative_id": cr["id"]}, status="PAUSED",
                             conversion_domain=conv)
            print(f"     ✓ ad {ad['id']}  «{NEW_AD_NAME}» (new video)")
            time.sleep(CAMP_GAP)

    print("\nDONE — 6 campaigns built PAUSED; owner activates in Ads Manager."
          if CONFIRM else "\nDRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
