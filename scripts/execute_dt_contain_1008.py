# -*- coding: utf-8 -*-
"""围堵 — MY 5.0 DAY TRADING（owner 2026-10-08「day trading 有 rejected」）。

取证（activity log）：我 06:53–07:00 建的 15 支 post 复用 ad 在 07:00–07:09 全部过审；07:08
Thelyin 在 Ads Manager 把 DAY TRADING 里 5 支 ad 的 creative 全换掉（新 creative id），5 支重进
审核；07:13 Meta 把换过的 «Video：不选 forex 不选黄金» 判 Not approved；07:09/07:15 她又把
ad set 年龄从 30-65 改成 25-65 + Advantage+ 打开、改名 28-65+、并开成 ACTIVE。

硬规则动作（可逆）：
  1. 被拒的那支 ad → PAUSED + 🚫 改名（被拒素材不投、不 resubmit；它现在 IN_PROCESS = 正在被重审）。
  2. DAY TRADING ad set → PAUSED：里面另外 4 支是改过的新 creative、还在审核，而且年龄 25+/Adv+ ON
     违反 owner「年龄 30 起」+「先别开」；新账户同 BM，少给 Meta 一次机会。
不删、不改 targeting、不碰另外两条 campaign。CONFIRM=true 才写。"""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
REJECTED_AD = "120251329153540329"      # Video：不选 forex 不选黄金 @ Day Trading（Thelyin 改过的版本）
DT_ADSET = "120251329145970329"         # Day Trading | MY 28-65+（原 Day Trading | MY 30+）


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    ad = g._request("GET", REJECTED_AD, params={"fields": "id,name,status,effective_status,creative{id}"})
    aset = g._request("GET", DT_ADSET, params={
        "fields": "id,name,status,effective_status,targeting{age_min,age_max,targeting_automation}"})
    t = aset.get("targeting") or {}
    print(f"ad    [{ad.get('status')}/{ad.get('effective_status')}] «{ad.get('name')}» creative={(ad.get('creative') or {}).get('id')}")
    print(f"adset [{aset.get('status')}/{aset.get('effective_status')}] «{aset.get('name')}» age {t.get('age_min')}-{t.get('age_max')}"
          f" adv+={(t.get('targeting_automation') or {}).get('advantage_audience')}")
    if not CONFIRM:
        print("DRY RUN — 会：ad PAUSED + 🚫 改名；adset PAUSED。"); return
    if ad.get("status") != "PAUSED":
        g.update_status(REJECTED_AD, "PAUSED"); print("  ⏸ ad PAUSED")
    time.sleep(0.8)
    if compliance.BAN_MARK not in (ad.get("name") or ""):
        g._request("POST", REJECTED_AD, data={"name": f"{compliance.BAN_MARK} {ad.get('name')}"}); print("  🚫 ad 改名")
    time.sleep(0.8)
    if aset.get("status") != "PAUSED":
        g.update_status(DT_ADSET, "PAUSED"); print("  ⏸ adset PAUSED")
    time.sleep(3)
    ad2 = g._request("GET", REJECTED_AD, params={"fields": "name,status,effective_status"})
    as2 = g._request("GET", DT_ADSET, params={"fields": "name,status,effective_status"})
    print(f"复查 ad [{ad2.get('status')}/{ad2.get('effective_status')}] «{ad2.get('name')}»")
    print(f"复查 adset [{as2.get('status')}/{as2.get('effective_status')}] «{as2.get('name')}»")
    print("DT CONTAIN DONE")


if __name__ == "__main__":
    main()
