# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-10「帮我开 LAL campaign 在 MY & SG」): one campaign per
account targeting the fresh 5% PURCHASE lookalikes (seed: 664 Paid Student List buyers).

  [SG] STOCKBLOOM | PURCHASE LAL 5% | 1-1-4   (LAL 120248811885370521)
  STOCKBLOOM | PURCHASE LAL 5% | 1-1-4        (LAL 120248227780480575)

- 1-1-4 = the three best all-round sellers (freestyle 1 · korea · 盖电脑) + the new
  赚美金 video (already uploaded per account today — reused by id, no re-upload).
- Targeting scaffold cloned from each account's converting Travel ad set; flexible_spec
  (interests) removed, custom_audiences=[LAL] swapped in. No exclusions (special-ad
  categories dislike them; 664 buyers among millions is noise).
- FPS note: if Meta blocks lookalikes for FINANCIAL_PRODUCTS_SERVICES the ad-set POST
  400s here — that IS the live verification; the error is reported, nothing dangles.
- RM50/day CBO · PAUSED · idempotent per campaign name. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy
import os
import time

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
DAILY = 5000    # RM50/day

SG = "act_893025326577600"
MY = "act_759339046918885"
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

LINEUP = ["freestyle 1", "korea", "盖电脑"]
DISPLAY = {
    "freestyle 1": "freestyle 1",
    "korea": "freestyle: korea",
    "盖电脑": "video 5：盖电脑，喂！",
}

ACCTS = [
    {"label": "SG", "acct": SG, "sg": True, "prefix": "[SG] STOCKBLOOM",
     "ref_camp": "120248220646980521", "geo": ["SG"],
     "lal": "120248811885370521", "video": "1397401099009914"},
    {"label": "MY", "acct": MY, "sg": False, "prefix": "STOCKBLOOM",
     "ref_camp": "120247524817830575", "geo": ["MY"],
     "lal": "120248227780480575", "video": "1569053221675935"},
]


def _norm(s: str) -> str:
    return " ".join((s or "").replace("：", ":").split()).casefold()


def resolve_posts(g) -> dict:
    pools = []
    for acct in (SG, MY):
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
                          "limit": "200"})
        pools.append(ads)
    out = {}
    for key in LINEUP:
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


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM} · PURCHASE LAL 5% campaigns × MY + SG · 1-1-4 · "
          f"RM{DAILY/100:.0f}/day · PAUSED\n")

    print("== winner posts ==")
    posts = resolve_posts(g)
    print()

    for ac in ACCTS:
        acct = ac["acct"]
        adsets = g._get_all(f"{ac['ref_camp']}/adsets",
                            {"fields": "id,targeting,promoted_object", "limit": "5"})
        if not adsets:
            raise SystemExit(f"‼️ {ac['label']} reference campaign has no ad sets")
        tgt = copy.deepcopy(adsets[0].get("targeting") or {})
        promo = adsets[0].get("promoted_object") or {}
        tgt.pop("flexible_spec", None)
        tgt["custom_audiences"] = [{"id": ac["lal"]}]

        aud = g._request("GET", ac["lal"],
                         params={"fields": "name,approximate_count_lower_bound,operation_status"})
        print(f"══ {ac['label']}  {acct} ══")
        print(f"  LAL «{aud.get('name')}»  size≈{aud.get('approximate_count_lower_bound')}  "
              f"status={((aud.get('operation_status') or {}).get('description') or '?')[:60]}")

        camp_name = f"{ac['prefix']} | PURCHASE LAL 5% | 1-1-4"
        aset_name = f"AdSet (Purchase LAL 5% | {ac['label']} 25+)"
        existing = {c.get("name"): c.get("id") for c in
                    g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
        if camp_name in existing:
            print(f"  · '{camp_name}' already exists — skip\n")
            continue

        if not CONFIRM:
            print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO PAUSED")
            print(f"     adset '{aset_name}'  audience: LAL {ac['lal']} (no interests)"
                  + ("  · SG binding" if ac["sg"] else ""))
            for key in LINEUP:
                print(f"       ad  «{DISPLAY[key]}»  (post reuse, PAUSED)")
            print(f"       ad  «{NEW_AD_NAME}»  (video {ac['video']} reuse, PAUSED)\n")
            continue

        try:
            camp = g.create_campaign(
                acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
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
            print(f"  ✓ adset {aset['id']}  (LAL accepted — FPS 没挡)")
            time.sleep(PACE)

            conv = s.meta.conversion_domain_bare or None
            for key in LINEUP:
                disp = DISPLAY[key]
                spec = {"name": f"{ac['label']} | PURCHASE LAL | {disp}",
                        "object_story_id": posts[key]}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **spec)
                ad = g.create_ad(acct, name=disp, adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"     ✓ ad {ad['id']}  «{disp}»")
                time.sleep(PACE)

            thumb = g.get_video_thumbnail(ac["video"])
            video_data = {"video_id": ac["video"], "title": NEW_HEADLINE, "message": CAPTION,
                          "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                             "value": {"link": s.meta.lead_destination.link_url}}}
            if thumb:
                video_data["image_url"] = thumb
            spec = {"name": f"{ac['label']} | PURCHASE LAL | {NEW_AD_NAME}",
                    "object_story_spec": {"page_id": s.meta.page_id, "video_data": video_data}}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=NEW_AD_NAME, adset_id=aset["id"],
                             creative={"creative_id": cr["id"]}, status="PAUSED",
                             conversion_domain=conv)
            print(f"     ✓ ad {ad['id']}  «{NEW_AD_NAME}» (new video)\n")
        except GraphError as e:
            print(f"  ❌ [{ac['label']}] {e}")
            print("     （若为 special-ad-category 限制 lookalike，此账户改走 Advantage+ 方案 — 汇报 owner）\n")

    print("DONE — LAL campaigns built PAUSED; owner activates."
          if CONFIRM else "DRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
