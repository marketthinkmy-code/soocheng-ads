# -*- coding: utf-8 -*-
"""Owner 2026-09-23「删」— DELETE the rejected ads sitting in the SG account.

Context: MY (MTC X SB 3.0) was disabled the same day (ADS_INTEGRITY_POLICY, the
second ban in this account family). SG is the only delivery asset left, and the
July forensics conclusion was that **rejected ads left in an account are
themselves a risk** — they should be deleted, not merely paused.

SCOPE — deliberately narrow, because delete is irreversible:
  ONLY ads whose own review state is rejected (issues_info present, or
  effective_status DISAPPROVED / *WITH_ISSUES). That is the 9 ads the 09-23
  forensics listed for SG.
  NOT every ad matching the permanent ban list — banned-but-approved copies
  (e.g. freestyle 1 @ 🌟BROAD B) are left alone for the monitor to PAUSE, which
  is reversible. SG only; the disabled MY account is not touched.

Safety: prints the exact roster first, aborts if the set is unexpectedly large,
CONFIRM-gated, and verifies each deletion afterwards."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
MAX_DELETE = 15          # blast guard: forensics found 9; abort if the set balloons
REJECTED_STATES = ("DISAPPROVED", "WITH_ISSUES", "ADSET_PAUSED_WITH_ISSUES",
                   "CAMPAIGN_PAUSED_WITH_ISSUES")


def main() -> None:
    mode = "APPLY — 永久删除" if CONFIRM else "DRY-RUN"
    print(f"SG 删除被拒广告（owner 2026-09-23「删」）— {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    info = g.get_object(acct, fields="name,account_status")
    print(f"账户 {info.get('name')} · account_status={info.get('account_status')} "
          f"(1=ACTIVE)\n")

    ads = g._get_all(
        f"{acct}/ads",
        {"fields": "id,name,effective_status,issues_info,campaign{name}", "limit": "500"})
    time.sleep(1.2)

    targets = []
    for a in ads:
        es = a.get("effective_status") or ""
        if es in REJECTED_STATES or (a.get("issues_info") or []):
            targets.append(a)

    print(f"── 被拒广告：{len(targets)} 支 ──")
    for a in targets:
        print(f"  ⛔ [{a.get('effective_status')}] «{(a.get('name') or '')[:34]}» @ "
              f"«{((a.get('campaign') or {}).get('name') or '')[:38]}»  id={a.get('id')}")
    print()

    if not targets:
        print("（没有被拒广告——无事可做）")
        return
    if len(targets) > MAX_DELETE:
        print(f"⛔ 中止：命中 {len(targets)} 支 > 安全上限 {MAX_DELETE}，不批量删。"
              f"请人工复核后再调整 MAX_DELETE。")
        return
    if not CONFIRM:
        print(f"[dry] would DELETE 上面 {len(targets)} 支（不可逆）。set confirm=true 才执行。")
        return

    deleted, failed = [], []
    for a in targets:
        try:
            g._request("DELETE", a["id"])
            deleted.append(a)
            print(f"  ✔ 已删 «{(a.get('name') or '')[:34]}»  id={a.get('id')}")
        except Exception as exc:  # noqa: BLE001
            failed.append((a, exc))
            print(f"  ⚠ 删除失败 «{(a.get('name') or '')[:34]}» — "
                  f"{type(exc).__name__}: {str(exc)[:120]}")
        time.sleep(PACE)

    print("\n── 复核（重新扫一次账户）──")
    again = g._get_all(
        f"{acct}/ads",
        {"fields": "id,name,effective_status,issues_info", "limit": "500"})
    left = [a for a in again
            if (a.get("effective_status") or "") in REJECTED_STATES or (a.get("issues_info") or [])]
    print(f"  删除 {len(deleted)} 支 · 失败 {len(failed)} 支 · 账户内剩余被拒广告：{len(left)} 支")
    for a in left:
        print(f"    还在: [{a.get('effective_status')}] «{(a.get('name') or '')[:34]}» id={a.get('id')}")
    print("\nDELETE REJECTED SG DONE")


if __name__ == "__main__":
    main()
