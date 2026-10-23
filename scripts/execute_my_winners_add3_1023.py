# -*- coding: utf-8 -*-
"""owner 2026-10-23「建」— MY WINNERS +3 single-creative ad sets (RM50 each, created PAUSED inside the live WINNERS MY
campaign; owner activates). Sold creatives never run on MY 5.0, none ever rejected:
  我跟你讲 (8 MY sales/180d) · 用我的方法，你也可以有将多 (6 MY) · 赚美金 = 求人？ (2, latest 9/23).
Copy = each video's last approved caption, with compliance edits (owner: 「旧文案逐句对照禁用词，有问题的句子改掉」):
  我跟你讲: drop「他们用的是自己的钱 / 而我用的是 Prop Firm 的机制」(other-people's-money framing)
  赚美金=求人: 「一开始不掏自己的血汗钱，用 Prop Firm 提供的资金」→ discipline-first wording; 「玩法」→「做法」
A phrase scan blocks the build if any banned wording survives. Targeting/promoted/regional = WINNERS MY «Broad · 赚美金».
Creatives are validate_only-checked in dry-run. Ban gate. Idempotent. CONFIRM=true writes."""
from __future__ import annotations

import os
import re
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMP = "120251533789970329"
SRC_SET = "120251533795640329"                      # «Broad · 赚美金 | MY 28+»
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
PAGE, IG = "1001334883061622", "17841480427751602"
URL_TAGS_REF = "120251454697280329"                 # a MY Webinarkit ad (its creative's url_tags)
BAD = ["玩", "200", "300", "提现", "提款", "保证", "零本钱", "不用自己的本钱", "自己的钱", "血汗钱", "别人的资金",
       "稳赚", "100%", "被动收入", "pass", "Pass", "copy paste", "填名字", "电话"]
PLAN = [  # (ad set, ad name, caption-source creative, video candidates, [(old, new), ...])
    ("Broad · 我跟你讲 | MY 28+", "Video：我跟你讲！", "1104962755787873", ["2059836261562402"], [
        ("因为他们用的是自己的钱。\n所以慢、所以怕、所以一直看。\n\n而我用的是\n👉 Prop Firm 的机制，\n👉 清楚的 formula，\n👉 可照着做的 SOP。",
         "因为他们没有一套写死的规则。\n所以慢、所以怕、所以一直看。\n\n而我用的是\n👉 清楚的 formula，\n👉 可照着做的 SOP，\n👉 风控先行的纪律。")]),
    ("Broad · 用我的方法 将多 | MY 28+", "Video：用我的方法，你也可以有将多", "3206809892857568", ["856184690790753"], []),
    ("Broad · 赚美金=求人 | MY 28+", "Video：赚美金 = 求人？", "SG_MJ", ["4659625310979420", "4431118597102739"], [
        ("一开始不掏自己的血汗钱，\n用 Prop Firm 提供的资金：", "先把纪律和风控练稳，\n再去考 Prop Firm 的资金审核："),
        ("完整玩法", "完整做法")]),
]


def caption(g, src: str) -> str:
    if src == "SG_MJ":                               # 🌟 Video 10：赚美金 = 求人？ (SG, sold) — find by name
        sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
        ads = graph_client(sg)._get_all(sg.meta.account_path + "/ads", {"fields": "name,creative{object_story_spec}", "limit": "500"})
        a = next(x for x in ads if "赚美金 = 求人" in (x.get("name") or "") and "🌟" in x["name"])
        return a["creative"]["object_story_spec"]["video_data"]["message"]
    c = g.get_object(src, "body,object_story_spec")
    return ((c.get("object_story_spec") or {}).get("video_data") or {}).get("message") or c.get("body") or ""


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"MY WINNERS +3 — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned([p[1] for p in PLAN], s.compliance.banned_creatives), "banned"
    src = g.get_object(SRC_SET, "targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                "regional_regulated_categories,regional_regulation_identities")
    url_tags = g.get_object(URL_TAGS_REF, "creative{url_tags}")["creative"]["url_tags"]
    have_sets = {x["name"] for x in g._get_all(CAMP + "/adsets", {"fields": "name", "limit": "20"})}
    have_cr = {c.get("name"): c["id"] for c in g._get_all(acct + "/adcreatives", {"fields": "id,name", "limit": "500"})}
    ready, made = [], 0
    for sname, aname, csrc, vids, edits in PLAN:
        msg = caption(g, csrc)
        for old, new in edits:
            assert old in msg, f"{aname}: edit anchor missing «{old[:30]}»"
            msg = msg.replace(old, new)
        hits = [b for b in BAD if b in msg]
        print(f"\n▶ {aname} · caption {len(msg)} chars · edits {len(edits)} · banned-phrase hits {hits or '无'}")
        assert not hits, f"{aname}: banned wording {hits}"
        vid, thumb, err = None, None, None
        for v in vids:
            th = g.get_video_thumbnail(v)
            vd = {"video_id": v, "message": msg, "title": HEADLINE, "image_url": th,
                  "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            try:
                g.create_adcreative(acct, name=f"{aname} · webinarkit-wed", url_tags=url_tags, execution_options=["validate_only"],
                                    object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": vd})
                vid, thumb = v, th
                break
            except Exception as exc:                                     # noqa: BLE001
                err = str(exc)[:160]
                print(f"   video {v} ✗ {err}")
        assert vid, f"{aname}: no usable video ({err})"
        print(f"   video {vid} ✓ validate_only · set exists {sname in have_sets}")
        ready.append((sname, aname, vid, thumb, msg))
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nADD3 DONE (dry-run)"); return
    for sname, aname, vid, thumb, msg in ready:
        if sname in have_sets:
            continue
        cname = f"{aname} · webinarkit-wed"
        cr = have_cr.get(cname) or g.create_adcreative(
            acct, name=cname, url_tags=url_tags,
            object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": {
                "video_id": vid, "message": msg, "title": HEADLINE, "image_url": thumb,
                "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}})["id"]
        time.sleep(2)
        a = g.create_adset(acct, name=sname, campaign_id=CAMP, status="PAUSED", daily_budget=5000,
                           bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal=src["optimization_goal"],
                           billing_event=src["billing_event"], targeting=src["targeting"], promoted_object=src["promoted_object"],
                           attribution_spec=src.get("attribution_spec"),
                           regional_regulated_categories=src["regional_regulated_categories"],
                           regional_regulation_identities=src["regional_regulation_identities"])
        time.sleep(2)
        ad = g.create_ad(acct, name=aname, adset_id=a["id"], creative={"creative_id": cr}, status="ACTIVE")
        print(f"  ✅ «{sname}» {a['id']} (PAUSED, RM50) · creative {cr} · ad {ad['id']}")
        made += 1
        time.sleep(2)
    if made:
        c = g.get_object(CAMP, "name")
        n = len(g._get_all(CAMP + "/adsets", {"fields": "id", "limit": "20"}))
        g._request("POST", CAMP, data={"name": re.sub(r"\| 1-\d+-\d+ \|", f"| 1-{n}-{n} |", c["name"])})
        print(f"  ✅ «{g.get_object(CAMP, 'name')['name']}»")
    print("ADD3 DONE")


if __name__ == "__main__":
    main()
