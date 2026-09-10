# -*- coding: utf-8 -*-
"""Owner 2026-09-10: 1-4-4 build, MY Broad.

  Campaign «STOCKBLOOM | BROAD MY 25+ | 0910 重拍» — ABO, 4 ad sets × RM50/day,
  each ad set named «Broad MY 25+», ONE ad each, everything ad-set-level PAUSED
  (owner reviews in Ads Manager and activates himself; campaign ACTIVE but inert).

  Ads:
    1. Image：iPhone Duo 对比 — NEW upload (Drive 1QK843z…), owner-approved copy
       written by us (对比/贬值角 + fixed 下半段), headline per owner 2026-09-10.
    2-4. 重拍 盖电脑 / 我跟你讲 / 厌倦了等待 — REUSE the already-approved AUGNEW
       posts (owner's pasted captions are verbatim identical to those posts'
       captions, so reuse = same creative, zero re-review risk, keeps engagement).

  Broad targeting cloned from «BROAD | 1-1-3 A» scaffold (custom audiences +
  flexible_spec stripped). Idempotent at (campaign, ad-name). Dry-run unless
  CONFIRM=true."""
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
PACE = 5.0
DAILY = 5000                       # RM50/day per ad set
N = cpa.norm

CAMP_NAME = "STOCKBLOOM | BROAD MY 25+ | 0910 重拍"
ASET_NAME = "Broad MY 25+"
SCAFFOLD = "BROAD | 1-1-3 A"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
IMG_FILE = "1QK843z3SQ0SxB8uJbGOb7-Xkd2BziHb6"

CAP_IMG = """RM15,499，买一台两年后就换掉的手机——
你眼睛都不眨。

一堂免费的课，学一套用一辈子的技能——
你却犹豫了三个月。

📱 手机，越用越贬值；
📈 技能，越用越值钱。

你不是花不起，
你只是习惯把钱花在「看得到」的东西上，
而真正拉开差距的，
从来都是看不见的那部分。

💬 Soo Cheng 老师常说：
「资产会旧，工具会换，
只有你会判断市场的能力，
没有人拿得走。」💡

✅ 这一次，不用 RM15,499——
一堂免费的线上分享会，
把《1 分钟极速交易攻略》完整讲清楚给你听。

📍 点击下方，免费报名——
钱可以再赚，判断力要自己学。🎯

══════════

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
📉 通胀 vs 利息：为什么钱放着不动，一直在缩水

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

REUSE = [
    ("重拍：Video 5：盖电脑，喂！", "重拍：video 5：盖电脑"),
    ("重拍：Video 6：我跟你讲！", "重拍：video 6：我跟你讲"),
    ("重拍：厌倦了等待", "重拍：厌倦了等待"),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-4-4 build · «{CAMP_NAME}» · 4 ad sets × RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    link = s.meta.lead_destination.link_url
    cta = {"type": s.meta.call_to_action or "SIGN_UP", "value": {"link": link}}

    # scaffold targeting
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
    tgt0.pop("custom_audiences", None)
    tgt0.pop("excluded_custom_audiences", None)
    tgt0.pop("flexible_spec", None)          # 真广投
    promo = sc.get("promoted_object") or {}
    print(f"scaffold ✓ «{(sc.get('name') or '')[:40]}» → broad (interests stripped)")

    # resolve the three approved 重拍 posts
    pool = g._get_all(
        f"{acct}/ads",
        {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
         "limit": "500"})
    time.sleep(1.2)

    def resolve_post(frag):
        best = []
        for a in pool:
            if N(frag) not in N(a.get("name") or ""):
                continue
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            if post:
                bad = a.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED")
                act = a.get("effective_status") == "ACTIVE"
                best.append((0 if act else (2 if bad else 1), post))
        best.sort()
        return best[0][1] if best else None

    plan = [{"name": "Image：iPhone Duo 对比", "kind": "image"}]
    for disp, frag in REUSE:
        post = resolve_post(frag)
        if post:
            plan.append({"name": disp, "kind": "post", "post": post})
            print(f"   post ✓ «{disp}»  {post}")
        else:
            print(f"   ⛔ «{disp}» 无可用已过审 post — 这支跳过")

    if not CONFIRM:
        print(f"\n▶ would create campaign(ABO ACTIVE) + {len(plan)} × "
              f"[adset «{ASET_NAME}» RM50 PAUSED + ad ACTIVE]")
        print(f"   image ad: 新上传 {IMG_FILE} · headline «{HEADLINE}» · link {link}")
        return

    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=s.meta.special_ad_categories,
            special_ad_category_country=["MY"], status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO, ACTIVE — ad set 全 PAUSED 才是闸门)")
        time.sleep(PACE)

    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}

    img_hash = None
    for t in plan:
        if N(t["name"]) in have:
            print(f"· «{t['name']}» 已在 — skip")
            continue
        aset = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
            targeting=_copy.deepcopy(tgt0), status="PAUSED")
        time.sleep(PACE)

        if t["kind"] == "image":
            if img_hash is None:
                drive = DriveClient(s.secrets.google_sa_json)
                p = drive.download_file(IMG_FILE, Path("/tmp/img_0910.png"))
                img_hash = g.upload_image(acct, str(p))
                print(f"   ⬆ image uploaded hash={img_hash[:16]}…")
                time.sleep(PACE)
            spec = {"name": f"MY | 0910 | {t['name']}",
                    "object_story_spec": {
                        "page_id": s.meta.page_id,
                        "link_data": {"image_hash": img_hash, "link": link,
                                      "message": CAP_IMG, "name": HEADLINE,
                                      "call_to_action": cta}}}
        else:
            spec = {"name": f"MY | 0910 | {t['name']}",
                    "object_story_id": t["post"]}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=t["name"], adset_id=aset["id"],
                         creative={"creative_id": cr["id"]},
                         status="ACTIVE", conversion_domain=conv)
        print(f"✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{t['name']}»")
        time.sleep(PACE)

    print("\nBUILD 0910 1-4-4 DONE — 全部 ad set PAUSED，owner 在 Ads Manager 审后自行开启。")


if __name__ == "__main__":
    main()
