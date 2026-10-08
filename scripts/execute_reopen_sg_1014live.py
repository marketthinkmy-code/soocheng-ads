# -*- coding: utf-8 -*-
"""SG 开回 — 为 2026-10-14（三）直播补量。owner 2026-10-08 要先看方案，一句话才执行。

只开「干净 + 30 天 CPA 达标（或从未真正跑过的新位）」的位；每个载体开之前再扫一次它底下
的 ads，只要有任何一支命中禁跑名单且 ad 层仍是 ACTIVE，就跳过那个载体（不开），绝不靠记忆。
幂等：已经 ACTIVE 的跳过。CONFIRM=true 才写；默认 dry-run 只印计划。

计划（载体 id 来自 report_sg_carriers_1008 的实盘读取）：
  A  campaign ANDRO POOL 30+ | 0922       CBO RM100  — 6 支干净成交素材的 Andromeda 池（新位，只花过 RM120）
  B  campaign BROAD SG 25+ | 0910 重拍     ABO        — 重拍：Video 6：我跟你讲！  30d CPA 183（唯一活 adset RM50）
  C  campaign 🌟 PURCHASE LAL 5% | 1-1-4  CBO RM70   — 🌟 video 5：盖电脑，喂！    30d CPA 654
  D  adset+ad  GOLF PICKLEBALL 30-55 | 0914 RM100     — HOOK：Video 5：盖电脑，喂！ 30d CPA 660 · CPL 83
  E (可选, BUMP_0911) adset «Broad SG 30+» RM50→RM100 — HOOK：Video 12：不选 forex 不选黄金 30d CPA 240，
     它旁边那个 RM100 adset 只剩被禁的 炒过那么多（已关），钱卡在空壳上。
  ── 60 天 CPA 标准才达标的位（owner 2026-10-08「以 60 天的 CPA 为标准再建议一次」，INCLUDE_60D）──
  F  campaign LUXURY GOODS | 1-1-3 CBO RM120 + ad video 1：用我的方法   60d CPA 487（30d 无单）
  G  ad 🌟 Video 2：市场不考你的英文 @ 🌟 PURCHASE LAL 5%（同 C 的 CBO，不加钱） 60d CPA 244

开关是常量（ops workflow 只传 CONFIRM）：改下面两行再 dispatch。
"""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
INCLUDE_60D = True      # owner 2026-10-08: judge by 60-day CPA -> F + G join the plan
BUMP_0911 = False       # optional E; flip to True only on the owner's word

CAMPAIGNS_ON = [
    ("A", "120249526319970521", "[SG] STOCKBLOOM | ANDRO POOL 30+ | 0922"),
    ("B", "120249341323780521", "[SG] STOCKBLOOM | BROAD SG 25+ | 0910 重拍"),
    ("C", "120248816613950521", "🌟 [SG] STOCKBLOOM | PURCHASE LAL 5% | 1-1-4"),
]
ADSETS_ON = [
    ("D", "120249392120610521", "Golf Pickleball SG 30-55 RM100 (HOOK V5 盖电脑)"),
]
ADS_ON = [
    ("D", "120249392121450521", "HOOK：Video 5：盖电脑，喂！ @ GOLF 30-55"),
]
if INCLUDE_60D:
    CAMPAIGNS_ON.append(("F", "120248256443280521", "[SG] STOCKBLOOM | LUXURY GOODS | 1-1-3"))
    ADS_ON.append(("F", "120248256452030521", "video 1：用我的方法 @ LUXURY GOODS 1-1-3"))
    ADS_ON.append(("G", "120248835502570521", "🌟 Video 2：市场不考你的英文 @ 🌟 PURCHASE LAL 5%"))
BUMP = ("E", "120249390885590521", "Broad SG 30+ RM50 (不选 forex) -> RM100", 10000)


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    banned = s.compliance.banned_creatives
    g = graph_client(s)
    acct = s.meta.account_path

    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,adset_id,campaign_id", "limit": "500"})
    time.sleep(1.0)
    by_camp, by_aset, by_id = {}, {}, {}
    for a in ads:
        by_camp.setdefault(a.get("campaign_id"), []).append(a)
        by_aset.setdefault(a.get("adset_id"), []).append(a)
        by_id[a["id"]] = a

    def armed_banned(kids):
        return [a for a in kids
                if compliance.is_banned(a.get("name") or "", banned) and a.get("status") == "ACTIVE"]

    def clean_live(kids):
        return [a for a in kids
                if not compliance.is_banned(a.get("name") or "", banned) and a.get("status") == "ACTIVE"]

    def info(path, fields):
        return g._request("GET", path, params={"fields": fields})

    plan, blocked = [], []

    for tag, cid, label in CAMPAIGNS_ON:
        c = info(cid, "id,name,status,daily_budget")
        kids = by_camp.get(cid, [])
        bad = armed_banned(kids)
        good = clean_live(kids)
        if bad:
            blocked.append((tag, label, f"⛔ 底下还有 {len(bad)} 支禁跑素材 ad 层 ACTIVE：" +
                            " / ".join((a.get("name") or "")[:24] for a in bad)))
            continue
        opening = {adid for _t, adid, _l in ADS_ON}
        good = good or [a for a in kids if a["id"] in opening]   # opened earlier in this same run
        if not good:
            blocked.append((tag, label, "没有任何干净 ad 是 ACTIVE——开了也烧不了钱，先开 ad"))
            continue
        if c.get("status") == "ACTIVE":
            plan.append((tag, "campaign", cid, label, "＝ 已经 ACTIVE（跳过）", None))
        else:
            plan.append((tag, "campaign", cid, label,
                         f"开 campaign → 会跑：{' / '.join((a.get('name') or '')[:26] for a in good)}", "ACTIVE"))
        time.sleep(0.6)

    for tag, aid, label in ADSETS_ON:
        x = info(aid, "id,name,status,daily_budget,campaign_id")
        bad = armed_banned(by_aset.get(aid, []))
        if bad:
            blocked.append((tag, label, "⛔ adset 里有禁跑素材 ad 层 ACTIVE"))
            continue
        if x.get("status") == "ACTIVE":
            plan.append((tag, "adset", aid, label, "＝ 已经 ACTIVE（跳过）", None))
        else:
            plan.append((tag, "adset", aid, label, "开 adset", "ACTIVE"))
        time.sleep(0.6)

    for tag, adid, label in ADS_ON:
        a = by_id.get(adid) or info(adid, "id,name,status")
        if compliance.is_banned(a.get("name") or "", banned):
            blocked.append((tag, label, "⛔ 这支本身在禁跑名单上！"))
            continue
        if a.get("status") == "ACTIVE":
            plan.append((tag, "ad", adid, label, "＝ 已经 ACTIVE（跳过）", None))
        else:
            plan.append((tag, "ad", adid, label, "开 ad", "ACTIVE"))

    if BUMP_0911:
        tag, aid, label, cents = BUMP
        x = info(aid, "id,name,status,daily_budget")
        cur = int(x.get("daily_budget") or 0)
        bad = armed_banned(by_aset.get(aid, []))
        if bad:
            blocked.append((tag, label, "⛔ adset 里有禁跑素材 ad 层 ACTIVE"))
        elif cur >= cents:
            plan.append((tag, "budget", aid, label, f"＝ 已是 RM{cur/100:.0f}（跳过）", None))
        else:
            plan.append((tag, "budget", aid, label, f"RM{cur/100:.0f} → RM{cents/100:.0f}", cents))

    print("═══ 计划 ═══")
    for tag, kind, oid, label, what, _ in plan:
        print(f"  [{tag}] {kind:<8} «{label[:48]}»  {what}")
    if blocked:
        print("═══ 不动（安全闸挡下）═══")
        for tag, label, why in blocked:
            print(f"  [{tag}] «{label[:48]}»  {why}")

    todo = [p for p in plan if p[5] is not None]
    if not todo:
        print("\n没有要写的。")
    elif not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才会执行以上 {len(todo)} 个动作。")
    else:
        ok = fail = 0
        # 先开 ad / adset，再开 campaign：campaign 一开就有干净 ad 能跑，不出现空壳
        order = {"ad": 0, "adset": 1, "campaign": 2, "budget": 3}
        for tag, kind, oid, label, what, val in sorted(todo, key=lambda p: order[p[1]]):
            try:
                if kind == "budget":
                    g.update_daily_budget(oid, val)
                else:
                    g.update_status(oid, val)
                ok += 1
                print(f"  ✅ [{tag}] {kind} «{label[:44]}» {what}")
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ [{tag}] {kind} «{label[:44]}»: {str(exc)[:120]}")
            time.sleep(0.8)
        print(f"\n执行 {ok} 个，失败 {fail} 个。")
        time.sleep(3)
        again = g._get_all(acct + "/ads", {
            "fields": "id,name,status,effective_status", "limit": "500"})
        live = [a for a in again if a.get("effective_status") == "ACTIVE"]
        bad = [a for a in live if compliance.is_banned(a.get("name") or "", banned)]
        print(f"复查：SG 现在在跑 {len(live)} 支；其中禁跑素材 {len(bad)} 支"
              + ("" if not bad else " ← 立刻停！"))
        for a in live:
            print(f"      {'⛔' if a in bad else '  '} «{(a.get('name') or '')[:44]}»")
    print("REOPEN 1014LIVE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
