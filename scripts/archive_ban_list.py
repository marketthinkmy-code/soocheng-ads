"""Archive the ban forensics to Notion (owner-approved 2026-07-12): one page in the
Content Pipeline DB titled with ⛔ — notion_captions skips non-"Video N：/Image N："
titles, so this row can never confuse a build.

Dry-run unless CONFIRM=true. Creates ONE page; re-running creates another (delete dupes
in Notion UI if run twice).
"""
from __future__ import annotations

import os

from adbot.commands import notion_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

TITLE = "⛔ 禁跑名单 · MTC X STOCKBLOOM 2 被封取证（2026-07-12）"


def h2(t):
    return {"heading_2": {"rich_text": [{"text": {"content": t}}]}}


def h3(t):
    return {"heading_3": {"rich_text": [{"text": {"content": t}}]}}


def p(t, bold=False):
    return {"paragraph": {"rich_text": [{"text": {"content": t},
                                         "annotations": {"bold": bold}} if bold
                                        else {"text": {"content": t}}]}}


def b(t):
    return {"bulleted_list_item": {"rich_text": [{"text": {"content": t}}]}}


BLOCKS = [
    h2("官方结论（API 取证 2026-07-12）"),
    p("account_status = 2 (DISABLED) · disable_reason = 1 (ADS_INTEGRITY_POLICY 广告诚信政策违规)。"
      "Meta 审查 7/10–7/11 扫过全账号逐个下架广告后封号。旧账号 MyTrade50 6/23 已被封过一次（重犯权重）。"),

    h2("⛔ 永久禁跑名单（连名带素材都不要再上）"),
    b("video 3：不是怕交易 — 视频 vid 2770424979983940 — SG 1-1-9 正式被拒；合规重建也被拒（视频本身违规）"),
    b("Video 4: 厌倦了等待 — 视频 vid 1615514406147821 — SG 1-1-4 正式被拒；合规重建也被拒（视频本身违规）"),
    b("single image 5：moomoo — 图片 img 38371d44c3ee5492f5eba9160d3c311b — SG 1-1-9 正式被拒"),
    b("video 1: 1 分钟赚 300 — 名字即收入承诺；纸板道具写「每周多 美$200-300」"),
    b("single image: 每天 1 分钟就能盈利 — 名字即收入承诺；MY+SG 两份 7/11 均被 review 下架"),
    b("Video 2（谁讲trading一定要~ 脚本）— 口播「每个星期有多 200-300块 US Pocket钱」+ 喝茶看手机收钱画面"),
    b("video 2：你敢吗？ — owner 报告 2026-07-16 被拒（此前是成交素材，停止 relaunch/scale；原因待 issues_info 核实）"),
    b("freestyle 2 — owner 报告 2026-07-16 被拒（GOLF；SG 版此前已 DISAPPROVED 删除，MY 版此次亦被拒）"),
    b("video 12：炒过那么多，累而且不稳定 — owner 报告 2026-07-16 被拒（原为上升素材，立即停止 scale）"),

    h2("🔍 逐支视频脚本违规点（2026-07-12 脚本核对）"),
    h3("共同违规 DNA（几乎每支视频的结尾都有同一段）"),
    b("「我们用 Prop Firm，用别人的资金，去赚(取)属于自己的交易回报」→ 用别人钱赚钱 = 违规"),
    b("「在零本钱的情况之下，去开始交易期货」→ 零本钱+期货 = 无风险暗示，违规"),
    b("Pop-up 成绩/result/TP 截图 BROLL → 收益证明画面，违规（老账号被封主因之一）"),
    b("「每周/每天 200-300 USD pocket 钱」任何形式（口播/字幕/道具纸板）→ 硬违规"),
    b("「proven works 公式 / copy paste 跟着做就会」→ 轻松赚钱框架，高风险"),

    h3("Video 1：1 分钟赚 300"),
    b("Scene 1 纸板道具「每周多 ➡️ 美$ 200- 300」＋「用我的方法，你每天就可以有将多的回报」→ 必删"),
    b("「proven works 的公式，很多学员已经验证过」→ 改为「一套可以照做的 SOP，免费课里完整讲解」"),

    h3("Video 2：谁讲trading一定要~"),
    b("「我每天只需要用 1分钟就能做到每个星期有多 200-300块 US Pocket钱」→ 必删"),
    b("「喝茶+看手机就收钱」画面 → 必删"),
    b("「你也可以做到 200到300块的 US pocket 钱」→ 必删"),

    h3("Video 3：不是怕交易（重建也被拒的原因）"),
    b("「我以前月薪不到RM3,000」→ 收入数字，删或改「以前是打工族」"),
    b("「翻转收入、换掉旧生活」＋旅行照 → 收入转变叙事，必删"),
    b("「2,000 多个学员照着做，结果是这样（pop out result）」→ 成绩截图必删"),
    b("「現在我每天只用1分鐘，就能做到每週盈利200-300 US pocket錢」→ 口播+字幕都有，必删（这句就是重建也救不了的原因）"),

    h3("Video 4：搞懂交易的那一瞬间"),
    b("「我和我的学员在交易上获得这些result（pop out 学生TP result）」→ 必删"),
    b("「每天1分钟做完交易，再获利」→ 改「每天1分钟完成交易部署」"),
    b("「这堂课我不会跟你说什么『稳赚不赔』」→ 机器审核会抓关键词，连否定句都别提，删"),

    h3("Video 5：盖电脑，喂！（王牌，但同样带违规段）"),
    b("Scene 5 成绩截图 BROLL + 「用别人的资金去赚属于自己的交易回报」→ 重剪时删"),
    b("Scene 6 「零本钱…交易期货」→ 换合规版结尾"),
    b("「如果你在 1 分钟里面就能让你盈利了」→ 改「就能完成判断和部署」"),

    h3("Video 6：我跟你讲！"),
    b("成绩截图 BROLL + 「用别人的资金去赚属于自己的交易回报」+「零本钱…期货」→ 重剪时删"),
    b("「你还没赚到」「这个kangtao真的很好」→ 建议改掉（易触发误导判定）"),

    h3("厌倦了等待（口播稿 00:20 / 00:27 两处）"),
    b("00:20 「我们不用自己的本钱…用别人资金去赚取属于自己的交易回报」→ 必删"),
    b("00:27 「在零本钱的情况之下去开始交易期货」→ 必删；其余段落干净"),

    h2("✅ 合规版共用结尾（重剪直接用）"),
    p("「重点来了 —— 我们不拿自己的本金去冒险。我会教你怎么通过 Prop Firm 的资金审核，"
      "用机构的资金来操盘，本金一分不动。想学这套 1 分钟极速交易策略、了解怎么通过资金审核，"
      "点击链接报名我的免费线上分享会，到时我教你怎么 1 分钟完成进场、出场的判断。」"),
    b("成绩截图 → 换成「学员通过 Prop Firm 资金审核 / 获得资金授权」的画面，绝不出现金额"),

    h2("📌 规则（以后照做）"),
    b("新建广告就算 PAUSED 也会进审核 — 账号有被拒记录时不建任何新广告，先修素材"),
    b("同一素材被拒过，换文案救不了视频内声音/字幕里的违规 — 必须重剪"),
    b("申诉前先 DELETE 名单上的广告，申诉期间不动账号"),
]


def main() -> None:
    s = load_settings()
    nc = notion_client(s)
    dbid = s.notion.database_id
    db = nc._request("GET", f"databases/{dbid}")
    title_prop = next(name for name, prop in (db.get("properties") or {}).items()
                      if isinstance(prop, dict) and prop.get("type") == "title")
    print(f"CONFIRM={CONFIRM} · DB={dbid} · title property = '{title_prop}' · "
          f"{len(BLOCKS)} blocks\nPage title: {TITLE}")
    if not CONFIRM:
        print("DRY RUN — would create the page above. DONE.")
        return
    page = nc._request("POST", "pages", json_body={
        "parent": {"database_id": dbid},
        "properties": {title_prop: {"title": [{"text": {"content": TITLE}}]}},
        "children": [{"object": "block", **blk} for blk in BLOCKS],
    })
    print(f"CREATED page {page.get('id')}\nURL: {page.get('url')}\nDONE.")


if __name__ == "__main__":
    main()
