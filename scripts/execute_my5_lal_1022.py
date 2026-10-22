# -*- coding: utf-8 -*-
"""owner 2026-10-22「第三步，我同意」— MY 5.0 Purchase LAL:
1) customer-list custom audience «STOCKBLOOM Paid Students 1022» from the Paid Student List (email + phone,
   normalised and SHA-256 hashed inside this run — raw PII is never printed or stored);
2) lookalike 5% MY of it;
3) campaign «(Webinarkit) STOCKBLOOM | PURCHASE LAL 5% MY | 1-1-5 | 1022», CBO RM60, created PAUSED (owner activates),
   ad set «Purchase LAL 5% | MY 28+» age 28-65 hard / Advantage+ off, promoted object + MALAYSIA_UNIVERSAL from the
   MY BUSINESS OWNER Webinarkit ad set, 5 ads reusing its approved creatives. Ban gate. Idempotent by name.
CONFIRM=true writes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from adbot import compliance
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CA_NAME = "STOCKBLOOM Paid Students 1022"
LAL_NAME = "Lookalike (MY, 5%) - STOCKBLOOM Paid Students 1022"
NAME = "(Webinarkit) STOCKBLOOM | PURCHASE LAL 5% MY | 1-1-5 | 1022"
ASET = "Purchase LAL 5% | MY 28+"
DAILY = 6000
SRC_MY_SET = "120251454700740329"
WANT = ["Video：盖电脑，喂！", "Video：年纪大的人做不了交易？", "Video：赚美金，一定要接美国客户？", "freestyle: korea", "Video：用我的方法"]
H = lambda v: hashlib.sha256(v.encode()).hexdigest()


def _phone(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if not d:
        return ""
    if d.startswith("60") or d.startswith("65"):
        return d if len(d) >= 10 else ""
    if d.startswith("0"):                       # MY local 01x…
        return "6" + d
    if len(d) == 8 and d[0] in "689":           # SG local
        return "65" + d
    if d.startswith("1") and 9 <= len(d) <= 10:  # MY without leading 0
        return "60" + d
    return ""


def main() -> None:
    my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(my)
    acct = my.meta.account_path
    print(f"MY LAL build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned(WANT, my.compliance.banned_creatives), "banned"
    print("  account:", g.get_object(acct, "name,tos_accepted,user_tos_accepted"))
    vals = SheetsClient(my.secrets.google_sa_json).read_tab(my.cpa.spreadsheet_id, my.cpa.sales_tab)
    hi = next(i for i, r in enumerate(vals[:8]) if "UTM Campaign" in r)
    h = vals[hi]
    ei, pi = h.index("Email"), h.index("Phone Number")
    emails, phones = set(), set()
    for r in vals[hi + 1:]:
        e = (r[ei] if ei < len(r) else "").strip().lower()
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e):
            emails.add(H(e))
        p = _phone(r[pi] if pi < len(r) else "")
        if p:
            phones.add(H(p))
    print(f"  Paid Student List: {len(vals) - hi - 1} rows → {len(emails)} hashed emails · {len(phones)} hashed phones")
    src = g.get_object(SRC_MY_SET, "promoted_object,regional_regulated_categories,regional_regulation_identities,targeting")
    cr = {}
    for a in g._get_all(SRC_MY_SET + "/ads", {"fields": "name,creative{id}", "limit": "20"}):
        if a["name"] in WANT and a["name"] not in cr:
            cr[a["name"]] = a["creative"]["id"]
    assert not [w for w in WANT if w not in cr], "creative missing"
    existing = {c["name"]: c["id"] for c in g.list_custom_audiences(acct)}
    camps = {c["name"]: c["id"] for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "200"})}
    print(f"  exists? CA {CA_NAME in existing} · LAL {LAL_NAME in existing} · campaign {NAME in camps}")
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nLAL DONE (dry-run)"); return
    ca = existing.get(CA_NAME)
    if not ca:
        ca = g._request("POST", f"{acct}/customaudiences", data={
            "name": CA_NAME, "subtype": "CUSTOM", "customer_file_source": "USER_PROVIDED_ONLY",
            "description": "Paid Student List buyers (hashed email + phone), 2026-10-22"})["id"]
        for schema, rows in (("EMAIL_SHA256", sorted(emails)), ("PHONE_SHA256", sorted(phones))):
            for i in range(0, len(rows), 5000):
                r = g._request("POST", f"{ca}/users", data={"payload": json.dumps({"schema": schema, "data": rows[i:i + 5000]})})
                print(f"    upload {schema}: received {r.get('num_received')} · invalid {r.get('num_invalid_entries')}")
                time.sleep(1)
    print(f"  ✅ custom audience {ca}")
    lal = existing.get(LAL_NAME)
    if not lal:
        lal = g._request("POST", f"{acct}/customaudiences", data={
            "name": LAL_NAME, "subtype": "LOOKALIKE", "origin_audience_id": ca,
            "lookalike_spec": json.dumps({"type": "custom_ratio", "ratio": 0.05, "country": "MY"})})["id"]
    print(f"  ✅ lookalike {lal}")
    if NAME in camps:
        print(f"  campaign already exists {camps[NAME]} — stop\nLAL DONE"); return
    t0 = src["targeting"]
    t = {"geo_locations": t0["geo_locations"], "locales": t0.get("locales"), "custom_audiences": [{"id": lal}],
         "age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}}
    t = {k: v for k, v in t.items() if v is not None}
    c = g.create_campaign(acct, name=NAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                          daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")
    time.sleep(2)
    a = g.create_adset(acct, name=ASET, campaign_id=c["id"], status="ACTIVE", optimization_goal="OFFSITE_CONVERSIONS",
                       billing_event="IMPRESSIONS", targeting=t, promoted_object=src["promoted_object"],
                       attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                       regional_regulated_categories=src["regional_regulated_categories"],
                       regional_regulation_identities=src["regional_regulation_identities"])
    time.sleep(2)
    ids = [g.create_ad(acct, name=w, adset_id=a["id"], creative={"creative_id": cr[w]}, status="ACTIVE")["id"] for w in WANT]
    print(f"  ✅ {NAME}: campaign {c['id']} (PAUSED, RM{DAILY // 100}) · adset {a['id']} · ads {ids}")
    print("LAL DONE")


if __name__ == "__main__":
    main()
