# Routine 配置：STOCK BLOOM 广告日报

把下面这份配置建成 claude.ai Routine（跟「Martin 美国广告日报」同款建法：
Routines → 新建，或直接对 Claude 说「照 soocheng-ads repo 里
config/routine_daily_report.md 建一个 routine」）。

- **名称**：STOCK BLOOM 广告日报
- **排程**：每天 22:20 MYT（cron `20 14 * * *`，UTC）— 排在 22:09 的
  GitHub 自动报告之后，直接读现成结果，不重复打 Meta API
- **环境**：soocheng-ads 的 Claude Code 环境（repo marketthinkmy-code/soocheng-ads）
- **通知**：push + email 打开（跟其他 routine 一致）

## Prompt（整段贴进 routine）

```
每天帮我生成 STOCK BLOOM（Soo Cheng）广告日报，直接在这个 session 里发我，不用另外发 email。

数据来源（按顺序）：
1. 首选：GitHub repo marketthinkmy-code/soocheng-ads 的 issue「📊 Daily Ads Report」
   （label: daily-report）— 每晚 22:09 MYT 自动贴当天报告 comment。读最新一条，
   确认是今天（MYT）的。
2. 如果今晚的 comment 还没出现：dispatch GitHub workflow adbot-ops.yml
   （repo marketthinkmy-code/soocheng-ads，branch main，
   inputs: script=daily_report.py, confirm=false），跑完用 list_workflow_jobs +
   get_job_logs 读 log 里的报告 Markdown。

拿到报告后整理成简短中文战报，重点：
- 本广告周（周四起算）blended CPL vs 上限 RM50，超标的 campaign 逐条列（⚠️）
- 近 60 天 CPA：blended vs hard-stop RM1,200，超标的列出来
- Monitor 今天关了哪些 / CPA 救回哪些 / 手动 hold 的
- 有没有「⚠️ Partial report」（Meta rate-limit）；有的话说明哪段缺数据
- 最后一行一句话结论：今天要不要我做什么（没有就写「无需动作」）

铁律：只报事实和数字，报告里没有的不要编。用中文。
```

## 为什么这样设计

- 22:09 的 GitHub Actions 报告照跑（issue + email 不动），Routine 只是把同一份
  数据换成手机推送 + session 里可追问的形式 — 两条通道互为备份。
- Routine 读 issue comment 而不是自己打 Meta API：零额外 rate-limit 压力
  （rate-limit 正是 PR #51 要修的问题）。
- fallback 走 adbot-ops.yml（confirm=false 只读），不用 adbot-daily-report.yml 的
  manual dispatch — 后者会往 issue 重复贴 comment、多发一封 email。
