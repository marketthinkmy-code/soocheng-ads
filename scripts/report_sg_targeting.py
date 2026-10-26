# -*- coding: utf-8 -*-
"""READ-ONLY: targeting of every SG ad set that ran since 10/17 — geo, locales, age, Advantage+, custom audiences,
interest count — plus 30-day account reach/frequency/CPM, to see what SG audience the ads actually reach."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
r = g._get_all(acct + "/insights", {"fields": "reach,frequency,cpm,spend", "date_preset": "last_30d"})
print("30 天账户：", {k: r[0].get(k) for k in ("reach", "frequency", "cpm", "spend")} if r else "—")
for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status", "limit": "200"}):
    if "webinarkit" not in c["name"].lower():
        continue
    for a in g._get_all(c["id"] + "/adsets", {"fields": "name,effective_status,targeting", "limit": "20"}):
        t = a.get("targeting") or {}
        flex = t.get("flexible_spec") or []
        n = sum(len(spec.get(k) or []) for spec in flex for k in ("interests", "behaviors", "work_positions", "industries"))
        print(f"  {c['name'][13:55]} › {a['name']} [{a['effective_status']}] · geo {t.get('geo_locations', {}).get('countries')} · "
              f"locales {t.get('locales')} · age {t.get('age_min')}-{t.get('age_max')} · adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')} · "
              f"CA {[x.get('name', x.get('id')) for x in t.get('custom_audiences', [])]} · interests {n}")
print("SG TARGETING DONE (read-only)")
