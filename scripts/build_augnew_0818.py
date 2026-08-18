# -*- coding: utf-8 -*-
"""Owner-approved 2026-08-18 (plan ①+② approved step by step): the AUG NEW fleet.

  5 campaigns × 1-1-3 on BOTH accounts (30 ads total):
    {prefix} | AUG NEW A | 1-1-3   V1 接美国客户？ · V7 你最信的 · 重拍：盖电脑
    {prefix} | AUG NEW B | 1-1-3   V2 不考英文   · V8 一个客户都不用 · 重拍：我跟你讲
    {prefix} | AUG NEW C | 1-1-3   V3 Block掉他  · V9 三个不用 · 重拍：厌倦了等待
    {prefix} | AUG NEW D | 1-1-3   V4 外面有一堆人 · V5 年纪大 · V10 求人？
    {prefix} | AUG NEW E | 1-1-3   V6 小白 · V11 英文很烂 · V12 公司第一个

- RM100/day CBO each · SCHEDULED: ad set start_time 2026-08-20T00:00 MYT (campaign/
  adset/ads ACTIVE → Meta shows Scheduled; zero spend before 8/20; review runs now).
- Targeting cloned per campaign from each account's top-converting ad sets (owner-
  approved assignment: SG A/D=Travel, B/E=Broad, C=Golf Pickleball; MY A/D=Travel,
  B/E=Business Owner, C=Investment). custom_audiences stripped; everything else kept.
- Headline on ALL 30 ads (owner 2026-08-18): 🚨 教你如何在 1️⃣ 分钟内，判读市场节奏
- Captions: V1/V2/V3/V6 imported verbatim from their approved build scripts;
  重拍盖电脑 / 重拍我跟你讲 use the proven 原版 (pulled from live ads 2026-08-12);
  the other 9 are the owner-approved texts of 2026-08-18 (「文案 👌🏼」).
- Idempotent: existing campaigns get missing ads backfilled; per-account upload
  cache; V1/V2 reuse the already-uploaded per-account video ids. PACE 8s.
Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import copy as _copy
import importlib.util
import os
import time
from pathlib import Path

from adbot.clients.drive import DriveClient
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 10000            # RM100/day
START_TIME = "2026-08-20T00:00:00+0800"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, str(REPO_ROOT / "scripts" / fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_lal = _load("_blc", "build_lal_campaigns.py")
_av2 = _load("_av2", "add_video2_yingwen.py")
_v36 = _load("_v36", "add_v3_v6_broadmj.py")
SEP = _v36.SEP
BLOCK_B = _v36.BLOCK_B
_v36map = {v["key"]: v for v in _v36.VIDEOS}


def _v36cap(key: str) -> str:
    v = _v36map[key]
    return v["part1"] + SEP + BLOCK_B.format(bullet=v["bullet"])


CAP_RE_GAIDIANNAO = """⚠️ 你还在用 15 分钟、30 分钟，甚至 1 小时完成一单？
那不是认真，是方法还不够有效率。

Soo Cheng 直接把电脑盖上，因为他知道一件事：
市场很快，你要做的不是"看久一点"，而是"做对一次"。

—

很多人误会交易＝勤劳：
❌ 一直盯盘
❌ 一直分析
❌ 一直不敢离开电脑

但真相是——
如果你的方法不能让你安心关电脑，
那代表它还不够成熟。

—

Soo Cheng 用的是一套「1 分钟交易 SOP」：
⏱ 1 分钟内完成判断
⏱ 1 分钟内进场、出场
⏱ 做完就关电脑，去生活

因为一直看盘，
不会让结果更好，
只会让情绪更乱。

—

那是怎么做到的？

关键不是速度，
而是你有没有一套清楚、可复制的公式，
帮你解决 3 件事：
① 什么时候该进
② 错了怎么退
③ 风险怎么先控制

而不是靠感觉、靠猜、靠盯。

—

重点来了：
这套方法不是用自己的资金硬扛，
而是透过 Prop Firm 的机制，
用清楚的 SOP 去执行交易逻辑。

对新手来说更重要的是：
你学的不是"冲一把"，
而是一套能照着做的流程。

—

如果你也不想再：
❌ 每天被盘面绑住
❌ 一直看，却越来越不安
❌ 用时间换焦虑

Soo Cheng 即将开一场【免费线上分享会】，
完整拆解他的 1 分钟交易思路与执行方式。

📲 点击下面链接报名
先把"效率"这件事搞懂，
再决定你要不要继续走下去。"""

CAP_RE_WGN = """⚠️ 很多交易老师不敢告诉你这个事实：
交易，根本不需要看那么久。

—

你当然要分析，
但真正决定结果的，
只有一个瞬间：
👉 你下决定的那一刻，对不对。

如果你还在：
❌ 盯 15 分钟
❌ 画来画去
❌ 看到不敢离开屏幕

通常只有一个原因：
你现在的方法，还不能让你放心关电脑。

—

我只看什么？

⏱ 1 分钟。

不是乱来，
而是我会教你在这 1 分钟里，
完成该完成的事：
✔️ 判断能不能进
✔️ 知道哪里退
✔️ 风险先想好

做完，就关电脑去生活。

—

你想想看：
如果你在 1 分钟里，
已经把该做的事做完了，
你还会继续看盘吗？

不会。
你一定关电脑去喝咖啡、去走街。

—

那为什么大多数人不敢？

因为他们用的是自己的钱。
所以慢、所以怕、所以一直看。

而我用的是
👉 Prop Firm 的机制，
👉 清楚的 formula，
👉 可照着做的 SOP。

不是靠感觉，不是拼胆量，
而是一套让你敢做、敢退、敢离开的方法。

—

如果你也不想再：
❌ 被盘面绑住一整天
❌ 用时间换焦虑
❌ 看很久，却越来越乱

我接下来会有一场
【免费的线上分享会】，
把这套 1 分钟交易逻辑一次讲清楚。

📲 点击下面链接报名
先把"怎么看、怎么做、怎么退"搞懂，
再决定你要不要继续这条路。"""

P1_V4 = """🤫 外面有一堆人，
正在用一套你不知道的方式交易。

没接触过的人以为，
做 trading 一定要动用自己的血汗钱；💸
天天盯盘的人以为，
做 trading 就要牺牲全部时间；⏳
靠感觉进出的人以为，
交易根本就是一场高风险的赌博。🎲

你以为要先看懂一堆 indicator、
读财报、盯盘三五年才有资格进场？

💬 Soo Cheng 老师常说：
「我 19 岁时在大户身边倒茶水，
连 K 线是什么都看不懂。
真正决定你的，不是盯盘多久，
是你的方法对不对。」💡

✅ 一台 laptop，一分钟完成一单部署，
用的是 Prop Firm 的资金，不是自己的存款；
关电脑，去过自己的生活。

📍 想知道这套「你不知道的方式」怎么运作，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V4 = "🤫 外面那批人在用的方式：1 分钟部署 + Prop Firm 资金的完整逻辑"

P1_V5 = """☕ 40 岁以后才学交易，太迟了？
我看到的刚好相反：40、50 岁的学员，反而做得更稳。

你怕的我都懂：
怕不会用电脑，怕看不懂图表，🖥️
最怕的是——拿血汗钱去冒险。
房贷、家庭、责任，让你输不起。😮‍💨

但交易最重要的，
从来不是年轻、不是反应快，
是你有没有一套能照着做的系统。

💬 Soo Cheng 老师常说：
「成年人不敢开始，不是没能力，是输不起。
所以我们用 Prop Firm 的资金模式先练——
逻辑、风控、一步一步来，
自己的存款一分不动。」💡

✅ 不需要复杂技术，
40、50 岁一样一步一步跟着 SOP 上手。

📍 先了解规则，再决定适不适合你，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V5 = "🛡️ 40+ 的入门路线：不动老本、先学风控、照 SOP 一步一步来"

P1_V7 = """⚠️ 你交易这么多年，最信的是什么？
是你的「感觉」——而它，正是你一直输的原因。

「我觉得它会起」，
「我觉得差不多可以进了」，
「我觉得再等一下」。🤔

赢的时候，你以为是自己厉害；
输的时候，你不知道错在哪里；
下一次同样的情况，你还是做同样的决定。😵‍💫

因为你手上，没有一把尺。📏

💬 Soo Cheng 老师常说：
「我教的，就是把感觉换成一把尺——
什么信号才进、什么情况坚决不动、
几时 set 止损、几时离场，
不是靠你今天心情好不好。」💡

✅ 再配 Prop Firm 的资金去操作，
本金不用直接下场，
你才不会因为一个「怕」字，又回去靠感觉乱做。

📍 做了很久还是不稳的，缺的可能不是努力，是系统，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V7 = "📏 把「感觉」换成一把尺：信号 / 不动 / 止损 / 离场全部写死"

P1_V8 = """🙅 同样是赚 MJ——
别人叫你去接 angmo 客户，我这方法，一个客户都不用。

网上教你赚 MJ 的，
几乎都叫你去接美国客户：
要半夜爬起来配合美国时间，🌙
要一直 chase 单、一直做 sales，
一个普通打工的，光想就累了。😮‍💨

老实讲，AI 现在谁都会用，
美国人玩得比我们还熟——
他凭什么要来找你？这条路只会越来越挤。

💬 Soo Cheng 老师常说：
「你赚的 MJ，不是伺候谁来的，
是你自己直接参与美国市场。
没有客户，就没有那一堆烦事——
照跟 SOP，看到 signal 才动手，做完就走。」💡

✅ 你不用变成另一个人，你还是你。
先讲白：想快快捞一票的，别来；
我要的是肯跟 system、有纪律、想做长的人。

📍 想看这条不用客户的路怎么走，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V8 = "🗝️ 不接客户直接参与市场：看懂涨跌 / set 风控 / Prop Firm 资金怎么用"

P1_V9 = """✋ 想在马来西亚赚 MJ？
很多人以为要飞出国、要接美国客户、要整天守电脑——这三样，一样都不用。

你是不是也想过：
「赚 MJ 是别人的事啦，
我一个普通打工的，哪里有办法。」😔

因为你看到的路条条都辛苦：
出国打工要离乡背井，✈️
接美国客户要英文要 sales 要追单，
搞到最后人很累，钱又没多多少。

💬 Soo Cheng 老师常说：
「我走的是另一条路：
不用出国——人在大马，做的是美国市场；
不用客户——自己看市场、自己做决定；
不用整天盯盘——看到 signal 才出手，做完收工。」💡

✅ 几时进、几时出、止损 set 在哪，
一套写死的 SOP 全部讲清楚，
不是靠今天心情好不好。

先讲白：想赌一把快快发达的，这里帮不到你。

📍 肯跟着做、有纪律的，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V9 = "✋ 三个不用的玩法：不出国、不接客户、不盯盘，怎么照 SOP 执行"

P1_V10 = """🙇 想赚 MJ，就一定要这样求人？
不是的——因为你可以不赚「人」的钱，赚「市场」的钱。

一听到赚 MJ，大部分人马上想到五样：
❌ 要去接美国客户
❌ 英文要够好
❌ 要半夜爬起来开会
❌ 要一直 follow up 等人下单
❌ 经济一差，第一个被砍的就是你

光是想，就已经很累了，对不对？😮‍💨

💬 Soo Cheng 老师常说：
「美国的市场天天都开，
它不看你的英文，不用你 follow up，
更不需要你半夜求人——
不是赚人的钱，是赚市场的钱。」💡

✅ 一套 SOP 操作美国期货市场（本来就是 MJ 计价），
一开始不掏自己的血汗钱，
用 Prop Firm 提供的资金：
判断进场、设好风险、完成部署，关电脑。

📍 想看这条不求人的路，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V10 = "🙇 为什么赚 MJ 不用求人：赚「市场」的钱的完整玩法"

P1_V11 = """🫣 讲真的，我英文烂到自己都不好意思，
但我照样在赚 MJ——因为市场，不看你的英文。

别人跟你讲，赚 MJ 要接美国客户：
英文不好，怎么开会？怎么报价？怎么谈？😰
光这一关，就把你挡在门外好几年。

但你打开图表看看：
K 线就是 K 线，
红色就是跌，绿色就是涨，全世界都一样。🕯️
它不会因为你英文烂，就给你比较差的价钱。

💬 Soo Cheng 老师常说：
「这条路上，没有一句英文是你必须开口讲的。
你只需要看得懂市场给你的信号，
照着 SOP 出手——
靠的是纪律，不是英文。」💡

✅ 用 Prop Firm 的资金操作美国期货市场：
判断进场、设好风险、完成部署，收工。
我教过的学员里，很多人英文比我还差，一样学会。

📍 英文烂不烂，跟你能不能学交易没关系，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V11 = "🕯️ K 线没有英文：从价格信号判断买卖力量的入门方法"

P1_V12 = """🪓 AI 一出来，大公司一间接一间在裁人。
如果哪天轮到你——你手上，还有第二手准备吗？

现在最危险的不是没钱，
是你只有一份工：☝️
公司要砍预算，第一个被砍的可能就是你，
因为你的收入，握在别人手上。😨

但市场不一样：
会涨，也会跌，
涨的时候可以出手，跌的时候一样有机会出手。📊
你不需要「等经济好」。

💬 Soo Cheng 老师常说：
「先讲清楚——这不是叫你辞工，更不是稳赚。
这是让你多一样自己掌握的技能，
不用把全部身家，压在一份工、一个老板身上。」💡

✅ 一套 SOP 配 Prop Firm 的资金操作美国期货：
判断方向、控制风险、照规则走，不靠运气。
想赌一把快点发达的，这里不适合你。

📍 有一份工、有一点存款、怕哪天风一吹什么都没有的，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_V12 = "🪓 收入只有一份工的风险：怎么用规则市场给自己多一样技能"

P1_RE_YJ = """⏳ 厌倦了等待？
你的单子，是不是还在用 15 分钟、甚至 1 个小时来完成？

等确认、等回调、等「再看一下」，
等到机会走完，你才追进去，😬
然后又是一次不甘愿的止损。

其实 market 很快，
你要的不是看更久，
是效率——快、狠、准。⚡

💬 Soo Cheng 老师常说：
「1 分钟里面，完成你的单子：
进场、出场、抓准时机，
一分钟做完交易部署——
效率，就是你的武器。」💡

✅ 重点来了：我们不拿自己的本金去冒险，
学的是怎么通过 Prop Firm 的资金审核，
用机构的资金操盘，本金一分不动。

📍 想学这套 1 分钟极速交易策略，
点击下方，报名免费的【1 分钟交易攻略】线上分享会。🎯"""
B_RE_YJ = "⚡ 效率是武器：1 分钟进场出场、完成部署的完整流程"


def _nc(p1: str, bullet: str) -> str:
    return p1 + SEP + BLOCK_B.format(bullet=bullet)


VIDEOS = {
    "v1": {"name": "Video 1：赚美金，一定要接美国客户？", "file": None,
           "media": {"SG": "1397401099009914", "MY": "1569053221675935"},
           "cap": _lal.CAPTION},
    "v2": {"name": "Video 2：市场不考你的英文", "file": None,
           "media": {"SG": "1336717308449971", "MY": "2040235940700033"},
           "cap": _av2.CAPTION},
    "v3": {"name": "Video 3：Block掉他！", "file": "1Cz6iyrJdiSHRFDs7vTEjQ0-u5H-mkicb",
           "cap": _v36cap("v3")},
    "v4": {"name": "Video 4：外面有一堆人，正在用你不知道的方式交易",
           "file": "1EqIkZx78NM3TrIqYw0xeqMghdoP2KYZn", "cap": _nc(P1_V4, B_V4)},
    "v5": {"name": "Video 5：年纪大的人做不了交易？",
           "file": "1qPnxsYkqCGVwvWXBrQ8oDR5lYDUJMRO7", "cap": _nc(P1_V5, B_V5)},
    "v6": {"name": "Video 6：马来西亚小白怎样赚美金？",
           "file": "1l497Oy5SbZCxoh0VIaI87qkvCFYe0Uhw", "cap": _v36cap("v6")},
    "v7": {"name": "Video 7：你最信的那个东西，正在害你",
           "file": "1LJc_VPFAvbOYrMG4Myc_VU2MzjRQfDSV", "cap": _nc(P1_V7, B_V7)},
    "v8": {"name": "Video 8：一个客户都不用",
           "file": "1UecstOBHT5PO4rJfSOXI6f1mDZhJaFWi", "cap": _nc(P1_V8, B_V8)},
    "v9": {"name": "Video 9：三个不用",
           "file": "1RkjS0ZWfPPmJHH0eQDB4wQ9jx7sCEZsZ", "cap": _nc(P1_V9, B_V9)},
    "v10": {"name": "Video 10：赚美金 = 求人？",
            "file": "1cVd2EvhOz1RzeIvmOHG-rQ0wnqHGscJj", "cap": _nc(P1_V10, B_V10)},
    "v11": {"name": "Video 11：我英文很烂",
            "file": "1Rg36DKGMaX_4n6Grio9Y8oaPGIq6de6O", "cap": _nc(P1_V11, B_V11)},
    "v12": {"name": "Video 12：公司第一个的是你",
            "file": "1znG9yTSZeZiE5Kb6Zj82uwJFhqNW7H3c", "cap": _nc(P1_V12, B_V12)},
    "re_yj": {"name": "重拍：厌倦了等待",
              "file": "1HKzEQgJ4LIGcKsBCCp9u36K-IIEc-wZ9", "cap": _nc(P1_RE_YJ, B_RE_YJ)},
    "re_gdn": {"name": "重拍：Video 5：盖电脑，喂！",
               "file": "16pus-BidOKVjRkDto6jJzkVYBdAo04nI", "cap": CAP_RE_GAIDIANNAO},
    "re_wgn": {"name": "重拍：Video 6：我跟你讲！",
               "file": "1fL5pSTouw78eyvOPozruucTrgCBs76yp", "cap": CAP_RE_WGN},
}

CAMPAIGNS = [
    ("A", ["v1", "v7", "re_gdn"]),
    ("B", ["v2", "v8", "re_wgn"]),
    ("C", ["v3", "v9", "re_yj"]),
    ("D", ["v4", "v5", "v10"]),
    ("E", ["v6", "v11", "v12"]),
]

# targeting-source ad sets (cloned; custom audiences stripped)
TGT = {
    "SG": {"A": "120248575728300521", "B": "120248220658780521",
           "C": "120248220644070521", "D": "120248575728300521",
           "E": "120248220658780521"},
    "MY": {"A": "120247919645810575", "B": "120247585352830575",
           "C": "BY_NAME:adset (investment interests | my 25+)",
           "D": "120247919645810575", "E": "120247585352830575"},
}
TGT_LABEL = {
    "SG": {"A": "Travel", "B": "Broad", "C": "Golf Pickleball", "D": "Travel", "E": "Broad"},
    "MY": {"A": "Travel", "B": "Business Owner", "C": "Investment", "D": "Travel",
           "E": "Business Owner"},
}

ACCTS = [
    {"label": "SG", "cfg": "config.sg.yaml", "sg": True, "prefix": "[SG] STOCKBLOOM",
     "geo": ["SG"]},
    {"label": "MY", "cfg": "config.yaml", "sg": False, "prefix": "STOCKBLOOM",
     "geo": ["MY"]},
]


def resolve_tgt_source(g, acct: str, ref: str):
    if not ref.startswith("BY_NAME:"):
        return g.get_object(ref, "id,name,targeting,promoted_object")
    from adbot import cpa
    want = ref.split(":", 1)[1]
    for a in g._get_all(f"{acct}/adsets", {"fields": "id,name,targeting,promoted_object",
                                           "limit": "500"}):
        if cpa.norm(a.get("name") or "") == want:
            return a
    raise SystemExit(f"⛔ ad set named «{want}» not found on {acct}")


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"AUG NEW fleet · 5×1-1-3 × MY+SG · RM{DAILY/100:.0f}/day · "
          f"scheduled {START_TIME} — {mode}\n")

    paths: dict = {}
    if CONFIRM:
        base = load_settings(REPO_ROOT / "config" / "config.yaml")
        drive = DriveClient(base.secrets.google_sa_json)
        for key, v in VIDEOS.items():
            if v["file"]:
                paths[key] = drive.download_file(v["file"], Path(f"/tmp/augnew_{key}.mp4"))
                print(f"  ⬇ {v['name']}")
        print()

    for ac in ACCTS:
        s = load_settings(REPO_ROOT / "config" / ac["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"══ {ac['label']}  {acct} ══")

        sources = {}
        for cl, _keys in CAMPAIGNS:
            ref = TGT[ac["label"]][cl]
            if ref not in sources:
                src = resolve_tgt_source(g, acct, ref)
                tgt = _copy.deepcopy(src.get("targeting") or {})
                tgt.pop("custom_audiences", None)
                tgt.pop("excluded_custom_audiences", None)
                n_flex = sum(len(v) for spec in (tgt.get("flexible_spec") or [])
                             for v in spec.values())
                sources[ref] = {"tgt": tgt, "promo": src.get("promoted_object") or {},
                                "desc": f"«{src.get('name')}» ({n_flex} keywords)"}
                time.sleep(1)

        existing = {c.get("name"): c.get("id") for c in
                    g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
        uploaded: dict = {}

        def media(key: str):
            v = VIDEOS[key]
            if v["file"] is None:
                vid = v["media"][ac["label"]]
                if key not in uploaded:
                    uploaded[key] = (vid, g.get_video_thumbnail(vid))
                    print(f"     ↺ reuse video {vid}  «{v['name']}»")
                return uploaded[key]
            if key not in uploaded:
                vid = g.upload_video(acct, str(paths[key]), v["name"])
                time.sleep(PACE)
                uploaded[key] = (vid, g.get_video_thumbnail(vid))
                print(f"     ⬆ video {vid}  «{v['name']}»")
            return uploaded[key]

        for cl, keys in CAMPAIGNS:
            camp_name = f"{ac['prefix']} | AUG NEW {cl} | 1-1-3"
            aset_name = f"AdSet (Aug New {cl} | {ac['label']} 25+)"
            ref = TGT[ac["label"]][cl]
            src = sources[ref]
            try:
                camp_id = existing.get(camp_name)
                if camp_id:
                    print(f"  · '{camp_name}' exists ({camp_id}) — checking for missing ads")
                    casets = g._get_all(f"{camp_id}/adsets", {"fields": "id", "limit": "5"})
                    if not casets:
                        print("    ‼️ no ad set inside — manual check needed, skipping")
                        continue
                    aset_id = casets[0]["id"]
                else:
                    if not CONFIRM:
                        print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO "
                              f"ACTIVE·scheduled {START_TIME}")
                        print(f"     targeting[{TGT_LABEL[ac['label']][cl]}] from {src['desc']}"
                              + ("  · SG binding" if ac["sg"] else ""))
                        for k in keys:
                            print(f"       ad  «{VIDEOS[k]['name']}»")
                        continue
                    camp = g.create_campaign(
                        acct, name=camp_name, objective="OUTCOME_SALES",
                        buying_type="AUCTION", daily_budget=DAILY,
                        bid_strategy="LOWEST_COST_WITHOUT_CAP",
                        special_ad_categories=s.meta.special_ad_categories,
                        special_ad_category_country=ac["geo"], status="ACTIVE")
                    camp_id = camp["id"]
                    print(f"  ✓ campaign {camp_id}  '{camp_name}'")
                    time.sleep(PACE)
                    aset_kwargs = dict(
                        name=aset_name, campaign_id=camp_id,
                        optimization_goal="OFFSITE_CONVERSIONS",
                        billing_event="IMPRESSIONS", promoted_object=src["promo"],
                        targeting=src["tgt"], status="ACTIVE", start_time=START_TIME)
                    if ac["sg"]:
                        aset_kwargs.update(regional_regulated_categories=REGIONAL,
                                           regional_regulation_identities=REG_IDENTITIES)
                    aset = g.create_adset(acct, **aset_kwargs)
                    aset_id = aset["id"]
                    print(f"  ✓ adset {aset_id}  start_time={START_TIME}")
                    time.sleep(PACE)

                if not CONFIRM:
                    continue
                have = {a.get("name") for a in g._get_all(
                    f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
                for k in keys:
                    v = VIDEOS[k]
                    if v["name"] in have:
                        print(f"     ✓ «{v['name']}» already present — skip")
                        continue
                    vid, thumb = media(k)
                    video_data = {"video_id": vid, "title": HEADLINE, "message": v["cap"],
                                  "call_to_action": {
                                      "type": s.meta.call_to_action or "LEARN_MORE",
                                      "value": {"link": s.meta.lead_destination.link_url}}}
                    if thumb:
                        video_data["image_url"] = thumb
                    spec = {"name": f"{ac['label']} | AUG NEW {cl} | {v['name']}",
                            "object_story_spec": {"page_id": s.meta.page_id,
                                                  "video_data": video_data}}
                    if s.meta.url_tags:
                        spec["url_tags"] = s.meta.url_tags
                    cr = g.create_adcreative(acct, **spec)
                    ad = g.create_ad(acct, name=v["name"], adset_id=aset_id,
                                     creative={"creative_id": cr["id"]}, status="ACTIVE",
                                     conversion_domain=conv)
                    print(f"     ✓ ad {ad['id']}  «{v['name']}»")
                    time.sleep(PACE)
            except GraphError as e:
                print(f"  ❌ {camp_name}: {e} — continuing")
        print()

    print("DONE — AUG NEW fleet built, everything scheduled to start 2026-08-20 00:00 MYT."
          if CONFIRM else "DRY-RUN — set confirm=true to build.")


if __name__ == "__main__":
    main()
