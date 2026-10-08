# -*- coding: utf-8 -*-
"""SG 禁跑素材「拆引信」— 把禁跑名单上的每一支 ad 在 **ad 层** 关掉。

为什么必须在开回之前做（owner 2026-10-08 要为 14/10 直播开回 SG 广告）：
2026-09-23 那次只删掉「自身审核状态 = 被拒」的 9 支；名单上其余的母带副本还留在账户里，
而且很多是 **ad 层 ACTIVE、只被上层 campaign/adset 压住**。一旦有人在 Ads Manager
把 campaign 开回去（今天 10:21 SGT 就有人在开），这些被 Meta 拒审过的素材会立刻开始投放
—— 这正是第二次封号的成因，也是第三次封号最快的路。

本脚本只做一件事：把 ad 层 status 设成 PAUSED（可逆、不删）。
  · 不动任何干净素材，不动预算，不开任何东西。
  · 命中判定只走 adbot.compliance.is_banned（子串，忽略 🌟/HOOK：/重拍：/拼接：）。
CONFIRM=true 才写；默认 dry-run。读表部分永远执行。"""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
MAX_PAUSE = 70          # blast guard: 名单上 SG 共 ~52 支，远超就停手


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    banned = s.compliance.banned_creatives
    g = graph_client(s)
    acct = s.meta.account_path
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    token = result_action_type(s.meta.conversion_event)

    # ── 读：近 14 天每日花费 + 报名（判断账户黑了多久、够不够跑完学习期）──
    d14 = today - dt.timedelta(days=14)
    import json as _json
    daily = g._get_all(acct + "/insights", {
        "level": "account", "fields": "spend,actions", "time_increment": 1,
        "time_range": _json.dumps({"since": d14.isoformat(), "until": today.isoformat()}),
        "limit": 500})
    print(f"═══ SG 近 14 天 每日花费 / 报名 ═══")
    for r in daily:
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        cpl = f"CPL {sp/rg:.0f}" if rg else ("0 reg" if sp else "—")
        bar = "█" * int(min(sp, 600) / 20)
        print(f"  {r.get('date_start')}  RM{sp:>7.0f}  报名 {rg:>4.0f}  {cpl:<10} {bar}")
    print()
    time.sleep(1.2)

    # ── 读：全账户 ads，挑出禁跑命中 ────────────────────────────────────────
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,"
                  "campaign{id,name,status},adset{id,name,status}", "limit": "500"})
    hits = []
    for a in ads:
        why = compliance.banned_reason(a.get("name") or "", banned)
        if why:
            hits.append((a, why))

    live_now = [h for h in hits if h[0].get("effective_status") == "ACTIVE"]
    armed = [h for h in hits if h[0].get("status") == "ACTIVE"
             and h[0].get("effective_status") != "ACTIVE"]
    already = [h for h in hits if h[0].get("status") != "ACTIVE"]

    print(f"═══ 禁跑命中：{len(hits)} 支 ═══")
    print(f"  🔥 现在正在投放（eff ACTIVE）：{len(live_now)} — 必须立刻停")
    for a, why in live_now:
        print(f"      «{(a.get('name') or '')[:38]}» @ «{((a.get('campaign') or {}).get('name') or '')[:40]}»"
              f" 「{why}」")
    print(f"  ⚠️  上了膛（ad 层 ACTIVE，被上层压住 — campaign 一开就跑）：{len(armed)}")
    for a, why in armed:
        print(f"      «{(a.get('name') or '')[:38]}» @ «{((a.get('campaign') or {}).get('name') or '')[:40]}»"
              f" [adset {((a.get('adset') or {}).get('status') or '?')}]「{why}」")
    print(f"  ✅ ad 层已经是 PAUSED/ARCHIVED：{len(already)}\n")

    todo = live_now + armed
    if not todo:
        print("没有要关的（禁跑素材在 ad 层都已经压住了）。")
    elif len(todo) > MAX_PAUSE:
        print(f"⛔ 命中 {len(todo)} 支 > 上限 {MAX_PAUSE}，不动手（怕匹配过宽）。先人工核对。")
        return
    elif not CONFIRM:
        print(f"DRY RUN — CONFIRM=true 才会把这 {len(todo)} 支在 ad 层关掉（不删，只 PAUSE）。")
    else:
        ok = fail = 0
        for a, why in todo:
            try:
                g.update_status(a["id"], "PAUSED")
                ok += 1
                print(f"  ⏸  已关 «{(a.get('name') or '')[:40]}»  「{why}」")
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ 关失败 «{(a.get('name') or '')[:40]}»: {str(exc)[:110]}")
            time.sleep(0.8)
        print(f"\n关掉 {ok} 支，失败 {fail} 支。")
        time.sleep(3)
        again = g._get_all(acct + "/ads", {
            "fields": "id,name,status,effective_status", "limit": "500"})
        rest = [a for a in again
                if compliance.is_banned(a.get("name") or "", banned)
                and a.get("status") == "ACTIVE"]
        print(f"复查：ad 层仍 ACTIVE 的禁跑素材 {len(rest)} 支"
              + ("" if not rest else " ← 还有残留！"))
        for a in rest:
            print(f"      «{(a.get('name') or '')[:40]}» [{a.get('effective_status')}]")

    print("\n（下一步建议，等 owner 一句话：把这些禁跑素材 DELETE 掉 —— 2026-07 取证结论是"
          "「被拒广告留在账户里本身就是风险」，PAUSE 只是拆引信，删掉才是清场。）")
    print("BAN NEUTRALIZE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
