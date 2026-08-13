# -*- coding: utf-8 -*-
"""Owner 2026-08-13 «帮我上新广告» (scripts provided): add the two new MJ-series videos

  «Video 3：Block掉他！»                (SOOCHENG Video 03, creatives copy)
  «Video 6：马来西亚小白怎样赚美金？»  (SOOCHENG Video 06, creatives copy)

into both BROAD MJ campaigns (1-1-2 -> 1-1-4) — the V-series broad home. Captions are
马丁 Block A anchored on each video's own script + the fixed Block B (one swapped
bullet); 美金 written as MJ per standing rule; the video's 「越懒惰越赚钱」 line is NOT
used in the caption (income-claim risk stays in-video only).

Ads created PAUSED; idempotent by ad name; PACE 8s. Dry-run unless CONFIRM=true.
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
PACE = 8.0

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

VIDEOS = [
    {"key": "v3", "file": "1Cz6iyrJdiSHRFDs7vTEjQ0-u5H-mkicb",
     "ad_name": "Video 3：Block掉他！",
     "headline": "谁说一定要盯盘？Block 掉他！",
     "bullet": "🧠 为什么越「勤力」盯盘越不敢出手：把力气花对地方的 SOP",
     "part1": """🚫 谁说 trading 一定要盯盘一整天？
Block 掉他！快点 Block 掉他！

你有没有发现一个奇怪的现象：🤔
越是拼命盯盘、拼命上课的人，
反而越不敢出手；
越是「懒惰」只看条件的人，
反而做得越稳。

不是努力没用，
是你的努力用错了地方——
盯得越久，情绪越多，
决定反而越乱。😵‍💫

💬 Soo Cheng 老师常说：
「我每天用不到 1 小时，
甚至不用 15 分钟就做完交易。
不是我厉害，是 SOP 在替我工作——
进、出、止损写死了，人只负责执行。」💡

✅ 这里的「懒」，
是把力气花在规则上，不是花在盯盘上。

📍 想知道这套「懒人 SOP」长什么样，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""},

    {"key": "v6", "file": "1l497Oy5SbZCxoh0VIaI87qkvCFYe0Uhw",
     "ad_name": "Video 6：马来西亚小白怎样赚美金？",
     "headline": "马来西亚小白怎样赚 MJ？",
     "bullet": "🧭 判断方向、进场点、风险控制：一套固定流程建立自己的系统",
     "part1": """🇲🇾 马来西亚小白想赚 MJ，
一定要学 AI、找美国客户、接海外订单？

一讲到赚 MJ，你脑里是不是马上跳出这三样？💭
然后越想越复杂，
「算了吧，我一个普通人，哪有这个本事」。😮‍💨

其实赚 MJ，不一定要靠这些。
你可以透过交易，直接参与 MJ 计价的市场——
不用客户，不用订单，不用会英文。

💬 Soo Cheng 老师常说：
「我们做的事，就是把复杂的交易逻辑变简单：
不用学复杂技术，不靠 signal，不靠运气，
一步一步照着 SOP 走，小白也上手得来。」💡

✅ 分享会里会讲三样东西：
为什么新手一开始都犯同样的错、
怎么用一套固定流程判断方向 / 进场 / 控风险、
怎么建立自己的交易系统——不用等别人喂 signal。

📍 想参与 MJ 计价的市场，建立自己的交易能力，
点击下方，报名免费的【1 分钟短线交易攻略】线上分享会。🎯"""},
]

ACCTS = [
    {"label": "SG", "cfg": "config.sg.yaml", "campaign": "120248835876710521",
     "adset": "120248835880300521"},
    {"label": "MY", "cfg": "config.yaml", "campaign": "120248248921210575",
     "adset": "120248248922280575"},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Add V3 + V6 to BROAD MJ (both accounts) — {mode}\n")

    paths = {}
    if CONFIRM:
        base = load_settings(REPO_ROOT / "config" / "config.yaml")
        drive = DriveClient(base.secrets.google_sa_json)
        for v in VIDEOS:
            paths[v["key"]] = drive.download_file(v["file"], Path(f"/tmp/soocheng_{v['key']}.mp4"))
            print(f"  ⬇ {v['ad_name']} -> {paths[v['key']]}")
        print()

    for ac in ACCTS:
        s = load_settings(REPO_ROOT / "config" / ac["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"══ {ac['label']}  {acct} ══")
        try:
            camp = g.get_object(ac["campaign"], "name,effective_status")
            print(f"  campaign «{camp.get('name')}» ({camp.get('effective_status')})")
            if "broad mj" not in (camp.get("name") or "").lower():
                print("  ⛔ campaign name check failed — skipping account")
                continue
            have = {a.get("name") for a in g._get_all(
                f"{ac['campaign']}/ads", {"fields": "name", "limit": "50"})}
            for v in VIDEOS:
                if v["ad_name"] in have:
                    print(f"  ✓ «{v['ad_name']}» already present — skip")
                    continue
                if not CONFIRM:
                    print(f"  ▶ would add «{v['ad_name']}» (PAUSED)")
                    continue
                vid = g.upload_video(acct, str(paths[v["key"]]), v["ad_name"])
                time.sleep(PACE)
                thumb = g.get_video_thumbnail(vid)
                caption = v["part1"] + SEP + BLOCK_B.format(bullet=v["bullet"])
                video_data = {"video_id": vid, "title": v["headline"], "message": caption,
                              "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                                 "value": {"link": s.meta.lead_destination.link_url}}}
                if thumb:
                    video_data["image_url"] = thumb
                spec = {"name": f"{ac['label']} | BROAD MJ | {v['ad_name']}",
                        "object_story_spec": {"page_id": s.meta.page_id,
                                              "video_data": video_data}}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **spec)
                ad = g.create_ad(acct, name=v["ad_name"], adset_id=ac["adset"],
                                 creative={"creative_id": cr["id"]}, status="PAUSED",
                                 conversion_domain=conv)
                print(f"  ✓ ad {ad['id']}  «{v['ad_name']}»")
                time.sleep(PACE)
        except GraphError as e:
            print(f"  ❌ [{ac['label']}] {e} — continuing")
        print()

    print("DONE — BROAD MJ now 1-1-4 per account; new ads PAUSED, owner activates."
          if CONFIRM else "DRY-RUN — set confirm=true to apply.")


if __name__ == "__main__":
    main()
