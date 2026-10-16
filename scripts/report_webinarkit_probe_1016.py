# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-16: before rebuilding on Webinarkit — (1) custom conversion 1048291251556714 (owner's
«WED WEBINARKIT REGISTER»): its pixel/dataset, rule, which ad accounts can see it; (2) the team-built
«(Webinarkit) STOCKBLOOM | DAY TRADING» chain on MY 5.0 as the template: campaign/adset/ad fields,
promoted_object, targeting, creative spec (video id, link, url_tags, copy head); (3) for SG + MY 5.0 the
latest ad per clean creative we plan to use, with its creative spec or post id. No PII."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CC = "1048291251556714"
WANT = ["盖电脑", "korea", "年纪大", "赚美金", "用我的方法", "不选 forex", "我跟你讲"]


def j(x, n=400):
    return json.dumps(x, ensure_ascii=False)[:n]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    print("═══ custom conversion ═══")
    try:
        cc = g.get_object(CC, "id,name,pixel{id,name},custom_event_type,rule,default_conversion_value,account_id,"
                              "business{id,name},is_archived,last_fired_time,event_source_type")
        print(" ", j(cc, 900))
    except Exception as e:                                          # noqa: BLE001
        print("  ❌", str(e)[:300])
    for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
        st = load_settings(REPO_ROOT / "config" / cfg)
        acct = st.meta.account_path
        print(f"\n################ {label} {acct} ################")
        time.sleep(1)
        try:
            ccs = g._get_all(acct + "/customconversions", {"fields": "id,name,pixel{id,name},custom_event_type", "limit": "100"})
            print("  customconversions:", j([c for c in ccs if "webinar" in (c.get("name") or "").lower() or c.get("id") == CC], 600))
        except Exception as e:                                      # noqa: BLE001
            print("  customconversions ❌", str(e)[:200])
        time.sleep(1)
        try:
            px = g._get_all(acct + "/adspixels", {"fields": "id,name,last_fired_time", "limit": "50"})
            print("  adspixels:", j(px, 600))
        except Exception as e:                                      # noqa: BLE001
            print("  adspixels ❌", str(e)[:200])
        time.sleep(1)
        camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,objective,daily_budget,special_ad_categories,bid_strategy,buying_type,created_time", "limit": "200"})
        for c in camps:
            if "webinar" in (c.get("name") or "").lower():
                print("\n  ── template campaign:", j(c, 600))
                time.sleep(1)
                sets = g._get_all(c["id"] + "/adsets", {"fields": "id,name,status,daily_budget,optimization_goal,billing_event,bid_strategy,promoted_object,targeting,start_time,attribution_spec,destination_type,regional_regulated_categories,regional_regulation_identities", "limit": "20"})
                for a in sets:
                    print("    adset:", j(a, 2500))
                time.sleep(1)
                ads = g._get_all(c["id"] + "/ads", {"fields": "id,name,status,effective_status,creative{id,name,object_story_spec,asset_feed_spec,url_tags,effective_object_story_id,call_to_action_type,degrees_of_freedom_spec}", "limit": "20"})
                for a in ads:
                    print("    ad:", j(a, 1800))
        time.sleep(1)
        ads = g._get_all(acct + "/ads", {"fields": "id,name,status,created_time,campaign{name},creative{id,object_story_spec,url_tags,effective_object_story_id}", "limit": "500"})
        print(f"\n  ── latest ad per creative ({len(ads)} ads) ──")
        for w in WANT:
            hits = sorted([a for a in ads if w.lower() in (a.get("name") or "").lower() and "🚫" not in (a.get("name") or "")],
                          key=lambda a: a.get("created_time") or "", reverse=True)
            if not hits:
                print(f"   {w}: —"); continue
            a = hits[0]; cr = a.get("creative") or {}
            oss = cr.get("object_story_spec") or {}
            vd = oss.get("video_data") or {}
            print(f"   {w}: «{a.get('name')}» @ {((a.get('campaign') or {}).get('name') or '')[:40]} · creative {cr.get('id')} · "
                  f"video {vd.get('video_id')} · link {j((vd.get('call_to_action') or {}).get('value'), 160)} · post {cr.get('effective_object_story_id')} · "
                  f"url_tags {cr.get('url_tags')} · msg {j((vd.get('message') or '')[:60], 90)}")
    print("\nPROBE DONE (read-only)")


if __name__ == "__main__":
    main()
