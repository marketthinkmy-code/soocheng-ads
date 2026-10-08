# -*- coding: utf-8 -*-
"""被拒应对（CLAUDE.md ⛔ 硬规则）：一支素材在任何账户被 Meta 拒审 = 母带永久禁跑，所有账户、所有副本。

对 REJECTED 里每个母带关键字（compliance 子串匹配）：
  · MY 5.0 + SG：所有命中的 ad → ad 层 PAUSED + 改名「🚫 」前缀（硬规则，自动）；
  · MY 5.0：DELETE_MY5=True 时把命中的 ad 删掉（被拒广告留在账户里本身就是风险；不可逆，等 owner 一句「删」）。
不 resubmit、不申诉。CONFIRM=true 才写；默认 dry-run 列出会动的每一支。
（config 的 banned_creatives 另外走 PR 进 main，让 monitor 也认得。）"""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
REJECTED = []            # 填母带关键字，例如 ["盖电脑"]；空 = 什么都不做
DELETE_MY5 = False       # owner 一句「删」后改 True
ACCOUNTS = [("MY5", "config.my5.yaml"), ("SG", "config.sg.yaml")]


def main() -> None:
    if not REJECTED:
        print("REJECTED 为空——没有要处理的。"); return
    for label, cfg in ACCOUNTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        ads = g._get_all(acct + "/ads", {
            "fields": "id,name,status,effective_status,campaign{name}", "limit": "500"})
        hits = [a for a in ads if compliance.banned_reason(a.get("name") or "", REJECTED)]
        print(f"═══ [{label}] 命中 {len(hits)} 支 ═══")
        for a in hits:
            print(f"  [{a.get('status')}/{a.get('effective_status')}] «{(a.get('name') or '')[:40]}»"
                  f" @ «{((a.get('campaign') or {}).get('name') or '')[:40]}»")
        if not CONFIRM:
            print(f"  DRY RUN — 会：ad 层 PAUSED + 🚫 改名" + ("，MY5 再 DELETE" if label == "MY5" and DELETE_MY5 else "") + "\n")
            continue
        ok = fail = 0
        for a in hits:
            try:
                if a.get("status") != "PAUSED":
                    g.update_status(a["id"], "PAUSED")
                nm = a.get("name") or ""
                if compliance.BAN_MARK not in nm:
                    g._request("POST", a["id"], data={"name": f"{compliance.BAN_MARK} {nm}"})
                if label == "MY5" and DELETE_MY5:
                    g._request("DELETE", a["id"])
                    print(f"  🗑 删了 «{nm[:40]}»")
                else:
                    print(f"  ⏸🚫 «{nm[:40]}»")
                ok += 1
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ «{(a.get('name') or '')[:40]}»: {str(exc)[:140]}")
            time.sleep(1.0)
        time.sleep(3)
        again = g._get_all(acct + "/ads", {"fields": "id,name,status,effective_status", "limit": "500"})
        live = [a for a in again if compliance.is_banned(a.get("name") or "", REJECTED)
                and a.get("effective_status") == "ACTIVE"]
        left = [a for a in again if compliance.is_banned(a.get("name") or "", REJECTED)]
        print(f"  做了 {ok}，失败 {fail}；复查：仍在跑 {len(live)} 支，账户里还剩 {len(left)} 支\n")
    print("REJECT RESPONSE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
