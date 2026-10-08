# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08「day trading 有 rejected」— the ad-level read showed 0 rejected
(DAY TRADING ads IN_PROCESS, its ad set ACTIVE). Look one level up and down for what Ads Manager
is calling "rejected": campaign + ad set issues_info / effective_status, ad review feedback with
placement detail, creative status, and the last 3 hours of activity (who flipped the ad set)."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path

    print("═══ campaigns ═══")
    for c in g._get_all(acct + "/campaigns", {
            "fields": "id,name,status,effective_status,issues_info,special_ad_categories,"
                      "configured_status,daily_budget", "limit": "50"}):
        print(f"  [{c.get('status')}/{c.get('effective_status')}] «{c.get('name')}» special={c.get('special_ad_categories')}")
        for i in c.get("issues_info") or []:
            print(f"      ❗ {json.dumps(i, ensure_ascii=False)[:300]}")
    time.sleep(0.8)

    print("\n═══ ad sets ═══")
    for a in g._get_all(acct + "/adsets", {
            "fields": "id,name,status,effective_status,issues_info,campaign{name},"
                      "targeting{age_min,age_max,flexible_spec,targeting_automation,locales},"
                      "learning_stage_info", "limit": "50"}):
        print(f"  [{a.get('status')}/{a.get('effective_status')}] «{a.get('name')}» @ «{((a.get('campaign') or {}).get('name') or '')[:36]}»"
              f" learning={(a.get('learning_stage_info') or {}).get('status')}")
        t = a.get("targeting") or {}
        print(f"      targeting: age {t.get('age_min')}-{t.get('age_max')} adv+={((t.get('targeting_automation') or {}).get('advantage_audience'))}"
              f" flexible={json.dumps(t.get('flexible_spec'), ensure_ascii=False)[:260]}")
        for i in a.get("issues_info") or []:
            print(f"      ❗ {json.dumps(i, ensure_ascii=False)[:300]}")
    time.sleep(0.8)

    print("\n═══ ads（含 review feedback / creative）═══")
    for a in g._get_all(acct + "/ads", {
            "fields": "id,name,status,effective_status,issues_info,"
                      "ad_review_feedback{global,placement_specific},"
                      "creative{id,status,effective_object_story_id},adset{name}", "limit": "100"}):
        fb = a.get("ad_review_feedback") or {}
        cr = a.get("creative") or {}
        print(f"  [{a.get('status')}/{a.get('effective_status')}] «{(a.get('name') or '')[:34]}» @ «{(a.get('adset') or {}).get('name')}»"
              f" creative={cr.get('id')}({cr.get('status')})")
        if fb:
            print(f"      review: {json.dumps(fb, ensure_ascii=False)[:400]}")
        for i in a.get("issues_info") or []:
            print(f"      ❗ {json.dumps(i, ensure_ascii=False)[:300]}")
    time.sleep(0.8)

    since = int(dt.datetime.utcnow().timestamp()) - 3 * 3600
    print("\n═══ 近 3 小时 activity ═══")
    for x in g._get_all(acct + "/activities", {
            "fields": "event_time,event_type,actor_name,object_name,extra_data",
            "since": str(since), "limit": "100"})[:60]:
        print(f"  {(x.get('event_time') or '')[5:16]}  {(x.get('actor_name') or '?')[:18]:<18}"
              f" {(x.get('event_type') or '')[:34]:<34} «{(x.get('object_name') or '')[:40]}»"
              f" {str(x.get('extra_data') or '')[:120]}")
    print("\nMY5 ISSUES DONE (read-only)")


if __name__ == "__main__":
    main()
