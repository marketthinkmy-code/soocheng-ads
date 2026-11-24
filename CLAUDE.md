# CLAUDE.md — STOCK BLOOM (Soo Cheng) ad ops + copy SOP

Standing instructions for any Claude session in this repo. Read this before writing ad
copy or building ads.

**Product:** Soo Cheng 老师《1 分钟短线交易盈利营》— a 1-minute short-term (futures)
trading course, sold in Malaysia. Funnel: Meta ad → **free Zoom 分享会 registration (the
lead)** → RM2,399 course. The ad objective is always *registration for the free 分享会*.

---

## ⛔ 死忌（owner 2026-10-25「错的地方不可以再犯，这是死忌」）

1. **报告里提到任何一支 ad，必须写「campaign › ad set · ad ID」，而且只能来自当次 API / monitor 数据——绝不凭记忆或推测。**
   查不到位置就说「查不到」，不猜。（10/25 把 LUXURY GOODS 的盖电脑说成 WINNERS 的盖电脑。）
   monitor 日志已带位置与 ad ID（PR #84），引用时照抄。
2. **会关广告 / 改预算 / 开广告的动作，只在 owner 明确说了之后才执行；之前一律 dry-run。**
   owner 中途打断，立刻查那个动作有没有已经执行，并第一时间如实告诉他、按他的意思复原。
   （10/25 关闭指令在 owner 说「先不关」时已送出，3 支被误关。）
3. **owner 说的看数范围就是判断范围**——他看「星期四到现在」，monitor 与报告都用同一个范围，不自行换窗口。
4. **对 owner 说「会怎样 / 不会怎样」之前，必须先用测试或真实 dry-run 证明——不凭代码注释、记忆或推测。**
   PR 描述、AskUserQuestion 选项、汇报里的每一句行为承诺，都要有对应的测试用例或当次 dry-run 日志；证明不了就写「未验证」。
   每个数字写清窗口和来源（哪天到哪天、哪个表 / API）。（2026-11-20：我说三支 CPA 保护「CPL 规则照常判」，实际代码连 CPL 关停也免掉——
   测试只测了硬线那一半，PR #98 修。owner：「以后不准，不准，不准，再出错。重要的事情我重复了三次！」）

## "上广告" workflow (when the owner says to put up an ad)

Every path ends the same way — **PAUSED 建好（0 花费）→ owner 在 Ads Manager 审 → owner 激活.**
**Never auto-activate.** Which entry path depends on whether the owner hands you copy:

### A) 没有文案 (owner gives only the creative)
1. **Read the creative** — Image → OCR the on-image text (`mcp__Google_Drive__read_file_content`
   returns text for `image/png` · `image/jpeg`). Video → read its script (Notion *SooCheng
   Video Script* page or the Drive file).
2. **根据已有的文案框架写文案** — write copy in the approved 马丁/Andromeda style below,
   anchored to *what this specific creative actually says on-image*.

### B) 有提供文案 (owner hands you copy)
1. **Read the creative the same way** (OCR / script) — you must still know what each image says.
2. **对齐图片和文案** — pair each piece of copy to the image whose on-image angle it actually
   describes. **READ each image to align — never best-guess the pairing.**

### Shared tail (both paths)
3. **Write into the Notion Content Pipeline DB** ("Stock Bloom Content Pipeline Template") as
   the row for that creative, Title `Image N：…` / `Video N：…` — the `N` is required, because
   `notion_captions` parses it into the `content_id`. **Do NOT set Status = "In Review"** —
   owner preference; leave Status default.
4. **Build from the Notion copy** — `adbot build` (single-image manifest, or the video build).
   Build pulls Notion live, so the row's copy is what ships. Everything is created **PAUSED**;
   the owner reviews and activates in Ads Manager.

### ⛔ The alignment rule (why the first single-image campaigns were scrapped, 26 Jun)
**视频同罪（2026-09-11 HOOK 1-4-4 再犯）**：owner 讯息里「链接 + HOOK 标签」的排列顺序**不可信**
——那次 4 个链接的标签全部错位，按顺序配对 = 4 支全建反，owner 只能自己在 Ads Manager 手动改回。
建前必须验证每个 Drive file：先 `get_file_metadata` 看文件名（如 HOOK 1-4 对应脚本 doc 顺序）；
文件名不能定案就抓帧/问 owner 确认，**绝不按讯息顺序 best-guess**。
A creative is an **image + its copy as ONE bound unit.** The build joins them *only* through
the manifest's `content_id ↔ file_id` pairing — copy and image are pulled from separate
sources and meet nowhere else. So if that pairing is guessed, the picture says one thing and
the caption says another. That "WRONG match" got 2 campaigns deleted. **Always derive the
pairing by reading each image's on-image text first; never write a "best-guess" pairing into
a manifest and ship it.**

### Targeting 硬规则（owner 2026-10-08「以后年龄放 28+」，取代 09-11 的「30 開始」）
**所有新建 ad set 年龄一律从 28 开始。** Meta 机制（run 253 实测）分两种：
- **Advantage+ audience ON（Broad 打法）**：只能给「建议下限」`age_range: [28, 65]`——硬 `age_min`
  锁不上（API 报错「You can add a higher minimum age as a suggestion instead」），Meta 认为高价值时
  仍可能投给 28 以下。建 adset 时直接带 `age_range`。
- **advantage_audience=0（硬锁受众，如兴趣组）**：设硬 `age_min: 28`，并剥掉 `age_range`
  （该字段只在 Advantage+ ON 时合法，run 244 教训）。
build 脚本 clone scaffold targeting 时必须覆写 age——scaffold 多半还是 25 起。已在跑的旧 ad set 不回改
（MY 5.0 的 Day Trading / Business Owner 两组 10/8 当天由 28 起重锁；Broad 由团队手改为 25+，未回改）。
⚠️ 在 Ads Manager UI 给 Advantage+ 关闭的 ad set 改年龄，UI 可能顺手把 Advantage+ 打开——兴趣锁会变参考值。

### Ad naming (Meta display name)
Ads on Meta are named **`Image：<descriptor>`** (or `Video：<descriptor>`) — **no running
number.** `build` strips the index automatically (`display_ad_name`), so the owner never
hand-renames in Ads Manager. The Notion row Title keeps its `Image N：…` index (needed for
`content_id` matching); only the on-Meta name drops it.

---

## Copy style — the approved "马丁 / Andromeda" format

Two-part structure (the generator version lives in `prompts/caption_system.md`):

- **Part 1 — emotional teaser** (self-selects the persona):
  vivid daily-life scenario hook → name the helplessness (「你知道不对，却不知道从哪调起」)
  → `Soo Cheng 老师常说：` + a mechanism/insight quote → gentle solution → `📍` soft CTA to
  the free 分享会.
- `══════════` separator.
- **Part 2 — the FIXED 下半段** (template below).

**Only Part 1's hook + ONE curriculum bullet change per angle.** Everything else in 下半段
is fixed.

**Mobile formatting (required):** short lines (break at commas), a blank line between each
idea-group, warm emoji leading lines. Part 1 is emoji-light; Part 2 is emoji-rich
(`👉` self-qualify, `❌` negation, varied-emoji curriculum). Never the old cold `🔴`-only look.

### Fixed 下半段 template

```
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
{每条按角度换 1 条，例：🧠 为什么盯盘越久反而越亏 / 📉 通胀 vs 利息 / 📈 为什么用期货}

⚠️ 名额有限，
别让「再等等」，又拖掉你一整年。

👇 点击下方，免费报名
```

### Credentials (use verbatim — financial vertical, keep truthful/verifiable)

- Soo Cheng — **首席投资分析师、资深银行专业投资顾问、超过 12 年实盘经验**
- **已帮助超过 10,000 名学员入门交易**

### 视频脚本写作规则（owner feedback 复盘，2026-09-08 起累积——写/改脚本前必读）

1. **诊断句禁用「正确的废话」。**「你缺一套 SOP / 你没有系统」这类人人点头的话零信息量
   （owner 09-08 V2 comment:「对一般人来说确实很废话」）。诊断必须**反常识**——把矛头指向
   观众引以为豪的努力行为：「你不赚钱，正是因为你看太多盘了。」SOP 只作为**解法**出现，
   永远不作为指控。
2. **痛点用具体行为画面，不用抽象标签。**「今天看新闻进场、明天听朋友出场」>「你靠感觉交易」。
   点名 2-3 个他这星期真的做过的动作。
3. **痛点讲完立刻上「高手对照组」**（owner 原话句式）：「其实真正赚钱的高手反过来——
   有一套稳定的 SOP，然后不看那么多盘。」
4. 结构硬规则（数据背书）：前 3 秒直呼观众（「我跟你讲」voice）· 前 10 秒自我筛选句
   （写给「有资金/在交易但不稳」的人，绝不写「脱贫」）· freestyle 给 talk-track/beats 不给逐字稿
   （freestyle 手机直拍 > 精修，Korea/Freestyle 1 证明）· 45-90 秒 · 收免费分享会 CTA。
5. 反筛选 hook 合规写法：讲**方法的前提**（「这套方法需要一笔亏得起的闲置资金」），
   禁止直指观众个人财务状况（「你连 1 万都没有」= Meta personal-attributes 拒审风险）。
6. 交付格式照团队 doc 惯例：【Scene N：机位/动作】+ 台词 + 剪辑注 + 每支 3 个 A/B hook；
   学员成绩 POP UP 只可出现「资金审核通过/资金授权」画面，任何金额不可入镜（口播同理）。
7. **用词黑名单（owner 09-08:「这边要你们 100% 注意」）：投资/交易语境禁用「玩」字**——
   玩法、新玩法、这样玩、玩交易、怎么玩、上场玩，一律不可出现（很儿戏、很飘）。
   替换词：做法 / 方法 / 操作方式 / 规则。贬义对照也别用（「别人当玩」→「别人靠感觉」）。
8. **Prop Firm 承诺用词黑名单（owner 09-08，winning ads 重拍的起因）：**
   「一天就可以 Pass」「很快 pass」「考试一点都不难/很简单」「容易到睡不着」「保证通过」
   一律禁用（飘 + 拒审风险）。Prop Firm 本身**保留**（下半段模板、offer signals、分享会照教）。
   合规讲法：「资金审核考的不是预测，是纪律」「照 SOP 去准备，把风控和执行练稳再去考」
   「有规则、有评估，不是零风险」「怎么准备，分享会里讲清楚」。加分反差句：
   「谁跟你讲很快就能过的，你要小心」——把旧承诺反过来打，变成信任感。
9. **CTA 禁句（owner 已多次强调，09-08 再次点名）：不要特地讲「填名字电话 / 填个名字和电话」。**
   CTA 直接写：「点下面报名，Zoom link 会直接发给你」，或更短「点下方，免费报名」。
10. **Prop Firm 口播三件套（owner 09-08 V12 comment）：**
   a) 「资金授权 / 通过资金审核」是书面词，**口播不用**——口播讲「funded account / 机构给你一笔
      资金操盘」（文案下半段的书面合规写法不变，仅口播换词）。
   b) **必须讲出 end result**——通过考试不是终点，重点是「用别人的资金去交易」。用已过审句式：
      「赚了，利润是你的；亏了，不伤你自己的本金」+「考试只是门票」。
   c) **讲资金规模**：「最高 5 万美金的 funded account」——资金规模可讲（不是收益数字）；
      但**不可**由此口播「所以盈利也不小」这类预期收益暗示（仍是拒审红线），
      让「5 万美金 vs 自己的小资金」的对比自己说话。

---

## Andromeda feeding (how to structure delivery, not just words)

Andromeda is Meta's ML retrieval engine — it picks the best creative per user from a broad
pool. Feed it well:

- **Broad / Advantage+ targeting** — do NOT lock interests. The creative's self-selecting
  hook does the targeting.
- **Run the distinct creatives together in ONE ad set** (a diverse creative pool to retrieve
  from); add **multiple formats** (single image + video + carousel).
- **Consolidate** ad sets (don't split into many duplicates fighting for budget).
- **Consistent offer signals** in every creative so the model understands the offer:
  `1 分钟极速交易策略` · `Prop Firm 资金审核` · `红绿灯 SOP` · `免费线上分享会`.

---

## Compliance (HARD RULES — this account was disabled by Meta once)

- **No income/profit figures, no 提款 amounts, no guaranteed/expected returns**, no
  get-rich / risk-free / 100% language.
- Frame student results as **「入门交易 / 通过 Prop Firm 资金审核 / 获得资金授权」** — never
  as money earned.
- Creatives that bake payout screenshots into the image stay in `creatives_held` (copy
  ready, not built) until reviewed.

### ⛔ 永久禁跑名单 (owner 2026-09-23 — 第二次封号后的硬规则)

**2026-09-23：MY 账户 MTC X SB 3.0 (act_759339046918885) 被 Meta 停用** —— API 取证
`account_status=2 (DISABLED)` · `disable_reason=1 (ADS_INTEGRITY_POLICY 广告诚信政策违规)`，
与 2026-07-12 旧账号 MTC X STOCKBLOOM 2 被封的代码**完全相同**（同一账号家族第二次被封）。
SG 账户 act_893025326577600 当时仍 `account_status=1 (ACTIVE)`——**它是目前仅剩的投放资产，
一切决策以「不触发第三次封号」为最高优先级。**

**OWNER 硬规则（2026-09-23，正式推翻 07-30「一切以 CPL CPA 为主」）：**
> 「list out all those rejected ads for me, and write a rule that not to advertise
> these ads anymore (even tho the ads are running well and had good cpa before)」

- **凡被 Meta 拒审过的素材 = 永久禁跑。** 不看 CPL、不看 CPA、不看历史成交——
  **就算它以前 CPA 很漂亮、正在赚钱、是 top seller，也一律不准再投。**
- 禁的是**素材母带本身（视频/图片）**，不是某一个 ad 名字：换文案、换 ad 名、换 campaign、
  换受众、换账户、post 复用、重新上传——**全部视为同一支，一律禁**。
- **禁止 resubmit / 申诉重投**被拒广告（每次重拒都给这个惯犯账号家族再加一条 strike）。
- 想保留这个角度 → **只能让剪辑师重剪干净版母带**（删掉违规口播/字幕/成绩截图），
  当**全新素材**走正常建案流程；重剪版与原版是两支，**原版永久禁不解**。
- 被拒广告**留在账户里本身就是风险**：名单上的广告应 DELETE，不要只是 PAUSE（7 月取证结论）。
- 本条**高于**本文件其它所有 CPL/CPA 规则：monitor / 清扫报告 / 开回建议里
  **永远不得出现禁跑素材**；即使 owner 点名开回，也要先提醒「这是禁跑素材」再等他确认。

#### 名单 A — 2026-09-23 封号时账户内仍在的被拒广告（API 取证）

| 素材（母带） | MY | SG |
|---|---|---|
| **拼接：Video 5：Trading 早就不是这样了！** | ×3（BEER 0914 / BROAD 0911 / DT 30-55 0914） | ×3（LAL 0910 `DISAPPROVED` / GOLF 0914 / BROAD 0911） |
| **Video 8：做么你 Trading 不用看盘的？**（含 `HOOK：` 版） | ×1 `DISAPPROVED`（BROAD 0911） | ×2（BROAD 0911 / GOLF 0914） |
| **video 5：trading 早就不是这样了！**（拼接版的原版母带） | — | ×1（🌟GOLF PICKBLEBALL） |
| **freestyle 1**（🌟 版） | — | ×1（🌟INVESTMENT） |
| **video 11：office 突访** | — | ×1（TRAVEL） |
| **video 12：炒过那么多，累而且不稳定** | — | ×1（BROKERS） |
| M2Video 3: What you do for living?（2025 旧 options 产品遗留） | ×1 `DISAPPROVED` | — |

#### 名单 B — 历史被拒（旧账号 2026-07-12 取证 + owner 报告，一并永久禁）

video 3：不是怕交易（合规重建也被拒）· Video 4：厌倦了等待（合规重建也被拒）·
single image 5：moomoo · video 1：1 分钟赚 300 · single image：每天 1 分钟就能盈利 ·
Video 2（谁讲 trading 一定要~）· video 2：你敢吗？· freestyle 2

⚠️ **2026-08-07 对「video 12 炒过那么多」的解禁作废**——它 09-23 在 SG BROKERS 仍是被拒状态，
现回到永久名单。同理，未来任何「它现在过审了所以可以再跑」的论证一律不成立：
**过审 ≠ 解禁，只有重剪干净版才能重新上场。**

#### 名单 C — 2026-10-24 MY 5.0 被拒（owner「全部照建议」）

**Video 1：赚美金，一定要接美国客户？** —— MY 5.0 WINNERS MY «Broad · 赚美金» 被拒（ad 120251533797560329，Meta 未给原因），MY 5.0 继「不选 forex」后第二支。按 9/23 规则全家族永久禁：被拒那支 DELETE，MY + SG 所有副本 ad 层 PAUSED 并加 🚫（yaml `banned_creatives` 已加，PR #80）。「赚美金 = 求人？」是另一支母带，不受影响（同角度，审核要盯）。
⏸ **owner 2026-10-25 本人例外（同 10/8 不选 forex 的申诉先例）：「先让我试试看，帮我 hold 不要自动关掉它」**——
仅 MY 5.0：`config.my5.yaml` 暂时从 banned_creatives 拿掉、加入 `kpi.cpl_hold`（PR #81）；SG / MY 3.0 仍禁。
带 🚫 的副本仍被标记拦住。owner 自己跑、被拒后是否 request review 由他本人决定（我们不代为申诉）。10/29 复盘时决定恢复禁跑与否。
⛔ **2026-11-02 例外结束**：LUXURY MY «Luxury | MY 28+» · ad 120251454699130329 在 10/30 被拒，owner 本人 request review 后**仍被拒**
→ owner「做」：该 ad DELETE；MY 5.0 其余 10 支副本 ad 层 PAUSED + 🚫（`execute_zmj_ban_1102.py`）；`config.my5.yaml` 恢复
banned_creatives、清空 cpl_hold（PR #86）。**赚美金 MY + SG 全面永久禁跑，不再有例外。**

#### 2026-11-05 SG 旧广告批量被拒（owner 选「C」= 本人例外）

11/05 04:16 Meta 重审 SG 旧 campaign（全已 PAUSED），6 支被拒（Meta 未给原因）：ANDRO POOL 30+ 0922 的 freestyle: korea /
HOOK：Video 5 盖电脑 / HOOK：Video 12 不选 forex / video 2 我只有一个目的；🌟 PURCHASE LAL 5% 1-1-4 的 🌟 video 5 盖电脑；
BROAD SG 25+ 0905 的 video 1 用我的方法。**owner 选「C」：只 DELETE 这 6 支（`execute_sg_delete_rejected_1105.py`），
在跑的同母带 / 同文案副本照跑**（含与被拒同文案的 MY korea ×2、MY 盖电脑 ×3、SG TRAVEL 盖电脑）——这是 owner 对 9/23「母带永久禁」
的本人例外（同 10/8 不选 forex 先例），**不进 banned_creatives、不加 🚫**。这些副本若再被拒，立刻报告 owner、建议 DELETE。

#### 共同违规 DNA（重剪前必须逐条清掉；逐支脚本级清单见 `scripts/archive_ban_list.py`）

收益金额（「每週/每天 200-300 US」「一星期赚一千美金」——口播/字幕/道具纸板任一形式）·
学员成绩 / TP / 提款截图 BROLL · 「用别人的资金去赚属于自己的交易回报」·
「零本钱…交易期货」· 「proven works 公式 / copy paste 跟着做就会」

机器可读名单：`config/config.yaml` 与 `config.sg.yaml` 的 `compliance.banned_creatives`；
判定入口只有 `adbot.compliance.is_banned(name)`（子串匹配，忽略 🌟 / `HOOK：` / `重拍：` /
`拼接：` 前缀）。**任何建案 / 开回 / scale 脚本动手前必须先过这道闸。**

**🚫 标记（owner 2026-10-08「禁跑名单的 ad name 前面统一加 emoji 🚫」）：**名单上的每一支 ad 在
Ads Manager 里一律改名为 `🚫 <原名>`（SG 已由 `scripts/execute_mark_banned_sg_1008.py` 全部加上；
以后新进名单的素材、每一个副本都要加）。`adbot.compliance` 把 🚫 当禁跑标记：**名字带 🚫 的 ad
不论 yaml 名单有没有它，一律视为禁跑**；匹配时忽略 🚫（同 🌟），CPA join 也忽略。
看到 🚫 = 不开、不复制、不 resubmit；只能等重剪干净版以新名字进场。

**ad 层拆引信（2026-10-08 教训）：**9/23 只删了「自身状态=被拒」的 9 支，名单上其余副本仍在账户里，
其中 17 支 ad 层 ACTIVE、只被 campaign/adset 压住——10/8 10:21 有人按 campaign 整条开回，
`炒过那么多` 立刻上线 7 分钟。**禁跑素材必须在 ad 层 PAUSED**（`execute_ban_neutralize_sg_1008.py`），
不能只靠上层关着；开回任何载体前先扫它底下有没有禁跑 ad 上膛。

### 📋 运营规则（仍然有效，但全部让位于上面的禁跑名单）

- **Owner 手动关 = 定案（owner 2026-09-14「我手动关了的广告不要再开回了」）**：被 owner 手动
  关掉的 campaign / ad set / ad 一律不得自动或主动开回——**包括近期有成交的链**。guardian 的
  每小时自动复活已于 2026-09-14 退役（adbot-guardian.yml 只剩 workflow_dispatch）。唯一开回
  路径 = owner 明确点名。报告里可以*建议*开回，执行必须等 owner 的字。
- **Pause decisions belong to the CPL/CPA monitor only** (2026-09-10 起：MY 线 RM60 / SG 线
  RM95，花满 RM60 / RM142 才判；超线**先把预算载体降 30%**（TEMP，`kpi.cpl_soft_reduce`），同一
  周四周期内再犯才关；0-reg 花满门槛直接关；CPA hard-stop RM1,200；converting ads are
  CPA-rescued；`cpa.hold` 是 owner 点名的 hard-stop 豁免).
- **2026-10-25 收紧（owner「紧密看」，PR #82，取代上一条里的软降与周四归零）**：MY + SG 都改为
  `cpl_lookback: rolling_7d`（最近 7 天含今天，不再周四归零）· `cpl_soft_reduce: false`（超线直接关该 ad，
  不再先降 30%）· SG `cpl_min_spend_myr` 142 → **80**（owner：「我不是设定了 80 吗」）。
  **成交保护只认原位**（owner：「一定要是那个 campaign、那个 ad set 的那个 ad 曾经成交过，才要保护，而不是
  所有副本都保护」）——按素材名跨副本保护已取消。保护期（hold_ad_until）只在 owner 亲自点名时设。
- **老将门槛（owner 2026-11-06「1」，PR #87）**：10/16 起 ≥10 报名且 CPL ≤40 的 ad = 老将，周四窗口内要花满 **RM150**
  才判 CPL / 0 报名（其他 ad 照旧 RM60 / RM80）。起因：周四归零 + 周四到周日最贵，monitor 在 RM60–81 就关掉了
  DAY TRADING 的 korea（28 报名 CPL 28）、年纪大（17 报名 CPL 21）。日志 reason = `veteran_wait`。禁跑 / CPA 硬线不受影响。
- **开着的广告准入标准（owner 2026-09-20「以 30 day CPA 为标准」+「不希望开着的都是很久没
  成交/CPA 不合格的，新广告例外」）**：每支在跑的 registration ad 必须满足其一——
  ① 30 天 strict CPA ≤ RM960（>1,200 关；960-1,200 watch）；② 位置 ≤14 天（新广告例外，
  判决日 = 建立日+14）；③ 本位 30 天无单但**素材 7 天内有成交**（不算「很久没成交」）。
  盘面检查/清扫按此判（executor 模板 `scripts/execute_cpa_enforce2_0920.py`）；owner 当天
  点名开回的位不自动关，标 CONFLICT 交 owner 定。
  **前提：素材不在禁跑名单上——在名单上的，CPA 再好也不准开。**
- 🛑 **2026-09-23 起暂停「按 CPA 清扫在跑的广告」（owner:「现在跑着的，没被禁的，就不要关它」）**：
  MY 被封后 SG 是唯一投放资产，量本来就稀缺——**当前在跑且不在禁跑名单上的广告一律不关**，
  上面那套 30 天 CPA 准入标准只用来判断「要不要*开*新的位」和写报告，**不再作为关闭理由**。
  要关任何一支干净的在跑广告，必须 owner 明确点名。禁跑名单仍照常自动关（那是硬规则）。
  仍然自动生效的只剩 monitor 的基本护栏（CPL 超线先降 30%、0-reg 花满、CPA hard-stop
  RM1,200）——owner 若要连这些也停，改 `kpi` / `cpa` 配置即可。

---

## Proven angles (old account purchase data, Apr 1 – Jun 23 2026 — buyers, not just CPL)

Ranked by real course buyers / conversion (use this order when prioritising):

1. **不是怕交易** (35 buyers, RM148k — top volume) · 2. **我跟你讲** (25% conversion — most
efficient) · 3. **盖电脑·别盯盘** (11%) · 4. **不选 forex 不选黄金** · 5. **你敢吗** ·
6. **40 岁·收入单一** · 7. **FD·闲置资金** · 8. **怀疑者**.

⚠️ #1 **不是怕交易** and #5 **你敢吗** are on the ⛔ 禁跑名单 above (Meta-rejected) — the ranking is
historical data only; do NOT rebuild them. Reuse the *angle* with a fresh compliant creative instead.

- **Best-converting voice = personal, in-your-face direct address** (the「我跟你讲」voice).
- **Winning audiences (CPA/ROAS ~3x): Luxury Goods, Beer/Alcohol, Omakase/Wagyu** — affluent,
  mid-life, *already has capital*. Write to "make existing money work, principal untouched",
  not "escape poverty".
- **Avoid leading on** `不用看盘` / `街头突击采访` (cheap reach, weak conversion).
- ⚠️ Cheapest CPL ≠ best ad. `Travel` had the lowest CPL but the worst CPA — judge by
  purchases/ROAS, not CPL.

---

## 每周排程（2026-11-11 起：owner 手动，「我自己手动」）

**直播日（周三）关广告 / 周四开回 = owner 本人在 Ads Manager 手动做。不要假设有自动关开。**
- 实测（11/11）：adbot-weekly-off / weekly-on 两条 workflow 读的是 `config/config.yaml` = **已封的 MY 3.0**——
  11/4 weekly-off 报错「Ad account status is ineligible to manage ads」，weekly-on「no tagged ads to resume」。
  **MY 5.0 和 SG 都不在这个周期里**，周四 00:00 不会有任何东西自动开回。owner 11/11 选择不接到 MY 5.0，自己手动。
- 11/11 例子：owner 15:15（MY 5 个 campaign）/ 15:18（SG 4 个）在 campaign 层手动全关 = 定案；只有他本人开回。
- 周三下午看到被关的 campaign 是 owner 手动关的，不要去「修」；周三下午不判读当日数据。
- owner 若说「开回时顺便把 X 的 ad 层一起开」，只动 ad / ad set 层做准备，campaign 层留给他开。

## 新视频上线规则（owner 2026-11-10，取代上面「Copy style」里的固定下半段）

- **先 propose，owner approve 才建**：文案 + 建置 plan 一起给他看；他回「approve」才动手。
- **文案**：每支只给**一个**标题、一个 hook 的最佳版本，不给备选。开头两句写成完整句子（不要一行几个字地断开），
  第一、二句就要点出精准受众（有一笔钱 / 交易几年不稳 / 盯盘的上班族…）、试过什么、卡在哪里，然后痛点 → 解法 → 📍 课程 → ⏰ → 👇。
  参考马丁项目（martin-ads-MY / SG / CALIFORNIA）的写法：emoji 带节奏（✅ 列点、📍 课程、⏰ 名额、👇 报名），标题 🔴 开头。
  写完先自查敏感字眼（个人财务/年龄的断定、和 FD 利息比较的回报暗示、收益字眼）。
- **结构**：新视频测试用 **ABO**（CBO 只给要 scale 的赢家）。每个受众一个 campaign，里面每支视频一个 ad set，各 RM50/天。
  受众按 **Paid Student List 按国家的成交排名**选，不凭空建议 Broad。
- **Monitor**：名字含 `NEW VIDEO` 的 campaign 用 `kpi.campaign_overrides`——**RM80**（owner 11/11「不想那么快判死刑」，PR #89，原 RM50 / PR #88）：
  花满 RM80 才判；0 报名花满 RM80 就关；花满 RM80 后 CPL > RM80 就关。11/11 RM50 线一天关掉 30 支里的 22 支，其中 8 支有 1 个报名（部分是关后才回传）。
- **新广告不急着关（owner 11/11「新广告还没有跑出 learning phase，不急着关」）**：报告 / 建议里不要因为新广告前几天 0 报名或 CPL 偏高
  就提议关掉或排除——交给 monitor 的 RM80 规则判。11/12 00:00 owner 选 A：0 报名的新视频也全部开回（周四窗口归零后各自重新花满 RM80 才判）。
- **11/12 周四复盘（owner 本人破例「不要看周四窗口归零，看新视频从开始跑到现在」）**：按上线以来累计花费套 RM80 规则，
  owner「关 20 支」→ 留 10 支（MY News V2/V4/V5、MY Luxury V1/V2/V4、MY Broad V2、SG Broad V2/V4、SG Golf V1），
  SG Travel 新视频 5 支全关（`execute_nv_cut20_1112.py`）。这 20 支 = owner 决定关的，不得自动开回。
  累计结论：受众 MY News CPL 41 / MY Luxury 45 / SG Broad 66 好，MY Broad 117 / SG Golf 128 / SG Travel 268 差（落地页→报名仅 6–11%）；
  视频 V4 决定变少 CPL 43 最好，V3 越认真盯盘 150 / V5 不适合你 119 最差。
- **11/12 复盘其它定案**：周期（11/12–11/18）总预算上限 **RM6,250**（owner）；BROAD MY campaign RM275 → RM150（korea 10/29 起 43 报名只 1 单）；
  BUSINESS OWNER 年纪大、BROAD SG 照跑（11/11 场 2 单都来自这两个）。预算方案 owner 选「沒事繼續跑…monitor 會關掉一些廣告」：
  不暂停、不降预算（约 RM900/天），靠 monitor CPL 规则砍；周期累计过 RM5,500 时再报给 owner 问要不要收。
  **11/13 owner「我只看成绩」**（回应「改周一开回可省约 RM400」的建议）：只按成绩（报名 / CPL / 成交 · CPA）判断，
  不因预算提议改动作、到 RM5,500 也不问要不要收；周六 00:00 开回照原定。汇报成绩优先，花费 / 预计到周三只留最后一行。
  （11/12 22:15 说的「预计约 RM6,400」算少了——停 4 支实际只省周五一天约 RM200，不是 RM400；11/13 09:49 重算约 RM6,800。）
  **11/13 owner「OK」**：MY NEW VIDEO · Broad › Broad | MY 28+ · V2 · ad 120251840432100329（周四起 7 报名 CPL 14）
  「明天还稳」就把 ad set 120251840426800329 RM50 → RM60（+20%）。稳 = 11/13 全天 ≥1 报名且 CPL ≤30、周四起 CPL ≤30、三层 ACTIVE、预算仍 RM50；
  11/14 00:10 自动判（`execute_nv_broadv2_60_1114.py`，send_later trig_01W7kvNPoCMreWhxBJSmBnvE），不稳就不加。SG 11/13 判断：在跑 4 支都在线内，不调。
  **11/13 10:2x owner「👌🏼 广告先不动」**（回应「问题在出席不在 CPL」的建议：4 场 CPL 都 43–48，每学员成本 RM470–2,195）：
  这期除了周六两件已排程的事（00:00 开回 4 支、00:10 Broad V2 稳就 +20%，owner 再确认「照原定做」）之外不再改广告、不提加减建议；
  monitor 照常自动判。重点转到报名后的提醒 / Zoom link 流程（等 owner 给设定截图）。
  **11/13 10:14 owner 本人在 Ads Manager（activity log：Thelyin Siew）**：开回 BROAD MY | 1-1-5 | 1017 campaign + Broad | MY 28+ · freestyle: korea ·
  ad 120251456191090329（11/12 他「关」的，这次他本人开回 = 有效，在跑）；关掉 NEW VIDEO · Luxury Goods | 1-5-1 | 1110 campaign（120251840064210329）
  = 定案。→ 周六 00:00 开回脚本遇到 campaign 关着会跳过 Luxury V1/V2/V4，只开 News V5（不替他开 campaign）。MY 日预算 → RM585。
  monitor 对 BROAD MY korea 看到 0 原位成交（UTM 对不上；robust-UTM 是 10/29 起 1 单 / CPA RM1,747），所以不会触发 CPA 硬线，只按 CPL 判。
  **11/14 00:15 周六两件已执行**（排程迟到，我手动照 owner 已批的内容跑，排程随后停用）：News V5 · ad 120251840063080329 开回（回读 ACTIVE）；
  Luxury V1/V2/V4 因 campaign 被 owner 关着 → 跳过；Broad V2 ad set 120251840426800329 RM50 → RM60（11/13 全天 RM65 / 6 报名 CPL 11，周四起 CPL 12）。
  另：owner 11/13 22:06 本人把 SG NEW VIDEO · Broad › Broad | SG 28+ · V4 的 ad set 120250544545020521 RM50 → RM60。日预算 → 约 RM835（MY 645 / SG 190）。
  **11/14 owner「周一加」**（问「有没有需要加预算的？」后选我的方案）：**周一 11/16 00:05** 两支 MY 新视频各 +20%，各自周六+周日 CPL ≤30（≥1 报名）才加：
  News V4 · ad 120251840059300329 → ad set 120251840057130329 RM50 → RM60；Broad V2 · ad 120251840432100329 → ad set 120251840426800329 RM60 → RM72
  （`execute_nv_raise_1116.py`，send_later trig_012FRNoWMohGVbyStMNDifCY）。选周一的理由：上一场周一–周三报名出席 30%、周四–周日 4%。
  SG 不加（现有预算都花不完）；无成交或 CPA 太贵的（DAY TRADING korea、BROAD MY korea、News V5）不加。
  **11/16 00:06 已执行**：Broad V2 周六+周日 RM141 / 5 报名 CPL 28 → ad set 120251840426800329 RM60 → RM72（回读 RM72）；
  News V4 周六+周日 RM91 / 2 CPL 46 → 不加（仍 RM50）。日预算 → 约 RM847（MY 657 / SG 190）。
  **11/16 10:14 owner「关盖电脑和 BROAD MY korea」= 定案**（晨报：周日 BUSINESS OWNER RM148 / 0 报名、BROAD MY RM161 / 1；korea 10/29 起 CPA RM2,201）：
  BUSINESS OWNER › Business Owner | MY 28+ · 盖电脑 · ad 120251454701640329、BROAD MY › Broad | MY 28+ · korea · ad 120251456191090329 ad 层 PAUSED
  （`execute_close_bo_broadmy_1116.py`，回读 PAUSED）。两个 CBO（RM120 / RM150）已无在跑 ad。日预算 → 约 RM577（MY 387 / SG 190）。不得自动开回。
  ⛔ **11/17 教训（owner「有些星期四到现在的广告，cpl 便宜的被关了」）**：11/16 晨报我只列**周日单日**数字（BO 盖电脑 RM148/0、BROAD MY korea RM161/1），还写了「想关…跟我说」——但两支**周四起** CPL 33 / 35 都在线内 → 违反死忌 3（看数范围 = 周四到现在）和「广告先不动」。以后：关停 / 开回建议只能用周四起窗口；单日数字只当背景，**绝不配关停邀约**。
  11/16–17 CPL 飙高诊断（`report_cpl_spike_1117.py`）：不是关停造成的（各 campaign 自己的预算，关了不会把钱推给别人），而是整体投放变贵——MY CPM 111→169→203、链接 CTR 3.6%→2.7%、落地页访问成本 RM4→RM9.5、落地页→报名 11.6%→6.5%；SG CPM 253→530。11/17 11:40 monitor 按线关 News V2 · ad 120251840053010329（周四起 CPL 82）。
  **11/17 owner 三个决定（AskUserQuestion）**：① 照跑到周三 15:00（周三上午历来最便宜：MY 周三 CPL 10–26；周一到周三报名出席 30%）；② 版位这期不改（变贵主因 = Meta 把钱推到 Facebook 动态，MY 占比 15–18% → 42–51%、feed CPM 101–146 → 392–503；SG feed 67% / CPM 1,483；频次 1.1–1.5 不是看腻；多数 ad 质量排名 BELOW_AVERAGE_20/35）；③ 周四一起开：**11/19 00:01** 只开 BUSINESS OWNER › Business Owner | MY 28+ · 盖电脑 · ad 120251454701640329 的 ad 层（`execute_reopen_bo_gaidiannao_1119.py`，send_later trig_014pJDRYCWy8BhqoJDiohJJt），campaign 层留给 owner；BROAD MY korea 不开。owner 偏好：要他决定的事一题一题给、附我的推荐。
  **11/18 11:21–11:22 owner 本人在 campaign 层关掉全部 7 个 campaign**（MY DAY TRADING / NEW VIDEO · News / NEW VIDEO · Broad / BUSINESS OWNER / BROAD MY；SG BROAD SG / NEW VIDEO · Broad）——「花够钱了…这两天报名异常 我提早关了」= 定案，只有他开回。11/19 00:01 的盖电脑脚本只开 ad 层，要等他开 BO campaign 才跑。
  **11/18 复盘（`report_cycle_review_1118.py` / `report_cycle_trend_1118.py`）**：周期 RM7,028 / 145 报名 CPL 48（MY 4,823/119=41；SG 2,205/26=85），超上限 RM6,250 约 RM780。Register 每天报名 周四 30 · 周五 57 · 周六 22 · 周日 17 → 周一 4 · 周二 6 · 周三 4（真掉，非追踪）。历场：10/21 RM470/人 · 10/28 1,704 · 11/04 583 · 11/11 RM941（7 单）。有单（10/29 起 robust-UTM 原位）：BO 盖电脑 CPA 581、News V4 CPA 427、SG BROAD SG 年纪大 · ad 120250144813480521 CPA 685、用我的方法 1,185、BROAD MY korea 2,205；DAY TRADING（korea+年纪大）10/29 起 RM2,386 原位 0 单。⚠️ monitor 的成交比对比 robust-UTM 严：SG 年纪大 11/14 被当成 0 单、CPL 80.21 关掉（有单本应 CPA 保护）——修 monitor 比对待 owner 定。
  ⚠️ **11/13 机器人假报名（owner 11/18「好像被人针对，都是马来人」，`report_fake_regs_1118.py` / `report_placement_quality_1118.py`）**：Register 11/13 共 57 笔，**40 笔是机器人**（Experience 栏 = 名字打两次、电邮和名字无关；11/11 另 1 笔；11/14 起 0）。全部带 UTM Placement = Facebook_Mobile_Feed，分散在 11 个广告位置（BO 盖电脑 10 · BROAD MY korea 10 · NV Broad V2 4 · DT korea 4 · SG V4 3 · SG 我跟你讲 3 · News V4 2 · News V2 2 · DT 年纪大 1 · SG 用我的方法 1 · 已关的 Golf V3 1）= 真的点了 feed 广告、Meta 像素也算成报名（11/13 MY feed 34 报名 CTR 7.0%、SG feed 8 报名 CTR 10.7%）。**这期 CPL 被灌水**：MY 119 报名约 33 笔是假的 → 真 CPL 约 56；BO 盖电脑真实 3 报名 CPL 约 145（不是 33）、BROAD MY korea 12 报名 CPL 约 65。推测 Meta 因此把预算推进 FB 动态（11/16 起 42–51%）。版位成绩（10/29 起 Register）：Audience Network 28 报名 0 买家（CTR 7–15%）· FB Reels 83 报名 0 买家 · FB Mobile Feed 96 报名（41 假）5 买家。以后报告 / 复盘一律剔除 S1 假报名。
  **11/18 owner 对假报名的三个决定**：① Audience Network **不排除**（版位照旧）；② 盖电脑 11/19 00:01 **照原定开 ad 层**（知道真实 CPL 约 145，看的是那 1 单 CPA 581）；③ 报名页防机器人（reCAPTCHA / 隐藏栏位）**owner 团队自己处理**，不用我写步骤。
  **11/18 ~22:3x owner「等下 00:00 开完我今天 11:20am 左右关的广告」**：11/19 00:00 只在 campaign 层开回他 11/18 关的 7 个 campaign（`execute_reopen_campaigns_1119.py`，send_later trig_01S2kqdVTsnWfSo3Y2SwPTJp；有禁跑/被拒 ad 上膛的 campaign 不开）。ad / ad set 层不动：会跑的只有 DT 年纪大 + korea（CBO RM165）、News V4 / V5（各 RM50）、MY Broad V2（RM72）、SG Broad V4（RM60）≈ RM397；00:01 盖电脑 ad 层开后 + BO CBO RM120 ≈ RM517。BROAD MY / BROAD SG 底下没有开着的 ad，开了不花钱。
  **11/18 ~23:0x owner「你要确保有开到哦！有时候 campaign 开了，ad set/ ad 没有开到」**：00:00 脚本改成对 7 支应跑的 ad（含盖电脑）三层都确保 ACTIVE、读回 effective_status；原 00:01 盖电脑排程停用（并入 00:00）；01:00 再跑一次只读检查（trig_01VrQhJueSUm856uYQD2kRUp）确认 🟢 + 开始花钱。**以后凡是开回，都要读回 ad 的实际投放状态，不能只看 campaign 开关。**
  **11/18 ~22:5x owner 先说「有成交记录的都一起开」，随即撤回「这个成交不是 webinarkit 的，当我没说」**：`execute_reopen_sales_ads_1119.py` 只 dry-run 过、**没有排程、没有写入**。Paid Student List 11/18 新加的 12 行（10 行 Channel/Source/UTM 全空）**不是 Webinarkit 成交**——算每场成交 / 每学员成本时不能计入。00:00 开回 7 个 campaign + 00:01 盖电脑 ad 层照原定。
  **11/19 新周期（直播后）owner 决定（AskUserQuestion）**：① DAY TRADING 两支「两支都关」——Day Trading | MY 28+ · korea · ad 120251455974450329
  （10/29 起 RM1,584 / 35 UTM 报名 / 0 单）、年纪大 · ad 120251454717600329（RM850 / 22 / 0 单）10:57 ad 层 PAUSED（`execute_close_dt_1119.py`，回读 PAUSED）=
  owner 定案，不得自动开回；DAY TRADING campaign 仍 ACTIVE（CBO RM165）但无在跑 ad。② owner 10:55 本人在 campaign 层关掉 SG BROAD SG、SG NEW VIDEO · Broad
  （含 V4 · ad 120250544546540521）和 MY BROAD MY = 定案；随后选「SG 先全停，年纪大也不开」——SG 0 支在跑，SG 年纪大 · ad 120250144813480521 不开。
  ③ monitor 成交比对照修 → **PR #93**（报名表 UTM 原位成交 ∪ Paid 行自带 UTM，按 Paid 行去重；待 owner 看过再合并）：实测 News V4 0→1 单（CPA 458）、
  SG 年纪大 0→1（685）、BROAD MY korea 0→1（2,582）。在跑：MY 4 支（BO 盖电脑 CBO RM120、NV Broad V2 RM72、News V4 / V5 各 RM50）≈ RM292/天。
  11/18 场成交 11/19 早上还没入 Paid 表（webinar_nov18 只有 11/12 一笔 bank transfer）。11/18 Register 40 笔，0 机器人（多为周三回头报名）。
  **11/19 11:4x owner「先修好 PR #93，一定要看完 campaign、ad set、ad」→ 收紧后「合并」**：报名表比对与 Paid 比对用同一把严格的 key
  （campaign 只忽略「| 1-x-y |」 › ad set › ad 名字一字不差，只忽略 🌟/🚫/大小写/空格），每笔成交只认买前**最后一次**报名的位置，按 Paid 行去重。
  逐笔核对（`report_pr93_audit_1119.py`）60 天 60 笔：认到的全部三层 ✅，没有一个 key 落在两支 ad。PR #93 已 squash 合并（52a0ee4），
  合并后 main 上 dry-run：News V4 CPA=459(1 sale)、BO 盖电脑 740(1 sale)，无报错。
  **11/19 11:50 owner「可以开。只是要确保现在的都是带去 webinarkit 的广告」**：SG BROAD SG › Broad | SG 28+ · 年纪大 · ad 120250144813480521
  三层开回（BROAD SG campaign 只有它一支，CBO RM130；`execute_reopen_sg_laonian_1119.py`，回读 ACTIVE）。两账户在投放 5 支，campaign 全部带 (Webinarkit)。
  日预算 ≈ RM422（MY 292 / SG 130）。SG NEW VIDEO · Broad 仍是 owner 关的，不开。**以后开任何广告都要确认 campaign 名前面有 (Webinarkit)。**
  **11/19 复盘 11/12–11/18（owner「新广告是不是不给力…才一位，而且还是以前的广告报名的」，`report_cycle_deep_1119.py`）**：
  11/18 场 Paid 有电邮电话的 2 笔都是**旧名单**（7/19 SG INVESTMENT、9/14 BROAD MY 25+ 旧广告进来，11/18 用不带 UTM 的链接重新报名）→
  本周 Webinarkit 广告 91 真报名 0 单。新旧素材真 CPL（去机器人）MY 68 vs 59、SG 143 vs 184，这一场都 0 单 → 不是新视频特别差。
  真正差别 = 报名落在哪天：广告真报名 周四–日 / 周一–三 = 11/04 42/32（9 单）· 11/11 48/52（6 单）· 11/18 **81/10**（广告 0 单）；
  11/11 出席 周四–日 4% vs 周一–三 30% → 11/18 估计只有约 6 个广告报名进场。最近三场 17 笔可对上成交：旧名单 10、新名单 7（首报名即 Webinarkit 广告 4：
  BO 盖电脑、BO 年纪大、SG BROAD SG、News V4）。⚠️ DT korea 的报名表 UTM ad 名「Video：freestyle korea」≠ Meta「freestyle: korea」，严格比对认不到（已关）。
  owner 对「周五–日降 30%、周一起加」选 **「不变」**：照 RM422/天跑到周三，monitor 照判。待 owner：11/18 Webinarkit 出席名单 CSV、提醒 / Zoom link 设定截图。
  **11/19 14:1x owner「我们把 40 个机器人报名的假象数字移除掉」+「这一场广告费控制（花到星期三 3PM）在 RM6000 硬规矩。如果提早花完就关广告」→「合并」= PR #94（e257e5d）**：
  ① `spend_cap`（两个 config）：monitor 每 20 分钟加总 MY 5.0 + SG 自 11/19 00:00 MYT 起的花费，到 **RM5,950**（6,000 − 缓冲 50）就在 **campaign 层**
  关掉该账户所有 ACTIVE campaign、跳过 CPL 判定（日志 `SPEND CAP` / `CAP-PAUSE`，reason `spend_cap`）；11/25 15:00 后不动作。到线后周三 15:00 前
  owner 手动开回也会被再关——要例外 = 调高 cap_myr。读不到花费那一次跳过、下一次再查。合并后 main dry-run：周期花费 RM426（两边一致）。
  ② `kpi.exclude_bots: true`：报名表 S1 机器人从每支 ad 的 Meta 报名数扣掉（周四窗口 + 老将判定，严格 campaign › ad set › ad）。
  影响：BO 盖电脑 · ad 120251454701640329 去掉 10 个机器人后 10/16 起 12 报名 CPL≈60 → **不再是老将**（RM150 宽限没了），周四起 CPL 85 超线但
  1 单 CPA ~RM764 受成交保护 → 不关。按 RM1,200 硬线，它 60 天花费再加约 RM440 仍只有 1 单就会被 monitor 关（既有规则）。
  **以后每个周期的上限要 owner 重新给数字，并改 spend_cap 的 start / end / cap_myr。**
  **11/19 14:4x owner「day trading（webinarkit）里有什么需要值得开的吗？没有的话，campaign 就关掉」+「旧 1008 那 3 支开着的 ad 关掉」= 定案**：
  DT 1017 里 5 支 ad 全关、上线以来约 RM3,900 原位 0 单（年纪大 1,092/41 · korea 1,783/57 · 盖电脑 105/0 · 用我的方法 646/13 · 🚫赚美金 296/9；`report_dt_worth_1119.py`）
  → campaign 120251454713670329 关掉（`execute_close_dt_campaign_1119.py`，回读 PAUSED）。旧 STOCKBLOOM | DAY TRADING | 1-1-5 | 1008（campaign 120251329144280329，
  已关、非 Webinarkit）里 ad 层还开着的 3 支——盖电脑 · ad 120251329149060329、年纪大 · ad 120251329157060329、freestyle korea · ad 120251329160210329——
  ad 层 PAUSED（`execute_close_dt1008_ads_1119.py`，回读 PAUSED，1008 里 ad 层开着的 = 0）。都不得自动开回。
  同一轮 owner 质疑「为什么要加 News V4？」：News V4 唯一一单 = Paid 第 834 行 11/12 银行转账（11/11 经 News V4 报名 11/11 场、11/12 再无 UTM 报名 nov18）；
  这周它 RM37/0 报名 → 加预算建议**收回**；「V4→Business Owner、年纪大→News」新组合建议也收回（两支在 MY 的成交成本 RM1,500–2,100）。预算不变、无新建。
  **11/19 owner 新建法测试（「一个一个来」）· 第 1 个 = 两个 1-1-3（owner「两个 1-1-3…Broad MY 28+，预算 RM100/天，建好后是 PAUSED」+ 分组「按成绩分」）**：
  6 支素材（10/29 起有单 / 低 CPL，`report_top_creatives_1119.py`；post 链接全核对 = webinarkit-register-wed，`report_post_links_1119.py`）。
  15:39 建好（`execute_build_113_1120.py`，复用原 ad 的 creative = 同一个 Webinarkit post + 同 url_tags；SG 的用我的方法 post 在 MY 新建 creative 1506221654740169）：
  ① (Webinarkit) STOCKBLOOM | BEST CPA · Broad | 1-1-3 | 1120 · campaign 120251993979260329 · CBO RM100 · PAUSED › Broad | MY 28+ ·
     V4 决定变少 ad 120251993980970329 · 年纪大 ad 120251993983160329 · 盖电脑 ad 120251993984490329；
  ② (Webinarkit) STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120 · campaign 120251993985380329 · CBO RM100 · PAUSED › Broad | MY 28+ ·
     korea ad 120251993988780329 · V2 炒了五年 ad 120251993989200329 · 用我的方法 ad 120251993990070329。
  ad set / ad 已 ACTIVE（审核中），只等 owner 开 campaign。owner「跟新视频一样 RM80」→ PR #95（aa37b2c）`kpi.campaign_overrides` 加 `match: "1-1-3 | 1120"`（RM80/80/80）。
  **15:53 owner 本人（Power Editor）开了这两个 campaign**，同时两个 ad set 版位去掉 Instagram Explore（受众仍 Broad MY 28+）。6 支 ad Meta 15:41–15:45 已过审。
  → 在跑 MY 4 + 6 + SG 1 = 11 支，日预算 ≈ RM622（MY 492 / SG 130）。
  **第 2 个建法 CBO**：owner 先要「怎么判断好的受众」（`report_audiences_1119.py`：标准 = ①成交/CPA ≤1,200 ②报名→成交率 ③花够 ~RM1,200 才判 0 单 ④4 月起 Paid 历史 ⑤CPL 只看量；
  10/29 起 MY Luxury CPA 1,010 / 7.7%、BO 1,258 / 5.6%、News 1,513；MY Broad CPL 55 但 1.4%、CPA 4,050 = 陷阱）→ owner 选「Luxury + Beer + Omakase」。
  16:00 建好（`execute_build_cbo_1120.py`）：(Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · campaign 120251995650640329 · CBO RM150 · PAUSED，
  3 个 ad set（Luxury Goods / Beer / Omakase | MY 28+，兴趣硬锁 28–65）× 3 支 BEST CPA ad（V4 · 年纪大 · 盖电脑，复用原 creative）。
  ⚠️ 11/10 的「Luxury Goods」兴趣里已混了酒类 + 日料（41 个兴趣）→ 改用 MY 3.0 纯 luxury 的「LUXURY GOODS 30-55 | 0910 › Luxury Goods 30-55」(120248787849960575)，三组不重叠。
  owner「跟 1-1-3 一样 RM80」→ PR #96（d53b917）`match: "1-3-3 | 1120"`（RM80/80/80）。
  **SG 1-1-3**：owner 先选 Purchase LAL 5% SG，随即改「我觉得还是 broad 吧！让 meta 自己挑对的人报名」（LAL 版没写也没建）。16:06 建好（`execute_build_sg113_1120.py`）：
  (Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120 · campaign 120250705800700521 · CBO RM80 · PAUSED › Broad | SG 28+（Advantage+，建议 28–65，模板 SG BROAD SG 1030）·
  决定变少 ad 120250705802880521（MY News 有成交的 post，新建 SG creative 2674375702989899）· 年纪大 ad 120250705803610521（SG post）· 用我的方法 ad 120250705804890521。
  SG 一般规则本来就是 RM80/80/80，不用加 override。跟在跑的 SG BROAD SG 年纪大同受众（owner 知道会互抢）。
  **SG 第 2 个建法 CBO**（owner「SG 那边建 第二个建法」→「Purchase LAL + Investment + Luxury」）：16:20 建好（`execute_build_sgcbo_1120.py`）
  (Webinarkit) [SG] STOCKBLOOM | CBO · LAL INVEST LUX | 1-3-3 | 1120 · campaign 120250705919180521 · CBO RM100 · PAUSED，3 个 ad set：
  Purchase LAL 5% | SG 28+（来源 = 出过单的 1017 LAL 组 120249918199040521，不是 10/26 ALL LANG）· Investment | SG 28+（WINNERS 1020 交易/投资兴趣）·
  Luxury | SG 28+（SG LUXURY GOODS 1017，纯 luxury）× 决定变少 · 年纪大 · 用我的方法（SG creatives）。SG 规则 RM80，不用 override。
  **owner「MY CBO 预算 100 · SG 1-1-3 也是 100」**：16:3x 执行（`execute_budget_tests_1119.py`，回读 RM100 / RM100，仍 PAUSED）。
  **owner「SG 1-1-3 应该还有一个才对呀」→「建」**：16:51 建好（`execute_build_sg113b_1120.py`）(Webinarkit) [SG] STOCKBLOOM | LOW CPL · Broad | 1-1-3 | 1120 ·
  campaign 120250706566080521 · CBO RM100 · PAUSED › Broad | SG 28+ · korea ad 120250706569340521 · 炒了五年 ad 120250706569810521 · 盖电脑 ad 120250706571120521
  （MY 那三个 Webinarkit post，SG 新建 creative）。⚠️ korea / 盖电脑 11/05 在 SG 有旧副本被拒——若被拒立刻报告、建议 DELETE、不申诉。
  owner：「有些我可以安排在周六 / 周日开。你等下，再建议我吧」→ 全部建完后给开启时间建议。
  **owner「先不要建，等周日，你再问我」**：第 3 个建法起暂停；原排周日 11/22 10:30 再问——**owner 11/19 17:3x「取消」**（send_later 已删）：第 3 个建法起不再主动问，等 owner 自己提。
  owner 打算自己检查并开 4 个 PAUSED（MY CBO、SG 1-1-3 ×2、SG CBO）：全开后日预算 ≈ RM1,022（MY 592 / SG 430）。
  **owner 先选「方案 B，我排程自动开」（周六 MY CBO + SG 1-1-3 BEST、周日 SG CBO），17:1x 改主意「sg 我会先开 2 个 1-1-3，因为 sg 现在没有什么 campaign 在跑」**：
  WK 本人开了 SG 1-1-3 BEST · campaign 120250705800700521 + SG 1-1-3 LOW CPL · campaign 120250706566080521（17:1x 读回 6 支 ad 实际 ACTIVE）。
  接着「周六你看看到时候的成绩和预算，建议和问我要不要开 MY CBO SG CBO」→ **自动开启排程全部取消**（4 个 send_later 已删）。
  **周六 11/21 10:30** send_later（trig_01JnjKLdEHMsfsDBG1HeVPSS）：看**全部在跑的广告**的周四起成绩（owner「不是只给我 4 个 1-1-3 而是全部在跑的广告」）+ 周期花费推到周三 15:00，一个一个问 MY CBO · campaign 120251995650640329、
  SG CBO · campaign 120250705919180521 开不开；WK 说开才跑 `execute_open_tests_1121.py`（MY CBO）/ `execute_open_tests_1122.py`（SG CBO）——只开 campaign 层、读回每支 ad、
  有被拒 / 禁跑 ad 或周期花费已到 RM5,950 就拒绝。在投放日预算 → 约 RM822（MY 492 / SG 330）；照这样到周三 15:00 约 RM5,350。
  ⚠️ MY CBO + SG 1-1-3 + SG CBO 全开 ≈ RM950/天 → 约周三早上碰 RM5,950 上限被 monitor 全关（已告知 owner）。⚠️ 用我的方法、盖电脑、korea 11/05 有旧副本被拒（owner 例外 C）——这次若被拒，立刻报告、建议 DELETE、不申诉。
  **11/19 ~21:00 owner「CPL 都太高了，要做点什么」→ 选「MY 拿掉 AN」**（`report_cpl_now_1119.py`：MY 当天 AN RM135 = 26% / 0 报名；10/29 起 AN 28 报名 0 买家）。
  ⛔ **教训（我搞砸）**：`execute_my_drop_an_1119.py` 用 API 改版位——v21 API 读不到 owner 在 Ads Manager 设的版位排除（显示成自动版位），我写成明确版位后：
  23:38 实际写进 9 组（owner 叫停时已执行），顺带拿掉 WhatsApp Status / IG Explore home、还把 4 组原本没有的 IG Explore 打开，并让 9 组所有 ad（含 BO 里关着的 🚫 赚美金）重新送审。
  owner「你刚改的都复原」→ 23:44 `execute_my_restore_placements_1119.py` 写回不指定版位，但 IG Explore 变成全开（API 表达不了「关 Explore 留 Explore home」）→
  **owner 00:05–00:11 本人在 Ads Manager 手改**：9 组（BO、NV Broad V2、News V4/V5、MY 1-1-3 BEST/LOW CPL、MY CBO 3 组）= facebook + instagram + whatsapp + threads，
  无 Audience Network、无 IG Explore（留 Explore home），并取消「Allow limited spending to excluded placements」（勾着时被排除的版位仍会花约 5%/个）。
  核对用 META MCP 读 adset targeting（新版 API 看得到 publisher_platforms）。审核：全部重新过审，无被拒（🚫 赚美金 审完 Inactive）。SG 没改（SG 11/19 唯一报名来自 AN）。
  **以后版位一律 owner 在 Ads Manager 改；我不用 API 写版位**（只读核对）。
  **11/20 00:1x owner「不关」**：SG BROAD SG › Broad | SG 28+ · 年纪大 · ad 120250144813480521 周四起 RM122 / 1（CPL 122 > 80）但 1 单 CPA ~RM780 = SG 唯一有单 → 照跑；
  monitor RM1,200 CPA 硬线约再花 RM420 无第 2 单会自动关。
  **11/20 00:2x owner 本人在 SG BROAD SG（campaign 120250144810670521，CBO RM130 不变）开回 4 支「开完试试看」= 有效**：
  用我的方法 · ad 120250144813920521、我跟你讲 · ad 120250144814180521、不选 forex 不选黄金 · ad 120250144812470521、freestyle: korea · ad 120250144811900521
  （+ 原本在跑的年纪大 · ad 120250144813480521，5 支都 ACTIVE）。korea / 用我的方法 / 不选 forex 在 SG 有 11/05 被拒的旧副本（例外 C）——被拒立刻报告、建议 DELETE。
  用我的方法 60 天 RM1,185 / 1 单 → 再花约 RM15 无第 2 单会被 monitor CPA 硬线关；owner「照规则，让 monitor 关」= 不加 cpa.hold，被关后不得自动开回。
  **随即 owner「我关掉三个吧」= 定案**：用我的方法 · ad 120250144813920521、不选 forex · ad 120250144812470521、korea · ad 120250144811900521 ad 层 PAUSED（owner 本人，读回 PAUSED）。
  BROAD SG 在跑剩 年纪大 · ad 120250144813480521 + 我跟你讲 · ad 120250144814180521（CBO RM130）。
  **11/20 owner「你要来干嘛呢？你是负责广告而已」**：不再索取 Webinarkit 出席名单 CSV、报名后提醒 / Zoom link 设定截图；晨报 / 盘中检查不再问。只管广告。
  **11/21 owner「华语」**（我 11:47 汇报误用英文）：所有汇报 / 回复 / AskUserQuestion 一律用华语（简体中文），不用英文。
  **11/20 ~10:3x owner「sg 的很贵，都没有什么 leads」→「照跑，交给 monitor RM80」**：SG 周四起 RM432 / 1（CPM 190–320 ≈ MY 2 倍；37 LPV → 1 报名 ≈ 3%，上期 8–28%）。
  两个 SG 1-1-3 RM187 / 0（korea · ad 120250706569340521 已被 monitor 按 RM80 关），其余照跑到各自 RM80 由 monitor 判；BROAD SG 照跑。
  **11/20 ~10:2x–10:3x owner「因为 29/10 - 4/11 的成交不错（10人），所以我会开回 MY & SG 那段期间跑到不错的广告」→「我都开好了」**（owner 本人开回 = 有效，
  这些位置离开「owner 关 = 定案」名单；`report_live_budget_1120.py` 10:38 读回）：
  MY 开回 BROAD MY / BUSINESS OWNER / DAY TRADING / LUXURY MY / WINNERS MY 1022 的 9 支（BROAD MY korea · ad 120251456191090329、用我的方法 · ad 120251456458520329；
  BO 用我的方法 · ad 120251456457820329、年纪大 · ad 120251454702680329；DT korea · ad 120251455974450329、年纪大 · ad 120251454717600329；LUXURY 盖电脑 · ad 120251454697280329；
  WINNERS MY korea · ad 120251533795060329、盖电脑 · ad 120251533792260329），BO / BROAD MY / DT 的 CBO 现在都是 RM100；
  SG 开回 PURCHASE LAL 5% 1017（CBO RM60：用我的方法 · ad 120249918410030521、我跟你讲 · ad 120249918410840521）、TRAVEL SG 1030（CBO RM100：年纪大 · ad 120250144816380521）、
  WINNERS 1020（Investment › 用我的方法 · ad 120249964899250521 RM80、LAL 5% › 盖电脑 · ad 120250008788460521 RM65）。🚫 赚美金副本全部仍 ad 层 PAUSED；开着的 campaign 里 0 支禁跑 / 被拒 ad 上膛。
  **10:40 monitor 按 CPA 硬线关掉 3 支刚开回的** → owner「保护这两支到周三」+「三支都保护，合并后开回」→ **PR #97（dc0b15f）`cpa.hold_ad_until`**（只认 ad ID、到期自动失效、CPL 规则照判）：
  MY BROAD MY korea · ad 120251456191090329（60 天 CPA 2,584 / 1 单）、BO 年纪大 · ad 120251454702680329（1,646 / 1）、SG PURCHASE LAL 用我的方法 · ad 120249918410030521（1,206 / 1）都到 11/25；
  10:45 ad 层开回（`execute_reopen_cpa_hold3_1120.py`，回读三层 ACTIVE），main dry-run 三支 = `cpa_manual_hold`。
  在投放日预算 **RM1,425（MY 760 / SG 665）**；周期 11/19 起 RM1,312 → 照这个预算约 **周一 11/23 17:00 碰 RM5,950**，monitor 会在 campaign 层关掉两个账户全部 campaign 到周三 15:00。
  **11/20 ~11:xx owner「现在广告的规矩是什么？…首要目的：降低 CPL，拿到名单，报名的人都要是对的人」**：
  ① 我发现 PR #97 的保护**没有**让 CPL 照判（`combined_decision` 先回硬线、保护再改成留）→ 认错，死忌 4；**PR #98** 修（保护只免硬线）。
  ② owner「照建议」= 成交保护加上限 `cpa.rescue_max_x: 1.5`（CPL > 线×1.5 或 0 报名花到门槛×1.5，有成交也关；reason `cpa_rescue_over_cap`），并进 PR #98。
     分支 dry-run（11:33）：只有 SG BROAD SG › Broad | SG 28+ · 年纪大 · ad 120250144813480521（RM167/1，CPL 167 > 120）会关；BO 盖电脑 CPL 68、News V4 RM81/0 留。
     **owner「合并」→ PR #98 squash 合并（1372028）**；main dry-run 11:47：SG 年纪大 `cpa_rescue_over_cap` 会关，BO 盖电脑 6 报名 CPL 56 在线内，News V4 / 三支 CPA 保护留。
     **12:00 live monitor（1372028）已关 SG BROAD SG 年纪大 · ad 120250144813480521**（RM176 / 1，CPL 176，`cpa_rescue_over_cap`）= 新规则执行，不得自动开回；MY 0 支关。BROAD SG 里 我跟你讲 · ad 120250144814180521 照跑。
  ③ owner 提议 SG + 全部测试 campaign 改 RM60 门槛 / RM60 线（「没办法接受 CPL 整体超过 RM60」）并请我反驳 → `report_line_backtest_1120.py`（真实每小时数据，三期，扣机器人）：
     RM60 比 RM80 提早关掉的那一段 = RM1,546 / 42 真报名，CPL 37（比这些广告整体 65 便宜）→ 拿掉后 CPL 65 → 77。整体真 CPL：11/05–11/11 MY 41 / SG 60 / 合计 47；
     11/12–11/18 MY 46 / SG 74 / 合计 52（门槛与现在相同）；11/19–11/20 11:31 MY 86 / SG 504 / 合计 121。**owner「门槛维持 RM80」= 定案**
     （MY 一般 60/60、SG 80/80、测试 campaign 80/80 不变）。
  **11/20 12:0x owner「查一下这一期 CPL 为什么到 121」**（`report_cpl_why_1120.py` / `report_cpl_why2_1120.py` / `report_learning_1120.py`，同样经过时间 周四 00:00→周五 12:00）：
  这一期 RM1,564 / 15 报名 = CPL 104（11:31 的 121 是 Meta 报名还没回传完）vs 10/29 期 56 · 11/05 期 53（11/12 期有机器人不比）。追踪正常（Meta vs 报名表 11/19 MY 10/8、11/20 3/3）、CPM 正常、0 机器人。
  ① SG 最大：RM588 / 2（CPL 294），无 AN 的落地页→报名 3.3%（30 LPV→1）vs 13.6% / 22.0%；② MY 无 AN = CPL 63（= 11/05 期）、落地页→报名 12.3% 正常，
  多出来的是 11/19 AN RM153 / 39 LPV / 0 报名；③ 11/20 00–10 时 MY RM297 / 34 LPV / 1 报名——5 组 00:05–00:11 重大修改（我 23:38 API 改版位 + owner 手改）后回学习期；
  11/20 才开始投放的 7 支（owner 开回）RM103 / 5 LPV / 0。**owner 12:02 SG 8 组 + 12:04 MY 4 组拿掉 Audience Network、12:05 SG BEST 1-1-3 / LOW CPL 1-1-3 / TRAVEL SG CBO RM100 → RM80**
  （Power Editor，owner 本人 = 有效；这 12 组学习期重置、ad 重新送审，12:11 查 0 被拒 0 审核中）。日预算 → **RM1,365（MY 760 / SG 605）**，仍约周一 17:00 碰 RM5,950。
  ⚠️ ops.sh 不能同时跑两个（会抓错 run 的日志）。
  **11/20 12:2x owner「你再帮我盯紧一点」**：盘中检查改成**每小时 10:47–23:47 MYT**（trig_01KLefTqUatTBvX1135EcxPX，原 14/17/20/23 点）+ 09:52 晨报照旧；
  每次跑 `scripts/report_watch_hourly.py`（monitor 自己的判定逐支列、门槛/线、下一轮会关谁、被拒、学习期重置、报名表 vs Meta、机器人、预算 + 上限推算、ALERTS）
  + monitor 日志 + activity log。有事才报（monitor 关了什么 / 被拒 / 人为改动 / 下一轮会关 / 新 ALERTS），没事一行。只读，不替 owner 动广告。
  **11/20 17:1x owner「频密一点汇报我」**：排程器最短间隔 1 小时（30 分钟被拒，不绕过），改成**每小时 :47、07:47–00:47 MYT 每次都发简短汇报**（不再只有一行）：
  上次以来新报名、今天花费 / 报名、周四起 CPL、monitor 关了什么、下一轮会关 / 接近门槛、被拒、人为改动、ALERTS、最后一行在跑支数 / 日预算 / 周期花费。
  **11/20 15:01 monitor 按 SG 0 报名门槛 RM80 关**：WINNERS › Investment | SG 28+ · 用我的方法 · ad 120249964899250521（RM81.63 / 0，60 天 0 单）、
  WINNERS › LAL 5% · 盖电脑 | SG 28+ · 盖电脑 · ad 120250008788460521（RM82.79 / 0，60 天 0 单）= 规则正确（owner 早上开回的两支），不得自动开回。SG 在跑 10 支、日预算 → RM1,220（MY 760 / SG 460）。
  **16:13 owner 本人（Power Editor）关掉 SG WINNERS | 1-8-8 | 1020 campaign（120249964890710521）= 定案**（里面两支 15:01 已被 monitor 关）。
  **16:40 monitor 按 MY 0 报名门槛 RM60 关 LUXURY MY › Luxury | MY 28+ · 盖电脑 · ad 120251454697280329**（RM60.37 / 0，60 天 0 单）= 规则正确；LUXURY MY campaign（CBO RM60）已无在跑 ad。
  **17:12 owner 本人（Power Editor）关掉 LUXURY MY | 1-1-5 | 1017 campaign（120251454680840329）= 定案**（里面已无在跑 ad，日预算不变）。
  **18:40 monitor 按 SG 0 报名门槛 RM80 关 [SG] PURCHASE LAL 5% | 1-1-5 | 1017 › Purchase LAL 5% | SG 28+ · 用我的方法 · ad 120249918410030521**（周四起 RM81.96 / 0，`zero_results_over_min_spend`；60 天 CPA 1,288 / 1 单）= 规则正确（hold_ad_until 只免 CPA 硬线，PR #98），不得自动开回。同 campaign 的 我跟你讲 · ad 120249918410840521 照跑，CBO RM60 不变。
  **19:20 monitor 按 SG 0 报名门槛 RM80 关 [SG] TRAVEL SG | 1-1-2 | 1030 › Travel | SG 28+ · 年纪大 · ad 120250144816380521**（周四起 RM86.56 / 0，60 天 0 单，`zero_results_over_min_spend`）= 规则正确，不得自动开回；TRAVEL SG campaign（CBO RM80）已无在跑 ad。日预算 → RM1,080（MY 700 / SG 380），约周二 11/24 08:00 碰 RM5,950。
  **19:5x owner「有没有要我做决定的，要关的？」→ News V4 选「交给 monitor」**：NEW VIDEO · News › News | MY 28+ · V4 · ad 120251840059300329 周四起 RM89.67 / 0 报名、60 天 CPA 517 / 1 单（`cpl_high_but_cpa_ok`）→ 不手动关，照 rescue_max_x 上限花到 RM120 仍 0 报名由 monitor 关。下一题待问：3 支 60 天 0 单的老将（WINNERS MY 盖电脑 · ad 120251533792260329、DT korea · ad 120251455974450329、DT 年纪大 · ad 120251454717600329）RM150 宽限——等它们过 RM60 仍 0 报名再问 owner 要不要提早关。
  **21:40 monitor 按线关 LOW CPL · Broad | 1-1-3 | 1120 › Broad | MY 28+ · 用我的方法 · ad 120251993990070329**（周四起 RM80.01 / 1，CPL 80.01 > 线 80，`cpl_over_threshold`，60 天 0 单）= 规则正确，不得自动开回；同 campaign 的 korea / 炒了五年照跑，CBO RM100 不变。
  **22:00 monitor 按 MY 0 报名门槛 RM60 关 WINNERS MY | 1-6-6 | 1022 › Broad · korea | MY 28+ · freestyle: korea · ad 120251533795060329**（周四起 RM61.84 / 0，60 天 0 单，`zero_results_over_min_spend`）= 规则正确，不得自动开回。日预算 → RM1,030（MY 650 / SG 380），约周二 11/24 11:30 碰 RM5,950。
  **22:5x owner「现在关」= 定案**（22:47 汇报后 AskUserQuestion）：WINNERS MY | 1-6-6 | 1022 › Broad · 盖电脑 | MY 28+ · 盖电脑 · ad 120251533792260329（周四起 RM67.54 / 0，60 天 0 单，老将 RM150 宽限中）ad 层 PAUSED（`execute_close_winners_gdn_1120.py`，dry-run → 执行，回读 PAUSED）；该 ad set（RM50）已无在跑 ad。不得自动开回。日预算 → RM980（MY 600 / SG 380）。DT korea（RM62 / 1）/ DT 年纪大（RM42 / 0）仍在老将宽限内，过 RM60 仍 0 报名再问。
  **23:0x owner「如果 campaign 里 ad set 都关完了，请帮我把 campaign 也关掉」= 常设规则**：`execute_close_empty_campaigns_1120.py`（两账户扫所有 status=ACTIVE 的 campaign，0 支「ad ACTIVE 且 ad set ACTIVE」的 ad → campaign 层 PAUSED；ad / ad set 不动；PAUSED 的 campaign 不碰）。dry-run → 执行，关了 2 个（回读 PAUSED）：WINNERS MY | 1-6-6 | 1022 · campaign 120251533789970329、[SG] TRAVEL SG | 1-1-2 | 1030 · campaign 120250144814410521。其余 12 个 ACTIVE campaign 都还有在跑 ad。以后每小时汇报若有 ad 被关，先 dry-run 这支脚本，有 EMPTY 就关并在汇报里写（trig_01KLefTqUatTBvX1135EcxPX 已加第 4 步）。日预算不变（空 campaign 本来就不花）。
  **23:00 monitor 按线关 [SG] BEST · Broad | 1-1-3 | 1120 › Broad | SG 28+ · 决定变少 · ad 120250705802880521**（周四起 RM80.13 / 1，CPL 80.13 > 80，`cpl_over_threshold`，60 天 0 单）= 规则正确，不得自动开回；同 campaign 还有 用我的方法 / 年纪大 在跑（空 campaign 检查 0 个）。
  **11/21 夜里 monitor 关了 3 支（都 60 天 0 单，规则正确，不得自动开回）**：01:20 [SG] BEST · Broad | 1-1-3 | 1120 › Broad | SG 28+ · 用我的方法 · ad 120250705804890521（RM82.44 / 1，CPL 82.44 > 80）；
  03:20 BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · 用我的方法 · ad 120251456457820329（RM60.11 / 1，CPL 60.11 > 60）；07:40 [SG] PURCHASE LAL 5% | 1-1-5 | 1017 › Purchase LAL 5% | SG 28+ · 我跟你讲 · ad 120249918410840521（RM83.32 / 0）。
  **07:5x 常设规则关空 campaign**：[SG] PURCHASE LAL 5% | 1-1-5 | 1017 · campaign 120249918198320521（CBO RM60，dry-run → 执行，回读 PAUSED）。日预算 → RM920（MY 600 / SG 320）。
  **08:40 monitor 按 SG 0 报名门槛 RM80 关 [SG] NEW VIDEO · Broad | 1-5-1 | 1110 › Broad | SG 28+ · V4 · ad 120250544546540521**（周四起 RM81.06 / 0，60 天 0 单）= 规则正确，不得自动开回；**08:5x 常设规则关空 campaign** [SG] NEW VIDEO · Broad | 1-5-1 | 1110 · campaign 120250544490730521（ABO，回读见当次日志）。日预算 → RM860（MY 600 / SG 260）。
  **11/21 10:12 / 10:18 Meta 拒审 SG 两支（Meta 未给原因；activity log：之前无人修改）**：[SG] LOW CPL · Broad | 1-1-3 | 1120 › Broad | SG 28+ · 炒了五年 · ad 120250706569810521、[SG] BROAD SG | 1-1-5 | 1030 › Broad | SG 28+ · 我跟你讲 · ad 120250144814180521（`report_rejected_1121.py`）。我推荐按 9/23 全禁（DELETE + 副本 ad 层 PAUSED + 🚫），**owner 选「C 先不动」= 本人例外**：两支被拒 ad 留在账户、不 DELETE、不申诉；同母带副本（MY LOW CPL 1-1-3 › 炒了五年 · ad 120251993989200329 在跑；我跟你讲 MY 1 + SG 9 支 ad 层开着、上层关着）照旧，不进 banned_creatives、不加 🚫。BROAD SG campaign（CBO RM100）已无可投放的 ad。以后报告照列「被拒」但不再建议处理，除非 owner 再提。**11:5x owner：「被 reject 的那两个我已经 request review 了，所以先不要做任何东西先」**＝owner 本人申诉（同 10/8 不选 forex、10/25 赚美金的本人例外，我们不代为申诉）——两支不动；复审结果（转 ACTIVE 或仍 DISAPPROVED）出来第一时间报告 owner。
  **11/21 10:30 周六复盘（owner「现在开」×2，我两次都推荐不开：周末报名出席 4%、会把 RM5,950 上限提前到周二下午）**：周四起 MY RM1,627 / 21 = CPL 77、SG RM1,261 / 12 = CPL 105（`report_double_check_1108.py` / `report_morning_watch.py`）。10:41 开 MY CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · campaign 120251995650640329（`execute_open_tests_1121.py`，dry-run → 执行，9 支回读 ACTIVE）；10:45 开 SG CBO · LAL INVEST LUX | 1-3-3 | 1120 · campaign 120250705919180521（`execute_open_tests_1122.py`，dry-run → 执行，9 支回读 ACTIVE）。日预算 → **RM960（MY 700 / SG 260）**；周期 11/19 起 RM2,890 → 照这个预算约 **周二 11/24 15:15 碰 RM5,950**（线性推算，未验证），monitor 会在 campaign 层关两个账户全部 campaign 到周三 15:00。11:45 send_later（trig_01E63piv6CiEYNeBjeiWKjUx）只读 `report_open_tests_check_1121.py` 确认 18 支在花钱。11:45 实测：18 支都实际 ACTIVE、0 被拒；开了约 1 小时 MY CBO RM21 / SG CBO RM18，各有 1 支还是 RM0（MY Beer › 盖电脑 · ad 120251995665060329、SG Purchase LAL 5% › 决定变少 · ad 120250705922330521），CBO 正常分配。（两支分别 12:19 / 11:55 开始投放。）**12:50 发现**（`report_sg_an_1121.py`）：SG CBO 的 Luxury | SG 28+ · adset 120250705933050521、Investment | SG 28+ · adset 120250705927390521 是自动版位、含 Audience Network（11/20 owner 拿掉 SG 8 组 AN 时这个 campaign 还关着，没改到），今天 AN 花 RM9.01 / RM0.10；已报 owner，版位只由 owner 在 Ads Manager 改。**13:53 owner 本人（Power Editor）拿掉 SG CBO 3 组的 AN**（Purchase LAL 5% · adset 120250705920790521、Investment · 120250705927390521、Luxury · 120250705933050521 → facebook + instagram + whatsapp + threads，IG 只留 Explore home；META MCP 读回确认）= 有效。13:54 9 支 ad 换了新 creative ID、回到 IN_PROCESS（重新处理 / 送审），学习期重置；下一次汇报确认回到 ACTIVE、无被拒。（13:57–13:58 Meta 9 支全部重新过审 → ACTIVE，0 被拒。）
  ⚠️ **14:49 更正**：BUSINESS OWNER › Business Owner | MY 28+ · 年纪大 · ad 120251454702680329 是**老将 + CPA 保护**，门槛 RM150 不是 RM60——`cpa_manual_hold` 会把 `veteran_wait` 盖掉，`report_watch_hourly.py` 因此误显示「门槛 60」（12:47 / 13:47 汇报照抄了「离 RM60 差 RMx」，误导）；RM61 / 0 时 monitor 实际判「留」。脚本已修（4dac3ed）。按代码到 RM150 仍 0 报名会关（未实测）。
  **11/21 ~15:0x owner「CPL 太高了」→「3 支都关」= 定案**：周四起 MY RM1,787 / 27 = CPL 66 拆开 = 已关 ad RM542 / 3（CPL 181）+ 在跑 RM1,245 / 24（CPL 52）；SG 已关 RM1,136 / 9 + 在跑 RM231 / 6（CPL 38）。在跑里靠老将 / CPA 保护活着的 3 支 RM239 / 2（CPL 120）ad 层 PAUSED（`execute_close_3drags_1121.py`，dry-run → 执行，回读 PAUSED）：DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · freestyle: korea · ad 120251455974450329（RM124 / 2，10/29 起 0 单）、BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · 年纪大 · ad 120251454702680329（RM61 / 0，60 天 CPA 1,242，原有 cpa.hold 到 11/25）、DAY TRADING › Day Trading | MY 28+ · 年纪大 · ad 120251454717600329（RM54 / 0，10/29 起 0 单）。常设规则关空 campaign：DAY TRADING | 1-1-5 | 1017 · campaign 120251454713670329（CBO RM100，回读 PAUSED）。BUSINESS OWNER 只剩盖电脑 · ad 120251454701640329（CBO RM100 全给它，周四起 CPL 58）。都不得自动开回。日预算 → RM810（MY 550 / SG 260）。DT 年纪大的待问题已结案。
  **17:20 monitor 关 BEST CPA · Broad | 1-1-3 | 1120 › Broad | MY 28+ · 决定变少 · ad 120251993980970329**（周四起 RM80.78 / 0，60 天 0 单，`zero_results_over_min_spend`）= 规则正确，不得自动开回；BEST CPA 还有年纪大 / 盖电脑在跑（空 campaign 检查 0 个）。
  **11/22 00:40 monitor 按 SG 0 报名门槛 RM80 关 [SG] BEST · Broad | 1-1-3 | 1120 › Broad | SG 28+ · 年纪大 · ad 120250705803610521**（周四起 RM81.32 / 0，60 天 0 单，`zero_results_over_min_spend`）= 规则正确，不得自动开回；**00:50 常设规则关空 campaign** [SG] BEST · Broad | 1-1-3 | 1120 · campaign 120250705800700521（CBO RM80，dry-run → 执行，回读 PAUSED）。SG 在跑 10 支、日预算 → RM730（MY 550 / SG 180），约周三 11/25 07:40 碰 RM5,950（推算）。
  **11/22 13:40 monitor 按 SG 0 报名门槛 RM80 关 [SG] CBO · LAL INVEST LUX | 1-3-3 | 1120 › Investment | SG 28+ · 用我的方法 · ad 120250705932290521**（周四起 RM80.48 / 0，60 天 0 单，`zero_results_over_min_spend`）= 规则正确，不得自动开回；SG CBO 还有 8 支在跑（空 campaign 检查 0 个）。
  **11/22 14:1x owner「有沒有要建議我的？」→ 上限选「维持 RM6,000」= 定案**（`report_wed_morning_1122.py`：过去三期周三 00:00–15:00 RM2,489 / 43 报名 CPL 58 ≈ 周四–周日 61；11/11 期周一–周三报名出席 30% vs 周末 4%）。推算约周二 11/24 23:20 碰 RM5,950、到周三 15:00 两边全关，owner 知情接受。这期不再提加上限 / 调预算。
  **11/21 13:40（activity log 时间；不是 11/22）monitor 关 NEW VIDEO · News | 1-5-1 | 1110 › News | MY 28+ · V4 · ad 120251840059300329**（周四起 RM120.13 / 0，60 天 CPA 547 / 1 单，`cpa_rescue_over_cap`）= owner 11/20「交给 monitor」的结果，规则正确，不得自动开回；NEW VIDEO · News 还有 V5 在跑（空 campaign 检查 0 个）。日预算 → RM910（MY 650 / SG 260），约周二 11/24 17:00 碰 RM5,950。
  **11/23 02:20 monitor 按线关 [SG] CBO · LAL INVEST LUX | 1-3-3 | 1120 › Luxury | SG 28+ · 用我的方法 · ad 120250705940700521**（周四起 RM81.11 / 1，CPL 81.11 > 80，`cpl_over_threshold`，60 天 0 单）= 规则正确，不得自动开回；SG CBO 还有 7 支在跑（空 campaign 检查 0 个）。⚠️ 日志里这行写成「[PAUSE (carrier CPL 64 ok — budget kept)]」——grep 要用 `\[PAUSE`，不能用 `\[PAUSE\]`（00:47→07:47 那轮一开始漏看）。
  **11/23 10:xx owner「SG 那边我还可以怎么搞？怎么建」→ AskUserQuestion 选「建好后今天就开」**（`report_audiences_1119.py` / `report_top_creatives_1119.py` 11/23 10:07，10/29 起、报名表真报名去机器人：SG Broad RM4,596 / 57 真报名 / 2 单 / CPA 2,298 = SG 唯一有量有单的受众；SG 兴趣受众合计 5 真报名 0 单；SG Travel RM1,527 / 13 / 0 单；SG 素材有单 = 用我的方法 2、年纪大 1；决定变少 真 CPL 76；MY 同期约 RM2,965/单、SG 约 RM3,000/单）。10:17 建好（`execute_build_sgpool_1123.py`，dry-run → 执行）：(Webinarkit) [SG] STOCKBLOOM | BROAD POOL | 1-1-4 | 1123 · campaign 120250754563820521 · CBO RM100 · PAUSED › Broad | SG 28+ · adset 120250754564410521（Advantage+，建议 28–65，模板 SG BROAD SG 1030）· 4 支 ad 直接复用 SG 原 creative（同 post、同动态 url_tags）：年纪大 · ad 120250754565380521、用我的方法 · ad 120250754566010521（原 BROAD SG 那位 11/20 owner 关的，这是新位置）、决定变少 · ad 120250754566360521、盖电脑 · ad 120250754568750521。盖电脑的 post 1001334883061622_122126499021286543 现在读不到链接（token 缺 pages_read_engagement），用 11/19 核对记录 + nov25 报名表 6 笔 SG LOW CPL 报名作证据。版位没写（建好时 META MCP 读回 = 自动版位含 audience_network / IG explore）。**owner 本人（Power Editor）10:25 拿掉 IG Explore、10:26 开 campaign、10:29 拿掉 Audience Network = 有效**（META MCP 读回：facebook + instagram + whatsapp + threads，IG 只留 explore_home，无 AN）；改版位让 3 支 ad 换了新 creative ID、重新送审，10:3x 读回 4 支 PENDING_REVIEW / IN_PROCESS、RM0——下一次汇报确认转 ACTIVE、开始花钱、无被拒。`execute_open_sgpool_1123.py` 没用到（owner 自己开）。SG 规则 RM80/80，不用 override。⚠️ 盖电脑 / 用我的方法 11/05 在 SG 有旧副本被拒（例外 C）——被拒立刻报告、建议 DELETE、不申诉。（10:32–10:34 4 支重新过审 ACTIVE，10:38–10:39 开始投放。）
  **11/23 ~11:0x owner「MY 那边还可以怎么建？还是不建议建？」→ 选「这期不建，下期再调」= 定案**：理由（死忌 4 已标推测）：上限 RM6,000 固定，再开只是把周二之后的钱提前花；MY 在跑 17 支周四起 CPL 42，本期 MY 新建 3 个测试（BEST CPA / LOW CPL 1-1-3、CBO · LUX BEER OMAKASE，含已关）合计 RM1,221 / 28 = CPL 44 ≈ 在跑；MY 问题在成交：10/29 起 Broad RM5,430 / 101 真报名 / 1 单（1.0%）vs Business Owner 4.4% · Luxury 6.7% · News 4.3%（样本 1–2 单）。**待办：周三前把下期（周四 11/26 开）MY 结构写好给 owner 批——钱从 Broad 往 Business Owner / Luxury / News 移；批了才建；下期上限要 owner 给新数字。**
  **11/23 17:40 monitor 按 CPA 硬线关 BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · 盖电脑 · ad 120251454701640329**（周四起 RM611.35 / 10，CPL 61；60 天 CPA 1,204 / 1 单 > 1,200，`cpa_hard_stop`）= 规则正确（11/19 已预告「60 天再花约 RM440 仍 1 单就会被关」），不得自动开回。**17:50 常设规则关空 campaign** (Webinarkit) STOCKBLOOM | BUSINESS OWNER | 1-1-5 | 1017 · campaign 120251454700150329（CBO RM100，dry-run → 执行，回读 PAUSED）。日预算 → RM730（MY 450 / SG 280），推算约周二 11/24 17:20 碰 RM5,950。
  ⚠️ **11/23 16:00–17:00 News V5 · ad 120251840063080329 Meta 记 3 个报名，但那一小时只有 1 次点击 / 1 LPV**（ad 每小时数据）；报名表 MY 广告今天 8 vs Meta 13 → 疑似同一人重复报名或像素重复计（推测，未验证）。monitor 用 Meta 数，这 3 个会让 V5 看起来比实际好。
  **11/24 09:40 monitor 按线关 [SG] BROAD POOL | 1-1-4 | 1123 › Broad | SG 28+ · 用我的方法 · ad 120250754566010521**（周四起 RM84.29 / 1，CPL 84.29 > 80，`cpl_over_threshold`，60 天 0 单）= 规则正确，不得自动开回；BROAD POOL 还有 决定变少 / 盖电脑 / 年纪大 在跑（空 campaign 检查 0 个）。
  **11/24 11:01 monitor 按线关 CBO · LUX BEER OMAKASE | 1-3-3 | 1120 › Luxury Goods | MY 28+ · 决定变少 · ad 120251995655320329**（周四起 RM80.40 / 1，CPL 80.40 > 80，`cpl_over_threshold`，60 天 0 单）= 规则正确，不得自动开回；MY CBO 还有 7 支在跑（空 campaign 检查 0 个）。
  **11/24 14:20 周期花费碰 RM5,950 关停线（monitor SPEND CAP：RM5,950.73）→ monitor 在 campaign 层 `CAP-PAUSE` 两个账户全部 9 个 ACTIVE campaign**（activity log 14:20 STOCKBLOOM-ADS 9 条 Active→Inactive 对得上；14:50 读回两账户 0 个 ACTIVE campaign、0 支在投放）：MY BROAD MY | 1-1-5 | 1017 · 120251454704570329、NEW VIDEO · News | 1-5-1 | 1110 · 120251840045110329、BEST CPA · Broad | 1-1-3 | 1120 · 120251993979260329、LOW CPL · Broad | 1-1-3 | 1120 · 120251993985380329、CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · 120251995650640329；SG BROAD POOL | 1-1-4 | 1123 · 120250754563820521、LOW CPL · Broad | 1-1-3 | 1120 · 120250706566080521、CBO · LAL INVEST LUX | 1-3-3 | 1120 · 120250705919180521、BROAD SG | 1-1-5 | 1030 · 120250144810670521。ad / ad set 层没动。到周三 15:00 前有人开回会被下一轮再关；15:00 后 cap 不再动作，campaign 保持 PAUSED，下期由 owner 自己开（周四开回 = owner 手动）。这期最终：周四起 MY RM3,719 / 76 报名 CPL 49、SG RM2,235 / 23 CPL 97，合计 RM5,954 / 99 = CPL 60（Meta 数）。
  日预算 → RM1,160（MY 700 / SG 460），约周二 11/24 02:00 碰 RM5,950。
  **11/16 23:01 monitor 关 SG BROAD SG 用我的方法 · ad 120250144813920521**（CPL 98.55）——那次 Meta 400 读不到 60 天花费，CPA 保护失效（60 天 CPA 约 1,191 本应受保护）；
  离 RM1,200 硬线只差约 RM9，建议不开回。owner「修」→ **PR #92**：读不到 CPA 数据的那一次不做任何 CPL / 0 报名关停（reason `cpa_unavailable_hold`），禁跑照关，下一次再判。
- **11/12 晚 monitor 两项改动（PR #90，owner「改吧」+「SG 的关停线从 95 降到 80」）**：
  ① 成交比对忽略 campaign 名中间的「| 1-1-4 |」结构段（BUSINESS OWNER / BROAD MY 由 1-1-4 改名 1-1-5，ad 的 UTM 仍是旧名），
  其余照旧（同 campaign · 同 ad set · 同 ad）；上线前查过 MY 15 / SG 60 个 campaign 0 撞名，受影响只有 BUSINESS OWNER 年纪大、盖电脑 各认回 1 单。
  ⚠️ **教训（11/12 21:40）**：认回成交不等于「受保护」——monitor 的 CPA 用 **60 天花费 ÷ 成交**。BUSINESS OWNER 年纪大 · ad 120251454702680329
  认回 1 单后 CPA = 60 天 RM1,640 / 1 → 超 RM1,200 硬线，被 monitor `cpa_hard_stop` 关掉（改之前看作 0 成交，不触发硬线）。
  我事前用 10/29 起花费说它会受保护 = 算错窗口。owner「照关」。以后判断「会不会被保护 / 被 CPA 硬线关」一律用 monitor 的 60 天口径。
  ② **SG 关停线 95 → 80**（`config.sg.yaml` kpi.cpl_threshold_myr）。老将 RM150 宽限照旧（owner 未批取消）。owner 方针：「把 CPL 降下来…贵、浪费钱的广告就关掉」。
- **11/12 21:30 owner 本人在 Ads Manager 手动调整（activity log 取证）**：
  - MY **DAY TRADING | 1-1-5 | 1017 开回**（campaign 120251454713670329，CBO RM165）+ 两支 ad 开回：
    Day Trading | MY 28+ · 年纪大 · ad 120251454717600329、korea · ad 120251455974450329（owner 11/9 手动关的，这次他本人开回 = 有效）。
  - SG：关掉 NEW VIDEO · Broad › V2 · ad 120250544539830521、Golf Pickleball › V1 · ad 120250544690430521；
    NEW VIDEO · Travel / Golf Pickleball 两个 campaign 层关掉。SG 新视频只剩 Broad › V4 · ad 120250544546540521。
  - MY 新视频他点了几下开关，最终状态不变（7 支照跑）。日预算 → 约 RM965（MY 785 / SG 180）。
- **11/12 22:xx owner 定案**：「关」→ BROAD MY 两支关掉（korea · ad 120251456191090329：10/29 起 CPA RM1,662；盖电脑 · ad 120251454707880329：
  10/16 起 RM106 / 0 报名；`execute_broadmy_close_1112.py`），BROAD MY campaign 已无在跑 ad；BUSINESS OWNER 年纪大「照关」；
  **老将 RM150 宽限保持**；**MY 0 报名门槛 RM80 → RM60**（PR #91，新视频仍 RM80）。日预算 → 约 RM815（MY 635 / SG 180）。
- **11/12 22:09 新视频「留子弹」（owner「做」：「先暂时关掉没有出成绩的广告…等 2 天后…才开…平摊广告留子弹给 2 天后」）**：
  当天 0–1 报名的 4 支先停（Luxury V1 · ad 120251840350550329、V2 · ad 120251840352430329、V4 · ad 120251840364150329、
  News V5 · ad 120251840063080329；`execute_nv_hold4_pause_1112.py`），**周六 11/14 00:00 自动开回**（`execute_nv_hold4_reopen_1114.py`，
  排程 trig_015BgBKsgnmWwNtWPG3zJmZx）。这 4 支是「暂停待开」，不是 owner 定案关。继续跑：MY Broad V2、News V2、News V4、SG Broad V4。
  日预算 → 约 RM615（周六开回后回到约 RM815）。注意：开回后它们本周已花 RM64–69，monitor 很快在 RM80 判。
- **出席数据（11/11 场，报名表 × Webinarkit 出席名单）**：广告带来的 101 个报名只来 18 人（18%）；周四–周日报名 2/48（4%）、
  周一–周三 16/53（30%）；65 人在 Webinarkit 完全没有记录（从没点进场链接）→ 怀疑报名后的提醒 / Zoom link 流程有漏，已请 owner 查。
- 2026-11-10 建了 MY（News / Luxury Goods / Broad）+ SG（Broad / Travel / Golf Pickleball）各 3 个 `NEW VIDEO … | 1-5-1 | 1110`，
  Video 57–61（`scripts/specs_newvideo_1110.json`、`execute_build_newvideo_1110.py`）。News 的原始来源（旧账户 MTC - News）已无读取权限，
  兴趣改用 MY 3.0「AdSet (News MY 25+)」。

## Monitor 触发（2026-11-03 起）

GitHub 自带的 `schedule` 实测只有 3–10 小时跑一次（cron 写 20 分钟，被 GitHub 节流），所以 owner 11/3 选方案 A：
**cron-job.org 每 20 分钟各 POST 一次 `workflow_dispatch`**（「adbot monitor MY」→ `adbot-monitor-my5.yml`、
「adbot monitor SG」→ `adbot-monitor-sg.yml`，body `{"ref":"main"}`，dry_run 默认 false = 正式执行），GitHub schedule 留作备份。
用 owner 的 fine-grained token（只开 soocheng-ads · Actions read/write）—— **2026-12-03 到期，到期前要换**（11/30 已排提醒）。
验证：两条 workflow 的 run list 里应每 20 分钟出现一次 `workflow_dispatch`。

## 账户现况（2026-10-08）

- **MY 3.0 `act_759339046918885` 已封（2026-09-23）**——只读取证用，不投。
- **MY 5.0 `act_2285351942292267`「[MY] MTC X SB 5.0」**（config `config/config.my5.yaml`，pixel 2602956993413536）：
  2026-10-08 建了 3 条 1-1-5（DAY TRADING / BUSINESS OWNER 兴趣硬锁 30+、BROAD 30+），每条 CBO RM100，
  同样 5 支干净 post 复用 ad。**与两个被封账户、SG 同一个 BM（Soo Cheng X MTC 2 / 769016565904540）**——
  这里任何一支被拒都是整个 BM 家族的 strike：只上从没被拒过的素材、小预算、被拒立刻 DELETE 不申诉。
- **SG `act_893025326577600`**（`config/config.sg.yaml`）：唯一有投放历史的活账户，14/10 直播的流量来源。
  **SG 目标线（owner 2026-11-02「照这个计划走」）**：SG 贵在 CPM（10/29–11/2 RM240 vs MY 122），CTR / 报名页转化与 MY 相同；
  但 SG 报名转成交 6.0% vs MY 3.7%（9/1 起，按电话国码）→ **SG CPL ≤80 ≈ MY CPL 48 的每学员成本**，所以 SG 判「好」用 ≤80，
  monitor 关停线仍是 95。直播后按每学员成本判（≤RM1,500 加码 / >RM2,000 砍）；SG 不再试「不锁语言 ALL LANG」（10/26 测试 0 报名）。
- **2026-10-08 15:13 SGT，MY 5.0 DAY TRADING 的 `Video：不选 forex 不选黄金` 被拒**（团队成员在 Ads Manager
  把它改成 WhatsApp 目的地 → 新 creative → 重审 → Not approved；通知里露出的文案「涨跌都能赚，而且不用自己的本钱」
  是收益承诺 + 零本钱，同一段文案挂在 SG 4 个在跑位上）。**owner 决定自行申诉（规则第三条的例外，他本人拍板）**；
  申诉当天再被拒，owner 把 MY 5.0 的 3 支副本删掉。**owner 2026-10-08 裁定「MY 是 MY，不用碰到 SG」**：
  这次被拒**不外溢到 SG**——SG 的 不选 forex 位照跑，`不选 forex` **不进** banned_creatives、不加 🚫；
  报告 / monitor 不得再把 SG 的 不选 forex 列为「需要关」。（这是 owner 对 9/23 全家族规则的本人例外，仅此一支。）
  教训：**新账户的 ad 不要在 Ads Manager 里改 creative / 加 WhatsApp**——改一次 = 新 creative 重审一次。

## UTM 追踪（2026-10-29 诊断 + 修好）

10/21、10/28 两场的 Register 表 UTM **不是本次报名的来源**，而是客户系统里该联系人的「第一次来源」
（webinar_oct28：回头客 57/68 带旧 campaign UTM、其中 50 个与其首次报名完全相同；新客 93/100 空白；
(Webinarkit) campaign UTM = 0）——所以「成交对不回 Webinarkit 广告」是追踪假象，不是广告没带单。
**修法（10/29 上线并验证）**：GHL 报名页 tracking code 把网址 utm_campaign / utm_source / utm_content /
utm_medium 写进 Webinarkit 隐藏栏位 Custom Field 2 / 3 / 4 / 5；写 Register 表的自动化改读这 4 个栏位。
⚠️ 以后**每换一个报名页都要贴同一段 tracking code**（`webinarkit-register-wed` 现跳转 `1-page-187152-527570-516624`）。
10/28 及以前的 Register UTM 不可用于成交归因。

## Key locations

- **Approved copy bank** (the 8 ads): Notion page **"SOOCHENG-Andromeda"**
  (`38a82b424496810f8df7c2debb7c410f`).
- **Content Pipeline DB:** Notion "Stock Bloom Content Pipeline Template".
- **Copy-gen prompt:** `prompts/caption_system.md` · **Audience truth:** `config/audience.md`.
- **Ops commands** (build / monitor / weekly): `skills/meta-ops/SKILL.md`.
