# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08「看下 MY SG 哪些现在需要关的？」

For every ACTIVE registration ad on SG and MY 5.0: ban hit (yaml list / 🚫), review state,
today's spend / registrations (account TZ), the creative's destination (post reuse vs. new
creative; CTA type; WhatsApp / app destination — a WhatsApp CTA on a COMPLETE_REGISTRATION ad
sends people away from the LP), and 7-day sales for the creative (sheet). Verdict column:
⛔ 禁跑 / ⚠️ 目的地不是报名页 / 👀 看着 / ✅. No PII."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

REJECTED_TODAY = ["不选 forex"]      # MY 5.0 15:13 + ~16:00 SGT, twice; owner deleted MY copies


def cta_of(cr: dict) -> str:
    spec = cr.get("object_story_spec") or {}
    for key in ("link_data", "video_data", "photo_data"):
        d = spec.get(key) or {}
        cta = d.get("call_to_action") or {}
        if cta:
            v = cta.get("value") or {}
            return f"{cta.get('type')} {v.get('link') or ''} {v.get('app_destination') or ''}".strip()
        if d.get("link"):
            return f"link {d.get('link')}"
    return f"{cr.get('call_to_action_type') or '?'} (post reuse)" if cr.get("effective_object_story_id") else (cr.get("call_to_action_type") or "?")


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d7 = today - dt.timedelta(days=7)
    pool7 = {}
    for x in sales:
        if x.date and x.date >= d7:
            ck = cpa.creative_key(x.ad)
            pool7[ck] = pool7.get(ck, 0) + 1

    for label, cfg in (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        ads = g._get_all(acct + "/ads", {
            "fields": "id,name,status,effective_status,issues_info,"
                      "campaign{name,daily_budget},adset{name,daily_budget,promoted_object},"
                      "creative{id,effective_object_story_id,object_story_spec,call_to_action_type}",
            "limit": "500"})
        time.sleep(1.0)
        tod = {r.get("ad_id"): r for r in g.account_insights(acct, level="ad", fields="ad_id,spend,actions", date_preset="today")}
        time.sleep(1.0)
        live = [a for a in ads if a.get("effective_status") == "ACTIVE"
                and (((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type") or "").upper() == "COMPLETE_REGISTRATION"]
        print(f"\n═══ [{label}] 在跑 {len(live)} 支 ═══")
        print(f"{'判定':<10} {'素材 @ campaign':<58} {'今天花费':>8} {'报名':>4}  目的地 / CTA")
        for a in sorted(live, key=lambda a: -float((tod.get(a['id']) or {}).get('spend') or 0)):
            nm = a.get("name") or ""
            r = tod.get(a["id"]) or {}
            sp = float(r.get("spend") or 0); rg = extract_results(r.get("actions"), token)
            cr = a.get("creative") or {}
            cta = cta_of(cr)
            banned = compliance.banned_reason(nm, s.compliance.banned_creatives)
            rej = compliance.banned_reason(nm, REJECTED_TODAY)
            wa = "WHATSAPP" in cta.upper() or "wa.me" in cta
            if banned:
                v = "⛔禁跑"
            elif rej:
                v = "⛔今被拒"
            elif wa:
                v = "⚠️WhatsApp"
            elif a.get("issues_info"):
                v = "❗issue"
            elif rg == 0 and sp >= 100:
                v = "👀0reg"
            else:
                v = "✅"
            camp = ((a.get("campaign") or {}).get("name") or "")[:30]
            print(f"{v:<10} {nm[:26]:<27}@{camp:<30} RM{sp:>6.0f} {rg:>4.0f}  {cta[:70]}"
                  f"{'  7d成交 ' + str(pool7.get(cpa.creative_key(nm))) if pool7.get(cpa.creative_key(nm)) else ''}")
        print()
    print("CLOSE CANDIDATES DONE (read-only)")


if __name__ == "__main__":
    main()
