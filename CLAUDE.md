# CLAUDE.md — STOCK BLOOM (Soo Cheng) ad ops + copy SOP

Standing instructions for any Claude session in this repo. Read this before writing ad
copy or building ads.

**Product:** Soo Cheng 老师《1 分钟短线交易盈利营》— a 1-minute short-term (futures)
trading course, sold in Malaysia. Funnel: Meta ad → **free Zoom 分享会 registration (the
lead)** → RM2,399 course. The ad objective is always *registration for the free 分享会*.

---

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
A creative is an **image + its copy as ONE bound unit.** The build joins them *only* through
the manifest's `content_id ↔ file_id` pairing — copy and image are pulled from separate
sources and meet nowhere else. So if that pairing is guessed, the picture says one thing and
the caption says another. That "WRONG match" got 2 campaigns deleted. **Always derive the
pairing by reading each image's on-image text first; never write a "best-guess" pairing into
a manifest and ship it.**

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

### 📋 送审历史 (rejection history — OWNER POLICY 2026-07-30: judge by review status + CPL/CPA only)

**Owner directive 2026-07-30:「禁跑的广告都不要直接关了，因为他们都过审。一切以 CPL CPA 为主。」**
The old hard-ban treatment is retired. The rules now:

- A creative's **current Meta review status** is the only gate: if it PASSES review it may run,
  be scaled, and be rebuilt — rejection history alone is NEVER a reason to pause, exclude, or
  refuse it. If it sits DISAPPROVED it can't deliver anyway; resubmitting is the owner's call
  (each re-rejection adds a policy strike on a repeat-offender account — advise, don't block).
- **Pause decisions belong to the CPL/CPA monitor only** (CPL>RM50 after RM80 spend, 0-reg
  after RM80, CPA hard-stop RM1,200; converting ads are CPA-rescued). The monitor has NEVER
  enforced any ban list — do not pause an ad because of its rejection history.
- Income-claim content (「每週盈利 200-300 US」 etc.) still violates Meta policy and keeps
  failing review — for those, prefer re-cutting a clean version (forensics + compliant
  re-edit guide: `scripts/archive_ban_list.py`). This is advice about what will pass review,
  not a run/no-run rule.

History (for context, not enforcement): video 3 不是怕交易 / video 4 厌倦了等待 / moomoo /
video 1 1分钟赚300 / 每天1分钟就能盈利 — rejected for baked-in income claims (incl. rebuilds).
video 2 你敢吗 / freestyle 2 — rejected 2026-07-16; owner reports they later passed review.

✅ **video 12：炒过那么多，累而且不稳定 — UN-BANNED 2026-08-07（owner:「跑吧。解禁」）.**
It sold 8 单 in July and another on 8/5 via SG DAY TRADING, so the owner lifted the 07-30 禁跑.
It is now governed like every other creative: current Meta review status + CPL/CPA only.
History for caution, not enforcement: rejected 07-16 → TOP3 resubmission passed (SG) → fresh
copies in BEER/DAY TRADING were rejected again 07-30 (later instances passed). When scaling it,
PREFER reusing already-approved instances over building fresh copies — each new rejection adds a
policy strike on this repeat-offender account family.

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

## 每周排程（owner 2026-08-19 确认「留着」）

**MY 账户每周三 15:00 MYT 全停（adbot-weekly-off）→ 周四 00:00 MYT 自动恢复（adbot-weekly-on，
按 ADBOT_WEEKLY_OFF 标签精确复原，含 ad set / campaign 层）。SG 不在此周期内。**
周三下午看到 MY 广告/ad set 被关是这个周期的正常现象——不要去「修」，也不要在周三下午
判读 MY 当日数据；scheduled 未来开跑的新建 campaign 若跨周三也会被扫、周四自动弹回。

## Key locations

- **Approved copy bank** (the 8 ads): Notion page **"SOOCHENG-Andromeda"**
  (`38a82b424496810f8df7c2debb7c410f`).
- **Content Pipeline DB:** Notion "Stock Bloom Content Pipeline Template".
- **Copy-gen prompt:** `prompts/caption_system.md` · **Audience truth:** `config/audience.md`.
- **Ops commands** (build / monitor / weekly): `skills/meta-ops/SKILL.md`.
