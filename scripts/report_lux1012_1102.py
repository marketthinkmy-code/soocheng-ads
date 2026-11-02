# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/2「唯一有原位成交的那支 LUXURY MY 1-1-4 1012 korea，我该不该开？」).
Locate «STOCKBLOOM | LUXURY MY | 1-1-4 | 1012» on MY 5.0 and report: campaign/ad set/ads status + budget, who turned the
campaign off and when, optimisation event (promoted_object), every ad's destination link (post-reuse → read the post's CTA
link via the page token if possible), lifetime spend · clicks · results, and the strict sale row(s) (date · amount · source, no PII)."""
from __future__ import annotations

import datetime as dt
import json

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

AD = "120251390712180329"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
a0 = g.get_object(AD, "campaign{id,name,status,effective_status,daily_budget,created_time,start_time,stop_time}")
c = a0["campaign"]
print(f"«{c['name']}» · campaign {c['id']} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100} · 建 {c['created_time'][:10]}")
acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data",
                                                       "since": str(int(dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc).timestamp())), "limit": "2000"})
for x in sorted(acts, key=lambda x: x["event_time"]):
    if x.get("object_id") == c["id"] and ("run_status" in x["event_type"] or "budget" in x["event_type"]):
        print(f"   {x['event_time'][:16]}Z {x.get('actor_name', ''):<16} {x['event_type']} · {(x.get('extra_data') or '')[:110]}")
lt = json.dumps({"since": "2026-10-12", "until": (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()})
perf = {r["ad_id"]: r for r in g._get_all(c["id"] + "/insights", {"fields": "ad_id,spend,inline_link_clicks,actions,date_start,date_stop", "level": "ad", "time_range": lt})}
for st in g._get_all(c["id"] + "/adsets", {"fields": "name,status,effective_status,promoted_object,optimization_goal,targeting", "limit": "10"}):
    t = st["targeting"]
    ints = [i.get("name") for sp in t.get("flexible_spec") or [] for i in sp.get("interests") or []]
    print(f"  › {st['name']} · adset {st['id']} · {st['status']}/{st['effective_status']} · 优化 {st.get('optimization_goal')} · promoted {st.get('promoted_object')}\n"
          f"     受众: age {t.get('age_min')}-{t.get('age_max')} · adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')} · 兴趣 {len(ints)}: {ints[:12]}")
    for a in g._get_all(st["id"] + "/ads", {"fields": "name,status,effective_status,creative{effective_object_story_id,object_story_spec,url_tags}", "limit": "20"}):
        cr = a.get("creative") or {}
        post = cr.get("effective_object_story_id")
        link = ""
        try:
            p = g.get_object(post, "call_to_action,permalink_url")
            link = ((p.get("call_to_action") or {}).get("value") or {}).get("link", "")
        except Exception as e:                                           # noqa: BLE001
            link = f"(读不到 post: {str(e)[:60]})"
        r = perf.get(a["id"], {})
        acts_ = {x["action_type"]: x["value"] for x in r.get("actions") or []}
        print(f"     · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']} · RM{float(r.get('spend') or 0):.0f} · 点击 {r.get('inline_link_clicks', 0)} · "
              f"{r.get('date_start', '')}→{r.get('date_stop', '')} · 结果 {{{', '.join(f'{k}:{v}' for k, v in acts_.items() if 'offsite_conversion' in k or k == 'landing_page_view')}}}\n"
              f"        post {post} → {link}")
sales, _c, _h = cpa.parse_sales(SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab), 2399.0)
for x in sales:
    if _mkey(x.campaign) == _mkey(c["name"]):
        print(f"\n  原位成交: {x.date} · RM{x.amount:,.0f} · ad set «{x.adset}» · ad «{x.ad}»")
print("\nLUX1012 DONE (read-only)")
