# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: owner「SG 异常，今天都没有 leads」. SG vs MY today (MYT): per campaign spend · imp · link clicks ·
LPV · custom-conversion regs · all action types; the two custom conversions' rule / status / last fired; dataset stats;
Register tab rows today split by UTM [SG] / MY / none (ground truth, no PII)."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
Y = TODAY - dt.timedelta(days=1)
CC = {"config.sg.yaml": "1614065190214320", "config.my5.yaml": "1048291251556714"}


def main() -> None:
    for cfg, cc in CC.items():
        st = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        tok = f"offsite_conversion.custom.{cc}"
        print(f"\n######## {cfg}")
        c = g.get_object(cc, "name,rule,custom_event_type,is_archived,is_unavailable,last_fired_time,event_source_type")
        print(f"  CC {cc}: {json.dumps(c, ensure_ascii=False)[:400]}")
        for d in (Y, TODAY):
            rows = g.account_insights(st.meta.account_path, level="campaign",
                                      fields="campaign_name,spend,impressions,inline_link_clicks,actions",
                                      time_range={"since": d.isoformat(), "until": d.isoformat()})
            print(f"  ── {d}")
            for r in sorted(rows, key=lambda r: -float(r.get("spend") or 0)):
                acts = {a["action_type"]: a["value"] for a in (r.get("actions") or [])}
                print(f"   {r['campaign_name'][13:52]:<40} RM{float(r.get('spend') or 0):>5.0f} imp {r.get('impressions'):>5} "
                      f"点击 {r.get('inline_link_clicks', 0):>3} LPV {extract_results(r.get('actions'), 'landing_page_view'):>3.0f} "
                      f"报名 {extract_results(r.get('actions'), tok):.0f}")
                if d == TODAY:
                    print("      actions: " + ", ".join(f"{k}={v}" for k, v in acts.items() if "custom" in k or "pixel" in k or "lead" in k or "regist" in k or "landing" in k))
            time.sleep(1)
        time.sleep(1)
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
    hi = next(i for i, r in enumerate(vals[:8]) if "UTM Campaign" in r)
    h = vals[hi]
    di, ui, si = h.index("Created date"), h.index("UTM Campaign"), h.index("Source")
    cnt = Counter()
    for r in vals[hi + 1:]:
        d = cpa.parse_date(r[di][:20]) if di < len(r) else None
        if d in (Y, TODAY):
            u = (r[ui] if ui < len(r) else "").strip().lower()
            k = "SG" if "[sg]" in u else ("MY" if u else "无UTM")
            cnt[(d.isoformat(), k, (r[si] if si < len(r) else "")[:26])] += 1
    print("\nRegister 实际报名（日期 · 市场 · source）:")
    for k, n in sorted(cnt.items()):
        print(f"   {k[0]} · {k[1]:<5} · {k[2]:<26} {n}")
    print("\nSG TODAY DONE (read-only)")


if __name__ == "__main__":
    main()
