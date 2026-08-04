# Routine 配置：STOCK BLOOM 广告日报（Martin 式 · 评估+自动执行版）

在 claude.ai Routines 建（最快 = duplicate「Martin 美国广告日报」再改）：

| 格子 | 填什么 |
|---|---|
| 名称 | STOCK BLOOM 广告日报 |
| Repositories | marketthinkmy-code/**soocheng-ads** |
| Repeats | Runs daily at **22:20 GMT+8**（22:09 GitHub 报告出来之后） |
| Connectors | **META**（必须）· Google Drive（可选，看成交表） |
| Instructions | 下面整段贴进去 |

## Instructions（整段复制）

```
每天帮我生成并执行 STOCK BLOOM（Soo Cheng）广告日报。
两个账户：MY act_759339046918885 · SG act_893025326577600。

步骤：
1. 读 GitHub repo marketthinkmy-code/soocheng-ads 的 issue「📊 Daily Ads Report」
   （label: daily-report）最新 comment（每晚 22:09 MYT 自动贴；确认是今天的）。
   里面有：本广告周 CPL、60 天 CPA（campaign 级）、monitor 关停动作。
   如果今晚 comment 还没出现：dispatch workflow adbot-ops.yml（branch main，
   inputs: script=daily_report.py, confirm=false），读 job log 拿同样内容。
2. 用 META 工具拉两个账户 last_3d 的 ad 层表现
   （effective_status / amount_spent / omni_complete_registration /
   cost_per_omni_complete_registration）。

评估 + 自动执行（我已授权，不用再问我）：
- 判定标准看真实付费 CPA（60 天，hard-stop RM1,200），不是报名 CPL。
- CPL 高但有真实成交的赢家 → 一律保留，绝不关。
- GitHub monitor 每小时已经自动关差的（CPL>50 + CPA 救援），routine 不重复关。
  只有发现「60 天 CPA 超 RM1,200、spend≥RM1,000、建立≥14 天、还在跑」
  而 monitor 没关的 → 才用 ads_update_entity 设 PAUSED，并在报告列出（名字+原因）。
- ⛔ video 12：炒过那么多，累而且不稳定 — 永远禁跑，不重开不重建。

然后整理简短中文报告发我，重点：
- 昨天有没有新成交？哪几条广告出的单？
- 8/4 重开的 8 条赢家有没有恢复花钱/出单：
  MY 你敢吗(BUSINESS OWNER)、你没有本钱(TRAVEL)、video 12 不选 forex(LUXURY RM100/day)
  SG freestyle 1(BROAD B)、盖电脑+你没有本钱(TRAVEL(2) RM130/day)、
  trading 早就不是这样了(GOLF RM130/day)、用我的方法(INVESTMENT)
- 新测试：BEER ALCOHOL / DAY TRADING / TRAVEL TOP3（7/30 建，8/13 前不判 CPA）
- MY TRAVEL 降到 RM70/day 之后的表现
- 我今天关了哪些、为什么；有没有「⚠️ Partial report」（Meta rate-limit）
- 最后一句话结论：要不要我做什么（没有就写「无需动作」）
铁律：只报事实和数字，报告里没有的不要编。用中文。不用发 email。
```

## 设计说明

- 22:20 读 22:09 的现成报告，不重复打 Meta API（rate-limit 友好）；
  fallback 才 dispatch adbot-ops（confirm=false 只读）。
- 关停权在 GitHub monitor（每小时 + CPA 救援）；routine 只补漏网的
  hard-stop，避免两套系统抢着关。
- 升级路线：scripts/reopen_review.py（per-ad CPA/ROAS 全表）合进 main 后，
  routine 可加一步 dispatch 它拿逐条广告的真实利润表。
