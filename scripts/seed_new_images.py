# -*- coding: utf-8 -*-
"""Create the 12 new single-image rows (Image 23..34) in the Notion Content Pipeline DB,
each with Title / Hook / Caption (approved Part 1 + the fixed 下半段, only the 5th curriculum
bullet swapped per angle). Status left default (NOT In Review — owner preference).
Idempotent: skips a row whose Title already exists. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.clients.notion import rich_text_property, title_property
from adbot.commands import notion_client
from adbot.notion_captions import _title_text, content_id_from_title
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

TAIL = """══════════

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
___BULLET___

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名"""

# (N, title_desc, hook, bullet, part1)
ROWS = [
    (23, "英文不好也能做交易（门外）", "英文不好，也能做交易",
     "📊 看的是 K 线不是英文——中文就能学会看图表",
     """💰 有资金、有想法，却因为一句「我英文不好」，就把自己挡在了门外？
你以为做外国市场要先啃完英文、看懂那些英文新闻，结果一年拖一年，始终没开始。

Soo Cheng 老师常说：做交易，你面对的是图表，不是老外的脸色。
市场从不看你的英文，只看你懂不懂 K 线、信号、进出场。

📍 英文不好照样能从 0 看懂——Soo Cheng 老师会在免费线上分享会里一步步带你走。"""),

    (24, "盯盘 8 小时不如 1 分钟 · SOP", "盯盘 8 小时，不如 1 分钟做对一个决定",
     "🧠 拉开差距的不是盯多久，是有没有一套写死的 SOP",
     """⏱️ 一天盯盘 8 小时，到头来该赚的没赚、该跑的没跑，问题到底出在哪？
你不是不够勤力，是方法错了——盯得越久越焦虑，越焦虑越乱按，人先熬垮了。

Soo Cheng 老师常说：真正拉开差距的不是你盯多久，是你有没有一套写死的 SOP。
看到条件才动，1 分钟做对一个决定，其他时间还给你的生意和生活。

📍 这套 1 分钟 SOP 长什么样，Soo Cheng 老师会在免费线上分享会里带你走一遍。"""),

    (25, "市场每天都开 · 主动权", "不用等客户上门，市场每天都开",
     "🗓️ 市场每天都开：不用等谁，你决定几点开工",
     """⏰ 你的收入，是不是一直在「等别人」——等客户回复、等老板点头、等别人先松口？
赚多赚少好像都握在别人手里，时间从来不是自己的，你越来越不甘心，却找不到出口。

Soo Cheng 老师常说：市场每天都开，不用等谁来找你，你决定几点开工。
主动权，这一次真的握在自己手上。

📍 怎么给自己搭一条「自己说了算」的现金流，Soo Cheng 老师会在免费分享会里讲给你听。"""),

    (26, "市场跌你有做法 · 做多做空", "市场跌，别人慌，你有做法",
     "📈 为什么用期货：买涨买跌都做得到，跌时也有做法",
     """📉 市场一跌，你是不是只会慌、只会干等它「回来」？
涨的时候人人是高手，一跌才看出谁真有做法——多数人只会做多，一跌就套牢，越等越深。

Soo Cheng 老师常说：涨和跌本就是市场的两面，真正稳的人做多、做空都知道怎么应对。
不靠猜，靠的是策略和方向。

📍 跌的时候到底该怎么做，Soo Cheng 老师会在免费线上分享会里把完整做法讲清楚。"""),

    (27, "做交易不用求人（已读不回）", "做交易，不用求人",
     "🧭 一个人就能执行：不用求人、不用看谁脸色",
     """💬 做生意做到现在，你最累的其实不是做事，是 pitch 完、报价完，然后盯着那三个字：「已读不回」。
被比价、被放鸽子、被晾着，你的收入一直捏在别人手里。

Soo Cheng 老师常说：做交易不一样，你面对的是市场，不是人。
不用求人、不用 chase、不用看谁脸色，你要说服的只有你自己的纪律。

📍 这套「一个人就能做」的方法，Soo Cheng 老师免费带你走一遍。"""),

    (28, "英文不好也能做外国市场（等准备好）", "英文不好，也能做外国市场",
     "🧠 别再「等英文好了再说」：看懂方法，中文就够",
     """🌏 想做外国市场，你是不是一直卡在同一句话：「等我英文再好一点，再开始」？
结果一等就是好几年——补了英文、看了新闻，交易却始终没真正动起来。

Soo Cheng 老师常说：做交易，你面对的是图表，不是老外的脸色。
市场不管你英文多好，只看你懂不懂方法。

📍 怎么从看懂一根 K 线、知道下一步该怎么做开始，Soo Cheng 老师会在免费分享会里带你走。"""),

    (29, "做交易不需要英文很好（图表）", "做交易，不需要英文很好",
     "📊 看懂 K 线 / 信号 / 进出场：不需要先懂英文",
     """📈 一打开图表，满屏 EURUSD、一堆英文，你是不是手一抖就关掉了？
「这是英文好的人才玩得起的吧」——你不是不想做，是被「语言」这两个字先吓退了。

Soo Cheng 老师常说：你真正要读懂的从来不是英文，是那根 K 线在告诉你什么。
什么时候有信号、什么时候进、什么时候出，这套「语言」中文就能学会。

📍 怎么从看懂一根 K 线开始，Soo Cheng 老师会在免费线上分享会里讲给你听。"""),

    (30, "交易不稳缺的是流程不是天赋", "交易做不稳，缺的不是天赋，是流程",
     "🧠 时好时坏不是天赋，是缺一套「每次都照做」的流程",
     """📉 同样的市场，别人稳稳地赚，你却时好时坏、赢一次亏两次，是不是开始怀疑自己没天分了？
其实不是天分的问题，你缺的是那一套「每次都照做」的东西。

Soo Cheng 老师常说：你缺的从来不是天赋，是一套流程。
看到什么信号、做什么动作、什么时候收手，全部写死，不靠那天的心情。

📍 方法对了，小白也能从 0 做起——Soo Cheng 老师会在免费分享会里手把手带你。"""),

    (31, "市场不会已读不回 · 一个人就能做", "你面对的是市场，不是人",
     "🧭 signal 来了就是来了：市场不会「已读不回」",
     """📵「请问还在考虑吗？」发出去半天，对方「已读不回」，这种滋味你是不是太熟了？
你最花时间的从来不是把事做好，是等别人回你、看别人心情。

Soo Cheng 老师常说：市场不会已读不回，signal 来了就是来了。
你面对的是图表，不是谁的脸色——看懂 K 线、信号、进出场，一个人就能做。

📍 怎么靠自己的纪律赚属于自己的那一份，Soo Cheng 老师会在免费分享会里带你走一遍。"""),

    (32, "第一步不是先掏钱 · 先有方法", "开始交易第一步，不是先掏钱",
     "🧠 顺序别搞反：先有方法、再验证，资金是最后一环",
     """💸 一想到做交易，你脑子里的第一个问题，是不是「我要先放多少本」？错，就错在这第一步。
钱准备得很快，方法却一片空白，本金一进场靠的还是感觉，亏的还是自己。

Soo Cheng 老师常说：第一步从来不是先掏钱，是先有一套方法。
先有方法、再验证，资金反而是最后最容易解决的一环。

📍 正确的第一步怎么走，Soo Cheng 老师会在免费线上分享会里免费教你。"""),

    (33, "会交易的人早就关电脑走人了", "会交易的人，早就关电脑走人了",
     "🧠 为什么盯盘越久反而越亏：会做的人早就关电脑走人",
     """💻 以为盯盘盯得越久、赚得越多？真正会交易的人，早就关掉电脑走人了。
天天守屏幕、连去趟厕所都怕错过的，多半是新手——累的是你，乱的也是你。

Soo Cheng 老师常说：老手靠的是一套 SOP，不是靠坐得久。
看到什么信号、做什么动作，全部写死成流程，做完就关机。

📍 Trade smarter, not longer——这套流程 Soo Cheng 老师会在免费分享会里带你走一遍。"""),

    (34, "用别人的资金 · Prop Firm", "用别人的资金操作，是什么概念？",
     "🔍 Prop Firm 资金机制：证明你有方法，本金一分不动",
     """🏦 有一笔钱躺在户头里，你一直不敢动——怕判断错、怕辛苦攒的本金一夜缩水，对吗？
想让它动起来又怕一动就回不去，于是它一直「等」，眼看购买力一年年缩水。

Soo Cheng 老师常说：其实你不用拿自己的本金去冒险。
你证明自己有方法，Prop Firm 就给你资金授权——用机构的钱操盘，本金一分不动。

📍 门槛、规则、怎么通过全部有迹可循，Soo Cheng 老师会在免费线上分享会里从头带你理解。"""),
]


def main() -> None:
    s = load_settings()
    n = notion_client(s)
    db = s.notion.database_id
    existing = set()
    for page in n.query_database(db):
        cid = content_id_from_title(_title_text(page.get("properties", {})))
        if cid:
            existing.add(cid)
    print(f"CONFIRM={CONFIRM}  db={db}  existing image/video rows={len(existing)}\n")

    for N, desc, hook, bullet, part1 in ROWS:
        cid = f"image_{N}"
        title = f"Image {N}：{desc}"
        caption = part1.rstrip() + "\n\n" + TAIL.replace("___BULLET___", bullet)
        if cid in existing:
            print(f"· {title} — {cid} already exists, skip")
            continue
        if not CONFIRM:
            print(f"WOULD CREATE «{title}»  hook={hook!r}  caption={len(caption)} chars")
            continue
        props = {
            "Title": title_property(title),
            "Hook": rich_text_property(hook),
            "Caption": rich_text_property(caption),
        }
        page = n._request("POST", "pages",
                          json_body={"parent": {"database_id": db}, "properties": props})
        print(f"✓ {title} -> {page.get('id')}  (caption {len(caption)} chars)")
    print("\nDONE — 12 rows seeded (Status default)." if CONFIRM else "\nDRY-RUN.")


if __name__ == "__main__":
    main()
