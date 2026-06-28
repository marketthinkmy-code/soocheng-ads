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

---

## Proven angles (old account purchase data, Apr 1 – Jun 23 2026 — buyers, not just CPL)

Ranked by real course buyers / conversion (use this order when prioritising):

1. **不是怕交易** (35 buyers, RM148k — top volume) · 2. **我跟你讲** (25% conversion — most
efficient) · 3. **盖电脑·别盯盘** (11%) · 4. **不选 forex 不选黄金** · 5. **你敢吗** ·
6. **40 岁·收入单一** · 7. **FD·闲置资金** · 8. **怀疑者**.

- **Best-converting voice = personal, in-your-face direct address** (the「我跟你讲」voice).
- **Winning audiences (CPA/ROAS ~3x): Luxury Goods, Beer/Alcohol, Omakase/Wagyu** — affluent,
  mid-life, *already has capital*. Write to "make existing money work, principal untouched",
  not "escape poverty".
- **Avoid leading on** `不用看盘` / `街头突击采访` (cheap reach, weak conversion).
- ⚠️ Cheapest CPL ≠ best ad. `Travel` had the lowest CPL but the worst CPA — judge by
  purchases/ROAS, not CPL.

---

## Key locations

- **Approved copy bank** (the 8 ads): Notion page **"SOOCHENG-Andromeda"**
  (`38a82b424496810f8df7c2debb7c410f`).
- **Content Pipeline DB:** Notion "Stock Bloom Content Pipeline Template".
- **Copy-gen prompt:** `prompts/caption_system.md` · **Audience truth:** `config/audience.md`.
- **Ops commands** (build / monitor / weekly): `skills/meta-ops/SKILL.md`.
