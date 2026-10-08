# -*- coding: utf-8 -*-
"""给 SG 账户里每一支禁跑素材的 ad name 加上「🚫 」前缀（owner 2026-10-08）。

目的：人在 Ads Manager 一眼看到就知道不能开。只改名字，不动 status / 预算 / 创意
（名字不是审核字段，改名不会触发重审）。幂等：已含 🚫 的跳过。
命中判定 = adbot.compliance.banned_reason（与 monitor 同一道闸）。
CONFIRM=true 才写；默认 dry-run 只印对照表。MY 账户已被停用，不碰。"""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
MAX_RENAME = 70                      # SG 实盘 53 支；远超就停手


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    banned = s.compliance.banned_creatives
    g = graph_client(s)
    acct = s.meta.account_path
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,campaign{name}", "limit": "500"})

    todo, done = [], []
    for a in ads:
        nm = a.get("name") or ""
        why = compliance.banned_reason(nm, banned)
        if not why:
            continue
        (done if compliance.BAN_MARK in nm else todo).append((a, why))

    print(f"禁跑命中 {len(todo) + len(done)} 支：已带 🚫 {len(done)} · 要加 {len(todo)}\n")
    for a, why in todo:
        print(f"  «{(a.get('name') or '')[:40]}»  →  «🚫 {(a.get('name') or '')[:38]}»"
              f"   [{a.get('status')}] @ «{((a.get('campaign') or {}).get('name') or '')[:34]}»")
    if not todo:
        print("全部都已标记。")
    elif len(todo) > MAX_RENAME:
        print(f"⛔ {len(todo)} > 上限 {MAX_RENAME}，不动手。")
        return
    elif not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才会改这 {len(todo)} 个名字。")
    else:
        ok = fail = 0
        for a, why in todo:
            new = f"{compliance.BAN_MARK} {a.get('name') or ''}"
            try:
                g._request("POST", a["id"], data={"name": new})
                ok += 1
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ «{(a.get('name') or '')[:40]}»: {str(exc)[:120]}")
            time.sleep(0.7)
        print(f"\n改名 {ok} 支，失败 {fail} 支。")
        time.sleep(3)
        again = g._get_all(acct + "/ads", {"fields": "id,name,status", "limit": "500"})
        missing = [a for a in again
                   if compliance.banned_reason(a.get("name") or "", banned)
                   and compliance.BAN_MARK not in (a.get("name") or "")]
        live_banned = [a for a in again
                       if compliance.is_banned(a.get("name") or "", banned)
                       and a.get("status") == "ACTIVE"]
        print(f"复查：禁跑素材没带 🚫 的 {len(missing)} 支；ad 层仍 ACTIVE 的禁跑 {len(live_banned)} 支")
    print("MARK BANNED DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
