# -*- coding: utf-8 -*-
"""owner 2026-10-08「要硬锁回 Day Trading / Business Owner 兴趣」— MY 5.0 的两个兴趣 ad set
被手动改成了 Advantage+ ON、年龄 18/25 起、Business Owner 的兴趣也换了一组。

恢复成建的时候的样子：从旧 MY 3.0 的 «🌟 DAY TRADING | 1-1-3» / «BUSINESS OWNER | 1-1-3» 重新克隆
flexible_spec（同 execute_build_my5_1008），硬 age 28–65（owner 2026-10-08「以后年龄放 28+」）、advantage_audience=0、剥掉 age_range /
旧账户受众 / 版位键；geo MY + 中文。只改 targeting（不触发广告重审；会重置这两个 ad set 的学习期），
Day Trading 的名字改回「Day Trading | MY 30+」。Broad 不碰。CONFIRM=true 才写。"""
from __future__ import annotations

import json
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
OLD_MY = "act_759339046918885"
TARGETS = [
    ("120251329145970329", "DAY TRADING | 1-1-3",    "Day Trading | MY 28+"),
    ("120251329164990329", "BUSINESS OWNER | 1-1-3", "Business Owner | MY 28+"),
]
DROP_KEYS = ("custom_audiences", "excluded_custom_audiences", "age_range", "genders",
             "targeting_optimization", "targeting_relaxation_types", "publisher_platforms",
             "facebook_positions", "instagram_positions", "messenger_positions",
             "audience_network_positions", "device_platforms", "user_os")


def clone(g, fragment, locales):
    camps = g._get_all(OLD_MY + "/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(0.8)
    src = sorted([c for c in camps if fragment in (c.get("name") or "")],
                 key=lambda c: not (c.get("name") or "").startswith("🌟"))
    if not src:
        raise RuntimeError(f"old MY: no campaign «{fragment}»")
    asets = g._get_all(src[0]["id"] + "/adsets", {"fields": "id,name,targeting", "limit": "10"})
    time.sleep(0.8)
    t = dict(asets[0]["targeting"])
    for k in DROP_KEYS:
        t.pop(k, None)
    t["age_min"], t["age_max"] = 28, 65          # owner 2026-10-08「以后年龄放 28+」
    t["targeting_automation"] = {"advantage_audience": 0}
    if locales and not t.get("locales"):
        t["locales"] = locales
    return t, src[0].get("name")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    plan = []
    for aset_id, frag, name in TARGETS:
        cur = g._request("GET", aset_id, params={
            "fields": "id,name,status,targeting{age_min,age_max,targeting_automation,flexible_spec}"})
        ct = cur.get("targeting") or {}
        t, src_name = clone(g, frag, s.meta.targeting.locales)
        print(f"▶ «{cur.get('name')}» [{cur.get('status')}]")
        print(f"   现在: age {ct.get('age_min')}-{ct.get('age_max')} adv+={(ct.get('targeting_automation') or {}).get('advantage_audience')}"
              f" flexible={json.dumps(ct.get('flexible_spec'), ensure_ascii=False)[:200]}")
        print(f"   改成: age 28-65 adv+=0 (克隆自 «{src_name}») flexible={json.dumps(t.get('flexible_spec'), ensure_ascii=False)[:300]}")
        plan.append((aset_id, cur.get("name"), name, t))
        time.sleep(0.6)
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才写。"); return
    for aset_id, cur_name, name, t in plan:
        try:
            g.update_targeting(aset_id, t)
            if cur_name != name:
                g._request("POST", aset_id, data={"name": name})
            print(f"  ✅ «{name}» targeting 已硬锁回（28-65 / Adv+ off / 原兴趣）")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ❌ «{cur_name}»: {str(exc)[:200]}")
        time.sleep(1.5)
    time.sleep(3)
    for aset_id, _c, name, _t in plan:
        o = g._request("GET", aset_id, params={
            "fields": "name,status,effective_status,targeting{age_min,age_max,targeting_automation,flexible_spec}"})
        ot = o.get("targeting") or {}
        print(f"  复查 «{o.get('name')}» [{o.get('status')}/{o.get('effective_status')}] age {ot.get('age_min')}-{ot.get('age_max')}"
              f" adv+={(ot.get('targeting_automation') or {}).get('advantage_audience')}"
              f" interests={[i.get('name') for fs in (ot.get('flexible_spec') or []) for i in fs.get('interests', [])][:6]}")
        time.sleep(0.6)
    print("RELOCK DONE")


if __name__ == "__main__":
    main()
