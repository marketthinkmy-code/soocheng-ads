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
