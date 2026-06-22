# Replicate this Meta-ads automation onto a new project

## ⚡ 简易版(推荐 — 方便团队复制)

**为什么够用:** 整套逻辑(CPL/CPA 护栏、排程、1-1-N build)都是这个 repo 里的**确定性代码**,
prompt 不需要描述行为,只需要叫 Claude「换项目参数」。

**前提(二选一):**
- (A) 新项目直接从这个 repo 复制开始(GitHub「Use this template」/ 复制 repo),代码已全在;**或**
- (B) 让新项目的 Claude Code session 能读到 `marketthinkmy-code/soocheng-ads`(把它加进 session 范围)。

**做法:** 在新项目的 Claude Code 里,贴下面这段 ⬇️

```
这个 repo 是一套 Meta 广告自动化(adbot):自动建 1-1-N CBO 广告、每小时按 CPL+CPA 自动暂停亏的广告、
每周三 15:00 全停 / 周四 00:00 全开、每晚出报告、自动生成新创意点子,全部用 GitHub Actions 排程。
我要为一个新项目跑「一模一样」的自动化。

请保持所有代码、护栏逻辑、cron 排程原封不动,只换项目专属的设定。
一个一个问我所有会不一样的值:Meta 广告账户 / Page / Pixel、目标 + 转化事件、每日预算 + 货币、
国家 / 年龄 / 语言、落地页网址、命名前缀、Google Drive 素材文件夹、用来算 CPA 的付费名单 Sheet、
CPL 和 CPA 的阈值、时区。问完后更新 config/config.yaml、config/audience.md、prompts/caption_system.md,
并告诉我要设哪些 GitHub secrets。不确定就问,不要乱假设。

全程先保持 PAUSED;上线前先跑 python -m adbot doctor、离线测试、再 sync --dry-run 和 build --dry-run,
把结果给我看,我确认了才真正上线。
```

> 提示:若是品牌全新、又拿不到模板 repo,才需要下面的「完整版」(它把全部规格内嵌进 prompt,能从零重建)。

---

## 📋 完整版(从零重建、读不到模板 repo 时才需要)

> 把 `adbot` 这整套自动化(1-1-N 建构 + CPL/CPA 护栏 + 每周 OFF/ON + 每日报告 + 创意情报)
> 原封不动搬到另一个项目(例:马丁 Martin 的新课程/品牌)。
>
> **怎么用 / How to use**
> 1. 在新项目的 git repo 里打开 Claude Code(web / app 都行)。
> 2. 先填好下面 **PROJECT INTAKE** 区块的每一项(把 `<< ... >>` 换成真实值)。
> 3. 把 **整个 “MASTER PROMPT” 区段**(从 `===== MASTER PROMPT START =====` 到 END)连同你填好的 INTAKE 一起贴给 Claude Code。
> 4. Claude 会先 `--dry-run`,确认无误后才真正建立 + 上线。钱相关的动作都需要你点头。
>
> **最可靠的路径 / Fastest, most faithful path:** 这套系统已经在 `marketthinkmy-code/soocheng-ads`
> 跑得好好的。MTC 同时拥有那个 repo,所以最稳的做法是把它当**模板**:让 Claude 把 `adbot` 包和
> `.github/workflows/` **逐字复制**过来,只改 INTAKE 里列的那些项。下面的 prompt 已经这样写了——
> 即使新环境读不到模板 repo,prompt 里也带了完整规格,能从零重建出**行为一致**的系统。

---

```
===== MASTER PROMPT START =====

ROLE
You are setting up a hands-off Meta (Facebook/Instagram) ads automation for a new
project, run in the cloud and monitored from the Claude mobile app. Reproduce — exactly —
the proven system that already runs in the repository `marketthinkmy-code/soocheng-ads`
(the "adbot" Python package + GitHub Actions schedule + skills + prompts). Change ONLY the
per-project values supplied in PROJECT INTAKE below. Do not redesign the architecture, the
guardrail math, or the schedule.

WHY IT IS BUILT THIS WAY (keep these invariants)
- A committed Python package (`adbot`) does all the work through the OFFICIAL Meta Marketing
  (Graph) API + Google APIs (Drive/Docs/Sheets) + the Anthropic API for copy/intel. This is
  deliberate: an MCP connector cannot upload videos/images or build static carousels, and the
  money-touching guardrails (CPL/CPA pause, weekly OFF/ON) must be DETERMINISTIC code — never
  an LLM deciding per run.
- GitHub Actions is the cloud scheduler and the mobile-visible run log. Each scheduled job runs
  ONE committed command (`python -m adbot <cmd>` or `python scripts/<x>.py`) and reports a final
  one-line `SUMMARY:`.
- Everything is created PAUSED; nothing goes live without an explicit activation step.
- Pure decision functions (CPL/CPA) are unit-tested offline (no network).

REFERENCE IMPLEMENTATION (source of truth)
If you can read `marketthinkmy-code/soocheng-ads`, COPY these verbatim into this repo, then
re-parameterize via INTAKE:
  src/adbot/**            (clients/graph.py, drive.py, gdoc.py, sheets.py, llm.py;
                           drive_sync.py, media.py, creative_groups.py, captions.py,
                           build_1_1_10.py, monitor_cpl.py, cpa.py, weekly_off.py,
                           weekly_on.py, creative_intel.py, docwriter.py, settings.py,
                           state.py, logging.py, commands/*, __main__.py)
  scripts/**              (daily_report.py, cpa_report.py, cpa_preview.py,
                           cpa_decision_preview.py, adset_roas.py, read_adset.py)
  .github/workflows/**    (adbot-monitor, adbot-weekly-off, adbot-weekly-on,
                           adbot-daily-report, adbot-cpa-report, adbot-cpa-preview,
                           adbot-cpa-decision-preview, adbot-adset-roas, adbot-read-adset,
                           adbot-diag)
  prompts/**, skills/**, tests/**, pyproject.toml, setup.sh, .env.example, .gitignore
Then change ONLY: config/config.yaml, config/audience.md, prompts/caption_system.md
(+ prompts/intel_system.md) per INTAKE, plus workflow display names. Keep the cron lines and
the ADBOT_ROOT/ADBOT_CONFIG env wiring exactly.
If you CANNOT read the reference repo, build the system from the SPEC below; it is complete.

────────────────────────────────────────────────────────────────────────
PROJECT INTAKE  —  fill every << >> before running. This is the only thing that changes.
────────────────────────────────────────────────────────────────────────
Product / brand:        << e.g. Martin 老师 XYZ Course — one-line description >>
Primary language/voice: << e.g. ZH-CN (马华口语 + 英文术语) / EN / BM >>

Meta account & assets
  ad_account_id:        << act_XXXXXXXXXXXXXXX >>      (keep the act_ prefix)
  page_id:              << FB Page id the ads run under >>
  instagram_user_id:    << IG business account id, or null to omit >>
  pixel_id:             << pixel / dataset id for conversion tracking >>
  special_ad_category:  << [] OR ["FINANCIAL_PRODUCTS_SERVICES"] etc. — CONFIRM region rule;
                           a special category can force broad targeting and override age >>

Objective & conversion
  objective:            << OUTCOME_SALES | OUTCOME_LEADS | OUTCOME_TRAFFIC | ... >>
  optimization_goal:    << OFFSITE_CONVERSIONS | LEAD_GENERATION | LINK_CLICKS | ... >>
  conversion_event:     << e.g. COMPLETE_REGISTRATION | LEAD | PURCHASE >>
  lead_destination:     << WEBSITE | INSTANT_FORM | MESSENGER | WHATSAPP >>
  link_url:             << landing/lead URL >>
  conversion_domain:    << root domain Meta verifies for website-conversion ads >>
  call_to_action:       << LEARN_MORE | SIGN_UP | GET_OFFER | SUBSCRIBE | ... >>

Budget (CBO)
  daily_budget:         << e.g. 250 >>   currency: << MYR >>
  adset_min_spend:      << e.g. 50  (per-ad-set daily floor; redundant with a single ad set) >>

Targeting
  countries:            << ["MY"] >>
  age_min / age_max:    << 25 / 65 >>
  advantage_audience:   << 1 = Broad/Advantage+ ON  |  0 = hard age cap >>
  locales:              << e.g. [1004] = Chinese (All); [] for none >>

Build
  creatives_per_adset:  << N, e.g. 10 (the "10" in 1-1-N; 5 is fine for a focused test) >>
  activate_after_build: << true to auto-activate at the CBO budget after a verified build >>

Naming & scoping
  prefix:               << e.g. MARTINXYZ  — prefixes every entity this bot creates >>
  weekly_off_label:     << e.g. ADBOT_WEEKLY_OFF — Meta ad label marking the Wed-paused set >>

Creatives source (Google Drive)
  creatives_folder_id:  << Drive folder with videos / images / carousel subfolders >>
  carousel_marker:      << substring marking a carousel subfolder, e.g. "carousel" >>
  script_sidecar_ext:   << ".txt"  — per-asset brief: same basename, this extension >>

Google Docs (logs; blank = auto-create)
  caption_log_doc_id:   << "" >>
  idea_backlog_doc_id:  << "" >>

CPL guardrail (cost per optimized event)
  cpl_threshold:        << 40   — pause an ad above this CPL >>
  cpl_min_spend:        << 80   — only judge an ad after it spends >= this (fairness gate) >>
  cpl_lookback:         << week_thu (week-to-date from Thursday) | a Meta preset e.g. last_3d >>
  pause_zero_lead:      << true — spent >= min_spend with 0 results -> pause >>
  cpl_hold:             << [] or ["<ad-name substring to temporarily exempt from CPL pause>"] >>

CPA gate (real paid sales — optional but recommended)
  cpa_enabled:          << true | false >>
  spreadsheet_id:       << Google Sheet id of the paid-sales list >>
  sales_tab:            << tab name, e.g. "Paid Student List" (one paid sale per row + UTM + date) >>
  price:                << default unit price, e.g. 2399 (sheet Amount column overrides per row) >>
  cpa_target:           << 720   (primary target) >>
  cpa_healthy_max:      << 800   (end of healthy range; NOT a pause line) >>
  cpa_max_acceptable:   << 960   (pause candidate after diagnosis) >>
  cpa_hard_stop:        << 1200  (auto-pause line, with real sales, once matured) >>
  conversion_days:      << 14    (don't judge CPA until a sale/registration is this old) >>
  cpa_min_spend:        << 1000  (need >= this spend before a CPA verdict is fair) >>

Schedule
  timezone:             << Asia/Kuala_Lumpur (GMT+8, no DST) >>
  weekly_off:           << WED 15:00  — pause ALL >>
  weekly_on:            << THU 00:00  — resume what Wed paused >>
  monitor_interval:     << hourly (impl: a few times/hour, off the :00 boundary) >>
  daily_report_time:    << 22:00 >>

Secrets (set as GitHub repo secrets / environment variables — NEVER commit real values)
  META_SYSTEM_USER_TOKEN  (scopes: ads_management, ads_read, business_management,
                           pages_read_engagement  [+ leads_retrieval if pulling leads])
  META_APP_SECRET         (optional; signs Graph calls with appsecret_proof)
  GOOGLE_SERVICE_ACCOUNT_JSON_B64  (base64 of the SA key; enable Drive+Docs+Sheets APIs and
                           SHARE the Drive folder + both Docs + the Sheet with the SA email)
  ANTHROPIC_API_KEY
Network allowlist for the runner/environment:
  graph.facebook.com, www.googleapis.com, api.anthropic.com

────────────────────────────────────────────────────────────────────────
BEHAVIOR SPEC  —  reproduce exactly (these are the invariants, not the variables)
────────────────────────────────────────────────────────────────────────

FILE LAYOUT
  src/adbot/  clients/ (graph.py Meta · drive.py · gdoc.py · sheets.py · llm.py Claude)
              drive_sync.py  media.py  creative_groups.py  captions.py
              build_1_1_10.py  monitor_cpl.py  cpa.py  weekly_off.py  weekly_on.py
              creative_intel.py  docwriter.py  settings.py  state.py  logging.py
              commands/ (doctor, sync, build, monitor, weekly_off, weekly_on, intel)  __main__.py
  config/   config.yaml (all INTAKE values)   audience.md (the precise-audience framework)
  prompts/  caption_system.md   intel_system.md
  skills/   meta-ops   creative-intel
  scripts/  daily_report.py  cpa_report.py  cpa_preview.py  cpa_decision_preview.py
            adset_roas.py  read_adset.py
  state/    json ledgers (entities, media cache, pause log) — cache + audit
  tests/    offline unit tests for the pure decision functions

COMMANDS (each is one CLI entry; routines run exactly one)
  python -m adbot doctor      Preflight: token, account, page, pixel, Drive, Docs, audience.
  python -m adbot sync        Download Drive creatives, upload to Meta, group into N units.
  python -m adbot build       Create (+ optionally activate) the 1-1-N + write the caption log.
  python -m adbot monitor     Evaluate every ACTIVE ad and PAUSE losers (CPL folded with CPA).
  python -m adbot weekly_off  Pause ALL active ads and label them.
  python -m adbot weekly_on   Resume exactly the labeled set; clear the label.
  python -m adbot intel       Read live creatives -> 6-10 new content ideas -> Google Doc.
  (--dry-run on every command except doctor previews without writing.)
  scripts/: daily_report (nightly issue), cpa_report/cpa_preview/cpa_decision_preview (CPA joins),
            adset_roas, read_adset (read-only analysis helpers).

BUILD — the 1-1-N structure (build_1_1_10.py). Everything PAUSED first.
  Campaign (CBO):  objective=<objective>, buying_type=AUCTION, status=PAUSED,
                   daily_budget=<daily_budget in minor units/cents>,
                   bid_strategy=LOWEST_COST_WITHOUT_CAP, special_ad_categories=<...>.
  Ad set (broad):  optimization_goal=<optimization_goal>, billing_event=IMPRESSIONS,
                   promoted_object={pixel_id, custom_event_type=<conversion_event>},
                   targeting={countries, age_min, age_max, advantage/targeting_automation,
                   locales}, status=PAUSED. (Optional start_time to schedule first delivery.)
  Ads (N):         one creative per grouped unit:
                   - video      -> object_story_spec.video_data {video_id, title=headline,
                                   message=caption, image_url=thumbnail, call_to_action}
                   - single img -> link_data {link, image_hash, message, name=headline, CTA}
                   - carousel   -> link_data.child_attachments[] {link, image_hash, name, desc, CTA},
                                   multi_share_optimized=true, multi_share_end_card=true
                   attach instagram_user_id if set; append url_tags (UTM) and conversion_domain.
                   Name every entity with "<prefix> | ...".
  Resumable:  persist a state ledger after EVERY created entity (campaign/adset/each ad) so a
              mid-build failure resumes without duplicating a campaign.
  Activation: only if activate_after_build -> set campaign, then ad set, then each ad ACTIVE.

CPL GUARDRAIL (monitor_cpl.py) — pure function `decide(spend, results, kpi)`, unit-tested.
  Scope: WHOLE ACCOUNT, every campaign, but evaluate ONLY ads whose ad set's
         promoted_object.custom_event_type == <conversion_event> (so a campaign chasing a
         different objective can never be paused on a CPL it wasn't trying to produce).
         ACTIVE ads only. Judge ONE ad at a time (pause a single bad creative, not its ad set).
  Window: cpl_lookback. "week_thu" = week-to-date from the most recent Thursday (the weekly
          reset day) -> time_range {since: last Thursday, until: today (MYT)}.
  Results: count ONLY the exact action_type `offsite_conversion.fb_pixel_<event lowercased>`
           (Meta reports the same conversion under several overlapping buckets — substring-summing
           multiplies the real count).
  Decision per ad:
    spend < cpl_min_spend                       -> KEEP   (insufficient_spend)
    results == 0 and pause_zero_lead            -> PAUSE  (zero_results), CPL = ∞
    cpl = spend/results;  cpl > cpl_threshold   -> PAUSE  (over_threshold)
    else                                        -> KEEP   (within_threshold)
  Holds: an ad whose name contains any cpl_hold substring is EXEMPT from CPL pause (NOT from CPA).
  monitor only ever PAUSES; it never re-activates. Append every pause to a pause-log ledger.

CPA FOLD (cpa.py `combined_decision`) — real paid sales override CPL. Optional (cpa_enabled).
  Context: read <sales_tab> from <spreadsheet_id>; parse rows by HEADER NAME (robust to column
           reorder): date, utm_campaign, utm_adset, utm_ad, amount. Normalize UTM values; count
           sales in a 60-day window; join 60-day Meta spend per ad_id. CPA = spend / sales.
           If the Sheet or Meta context is unavailable, DEGRADE to CPL-only (never crash).
  matured = ad_age >= conversion_days AND 60-day spend >= cpa_min_spend.
  Rules (fold into the CPL decision):
    1) HARD STOP (auto-pause): matched_sales > 0 AND finite CPA > cpa_hard_stop AND matured.
    2) RESCUE (keep despite a CPL pause): CPL-would-pause AND matched_sales > 0 AND finite
       CPA <= cpa_hard_stop  (real profitable sales protect a high-CPL ad). Rescue ignores age.
    3) Otherwise the CPL decision stands.
    Zero matched sales NEVER auto-pauses on CPA (could be an attribution gap, not true waste).
  Reporting tiers: <= healthy_max KEEP · <= max_acceptable MONITOR · <= hard_stop PAUSE_CANDIDATE
                   · > hard_stop HARD_STOP.

WEEKLY OFF / ON (weekly_off.py / weekly_on.py) — coordinated by the Meta ad label, not state.
  weekly_off (<weekly_off> local): pause every ACTIVE ad in the account, tag each with
             <weekly_off_label>.  weekly_on (<weekly_on> local): resume exactly the ads carrying
             that label, then clear it. Label coordination means it works across fresh cloud
             clones with no shared state file. Ads paused by the monitor or by a human are NOT
             tagged, so they stay off. Re-running either side is a no-op.

REPORTING
  daily_report.py (<daily_report_time> local): read-only whole-account performance summary with
     explicit time windows; posted as a comment on a GitHub issue labeled `daily-report` (creates
     the issue once) so the owner gets a notification nightly. CPA section flags only above the
     hard-stop line (less noise).
  cpa_report.py (manual): join Meta campaign spend to the paid-sales list -> CPA per campaign
     (30d / 60d / lifetime) + waste signals. No writes, no pauses.

CREATIVE COPY & COMPLIANCE
  captions.py: for each unit, call the model with prompts/caption_system.md + config/audience.md
     -> {caption, headline, encoded_audience_signals, carousel_card_texts}. Write each to the
     caption-log Google Doc for the operator to audit.
  ANDROMEDA PRINCIPLE: the ad set is BROAD/Advantage+ (no narrow saved audience). Meta infers who
     to show the ad to partly from the creative's own text, so the copy must ENCODE the audience
     framework's precise signals (situation/pain/desire/life-stage, in the buyer's own language)
     so the right people self-select in and the wrong people scroll past.
  COMPLIANCE HARD RULES (especially financial/health/"make money" verticals): never write or imply
     guaranteed/expected/"sure" profit or income, specific return figures as promises, "get rich
     quick", "risk-free", "no-loss", "100%", or unrealistic results. Prefer education-framed
     language and light risk awareness. Adapt prompts/caption_system.md + config/audience.md to
     THIS product; do not reuse the previous product's persona verbatim.
  intel (creative_intel.py): read each managed ad's spend/leads/CPL, ask the model
     (prompts/intel_system.md + audience.md) for 6-10 new ideas, append non-duplicate ones (de-dup
     by title) to the idea-backlog Doc with a date stamp + a generation-ready prompt per idea.

SCHEDULE (GitHub Actions cron is UTC). The values below assume the project timezone is GMT+8
(no DST). If <timezone> differs, recompute: UTC = local_time − utc_offset (watch for day rollover),
and verify after creating. Stagger off the ":00" boundary (GitHub drops top-of-hour runs under
load) and add backup ticks for the costly-to-miss jobs.
  CPL+CPA monitor : cron "7,27,47 * * * *"                    (~every 20 min; repeats are no-ops)
  weekly OFF      : cron "9 7 * * 3"  + backup "9 8 * * 3"    (Wed 15:09 / 16:09 MYT)
  weekly ON       : cron "9 16 * * 3" + "9 17 * * 3" + "9 18 * * 3"  (Thu 00:09 / 01:09 / 02:09 MYT)
  daily report    : cron "9 14 * * *"                          (22:09 MYT)
  Every workflow sets env: ADBOT_ROOT=${{ github.workspace }},
  ADBOT_CONFIG=${{ github.workspace }}/config/config.yaml, plus the secrets above
  (pip install . is non-editable, so settings must be pointed at the checkout, not site-packages).

SAFETY RULES (non-negotiable)
  - Everything is created PAUSED. Activation happens only via activate_after_build or a human.
  - monitor only PAUSES; never re-activates. Re-activation is weekly_on or a human.
  - Do NOT pause/resume managed ads by hand mid weekly-cycle (it desyncs the label set).
  - If a command errors, report the error VERBATIM and STOP. Do not improvise Meta changes.
  - Confirm with the operator before the first live `build` (real money starts spending).

ACCEPTANCE / VERIFICATION (run in order; do not go live until all pass)
  ./setup.sh                       # venv + install + offline tests
  python -m adbot doctor           # every check must pass (token/account/page/pixel/Drive/Docs/audience)
  python -m pytest -q              # offline unit tests for decide()/combined_decision()/cpa parsing
  python -m adbot sync  --dry-run  # list + group assets, no upload
  python -m adbot build --dry-run  # print exact campaign/adset/creative payloads, create nothing
  # then, with operator confirmation:
  python -m adbot sync  &&  python -m adbot build
  # finally create the GitHub Actions workflows + repo secrets + network allowlist and verify a
  # manual workflow_dispatch run of the monitor (use its dry_run input first).

WHAT TO REPORT BACK
  After each step, relay the final `SUMMARY:` line (counts + any pauses/resumes/activations) —
  that is what the operator reads in the Claude mobile app. Surface the per-project values you
  used so they can be audited. Never print secret values.

===== MASTER PROMPT END =====
```

---

## Notes for the operator (you, not the prompt)

- **This file lives in `soocheng-ads` as a reusable template.** For a brand-new project, copy the
  `===== MASTER PROMPT =====` block out, fill the INTAKE, and paste it into the new repo's Claude
  Code session. Nothing here is specific to one product except the example default numbers.
- **Same Meta account vs. new account?** If Martin's project runs under a *different* ad account /
  page / pixel, set those in INTAKE. If it shares the account with another brand, the `prefix` and
  the whole-account-scoped monitor/weekly jobs will see *both* — keep the prefix distinct and be
  aware weekly OFF/ON pauses the *entire account*, not just one prefix (that is the current,
  intended design for soocheng-ads; flag it if Martin needs prefix-scoped weekly control instead).
- **CPA join needs a real sheet.** The CPA gate only works if there is a paid-sales Google Sheet
  with per-row UTM (campaign / ad set / ad) + date + amount, shared with the service account. No
  sheet yet → set `cpa_enabled: false` and run CPL-only until the sheet exists.
- **Timezone.** All example crons are GMT+8. If Martin's audience/reporting is another timezone,
  recompute the UTC crons (the prompt says how) and re-verify.
- **Scaling play (optional).** Beyond the initial 1-1-N, the same toolkit supports "read the best
  ad set → duplicate it into a fresh CBO campaign" for scaling a proven winner; ask for it when the
  account has enough data.
