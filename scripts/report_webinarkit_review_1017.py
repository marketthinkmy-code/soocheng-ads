# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-17: review state + first hours of the 8 Webinarkit campaigns built 10/16. No PII."""
from __future__ import annotations

import json
import time
from collections import Counter

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

PLAN = {
    ("MY 5.0", "config.my5.yaml", "offsite_conversion.custom.1048291251556714"):
        ["120251454680840329", "120251454704570329", "120251454700150329", "120251454713670329"],
    ("SG", "config.sg.yaml", "offsite_conversion.custom.1614065190214320"):
        ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521"],
}


def main() -> None:
    for (label, cfg, token), camps in PLAN.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        print(f"\n################ {label} ################")
        states = Counter()
        tot = [0.0, 0, 0, 0.0]
        for cid in camps:
            c = g.get_object(cid, "name,status,effective_status,daily_budget")
            ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,ad_review_feedback", "limit": "50"})
            time.sleep(0.8)
            ins = g._get_all(cid + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "date_preset": "today"})
            r = ins[0] if ins else {}
            sp, imp, lc = float(r.get("spend") or 0), int(r.get("impressions") or 0), int(r.get("inline_link_clicks") or 0)
            rg = extract_results(r.get("actions"), token)
            alltypes = sorted({a.get("action_type") for a in (r.get("actions") or []) if "custom" in (a.get("action_type") or "") or "registr" in (a.get("action_type") or "")})
            tot[0] += sp; tot[1] += imp; tot[2] += lc; tot[3] += rg
            print(f"\n  «{c['name']}» {c['status']}/{c['effective_status']} RM{int(c['daily_budget']) // 100} · 今天 RM{sp:.0f} · imp {imp} · 点击 {lc} · 报名 {rg:.0f} · types {alltypes}")
            for a in ads:
                if a.get("status") in ("DELETED", "ARCHIVED"):
                    continue
                states[a.get("effective_status")] += 1
                fb = a.get("ad_review_feedback")
                print(f"     {a.get('effective_status'):<16} «{a['name']}»" + (f"  审核: {json.dumps(fb, ensure_ascii=False)[:200]}" if fb else ""))
        print(f"\n  {label} 合计：{dict(states)} · 今天 RM{tot[0]:.0f} · imp {tot[1]} · 点击 {tot[2]} · 报名 {tot[3]:.0f}")
    print("\nREVIEW DONE (read-only)")


if __name__ == "__main__":
    main()
