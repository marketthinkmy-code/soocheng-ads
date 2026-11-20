# -*- coding: utf-8 -*-
"""READ-ONLY (CPL diagnosis 11/20): learning status + last significant edit time of every delivering ad set (both accounts).
Checks whether the 11/19 23:38 (my API placement write) / 11/20 00:05–00:11 (owner's manual placement fix) edits reset learning."""
import datetime as dt

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读")
for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    rows = g._get_all(s.meta.account_path + "/adsets", {"fields": "name,effective_status,learning_stage_info,campaign{name},updated_time",
                                                       "limit": "300", "effective_status": '["ACTIVE"]'})
    print(f"\n### {lab}: {len(rows)} 个在投放的 ad set")
    for a in rows:
        li = a.get("learning_stage_info") or {}
        ts = li.get("last_sig_edit_ts")
        t = (dt.datetime.utcfromtimestamp(int(ts)) + dt.timedelta(hours=8)).strftime("%m-%d %H:%M") if ts else "—"
        print(f"   {li.get('status', '—'):<10} 最后一次重大修改 {t} · 学习期转化 {li.get('conversions', '—')} | "
              f"{a['campaign']['name'].replace('(Webinarkit) ', '')} › {a['name']} · adset {a['id']}")
print("\nLEARNING 1120 DONE (read-only)")
