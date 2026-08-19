# -*- coding: utf-8 -*-
"""Owner 2026-08-19 «利用 lifetime 最多的吧»: re-point the two PURCHASE LAL 1-5%
ladder campaigns at each account's top-3 by LIFETIME sales (was: 30d-first).

Per account: recompute the sheet ranking sorted by (lifetime, 60d, 30d) desc,
resolve the first 3 names to live post ids, then for every band ad set in the
ladder campaign: create the missing wanted ads (one shared creative per post)
and DELETE ads no longer in the wanted trio. Deletes are scoped to ads inside
the exact-named ladder campaigns only, and refuse to touch anything whose
effective_status is ACTIVE. Idempotent; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
TODAY = dt.date(2026, 8, 19)
D30 = TODAY - dt.timedelta(days=30)
D60 = TODAY - dt.timedelta(days=60)

ACCTS = [
    {"label": "MY", "cfg": "config.yaml",
     "camp": "STOCKBLOOM | PURCHASE LAL 1-5% | 1-5-3"},
    {"label": "SG", "cfg": "config.sg.yaml",
     "camp": "[SG] STOCKBLOOM | PURCHASE LAL 1-5% | 1-5-3"},
]


def rank_lifetime(sales, label: str):
    """Sheet ads of one account ranked by (-lifetime, -60d, -30d)."""
    agg = {}
    for s in sales:
        if not s.ad:
            continue
        acct = "SG" if s.campaign.startswith("[sg]") else "MY"
        if acct != label:
            continue
        d = agg.setdefault(s.ad, {"life": 0, "d60": 0, "d30": 0})
        d["life"] += 1
        if s.date and s.date > D60:
            d["d60"] += 1
        if s.date and s.date > D30:
            d["d30"] += 1
    return sorted(agg.items(),
                  key=lambda kv: (-kv[1]["life"], -kv[1]["d60"], -kv[1]["d30"]))


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"LAL ladder → top-3 by LIFETIME sales — {mode}\n")

    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    # post pool from BOTH accounts (page-level posts work cross-account)
    pools = []
    for cfg in ("config.yaml", "config.sg.yaml"):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        pools.append(g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
             "limit": "300"}))
        time.sleep(1)

    def resolve_post(ad_key: str):
        cands = []
        for ads in pools:
            for a in ads:
                if cpa.norm(a.get("name") or "") != ad_key:
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    st = a.get("effective_status") or "?"
                    cands.append((0 if st == "ACTIVE" else 1, post, a.get("name"), st))
        if not cands:
            return None
        cands.sort()
        return {"post": cands[0][1], "name": cands[0][2], "src_status": cands[0][3]}

    for ac in ACCTS:
        label = ac["label"]
        s = load_settings(REPO_ROOT / "config" / ac["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"══ {label}  {acct} ══")

        ranked = rank_lifetime(sales, label)
        print("  lifetime ranking (life/60d/30d):")
        for name, d in ranked[:8]:
            print(f"    life={d['life']:3d}  60d={d['d60']:2d}  30d={d['d30']:2d}   «{name[:52]}»")

        top3 = []
        for ad_key, d in ranked:
            hit = resolve_post(ad_key)
            if hit:
                top3.append(hit)
                print(f"  TOP{len(top3)}: «{hit['name']}»  life={d['life']}  "
                      f"post={hit['post']}  (source ad: {hit['src_status']})")
            else:
                print(f"  (skip «{ad_key[:40]}» — no live post found)")
            if len(top3) == 3:
                break
        if len(top3) < 3:
            print(f"  ⛔ only {len(top3)} resolvable — skipping account\n")
            continue
        wanted = {t["name"] for t in top3}

        try:
            camp_id = None
            for c in g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"}):
                if c.get("name") == ac["camp"]:
                    camp_id = c["id"]
                    break
            if not camp_id:
                print(f"  ⛔ campaign «{ac['camp']}» not found — skipping\n")
                continue
            print(f"  campaign «{ac['camp']}» ({camp_id})")

            creative_cache = {}  # post id -> creative id (shared across bands)

            for aset in g._get_all(f"{camp_id}/adsets", {"fields": "id,name", "limit": "20"}):
                aset_id, aset_name = aset["id"], aset.get("name") or ""
                band = aset_name.split("Purchase LAL ")[-1].split(" |")[0] if "Purchase LAL " in aset_name else aset_name
                try:
                    have = g._get_all(f"{aset_id}/ads",
                                      {"fields": "id,name,effective_status", "limit": "20"})
                    have_names = {a.get("name") for a in have}
                    to_add = [t for t in top3 if t["name"] not in have_names]
                    to_del = [a for a in have if a.get("name") not in wanted]
                    if not CONFIRM:
                        print(f"   [{band}] would ADD {[t['name'] for t in to_add]}"
                              f" · DELETE {[a.get('name') for a in to_del]}")
                        continue
                    for t in to_add:
                        cr_id = creative_cache.get(t["post"])
                        if not cr_id:
                            spec = {"name": f"{label} | LAL ladder | {t['name']}",
                                    "object_story_id": t["post"]}
                            if s.meta.url_tags:
                                spec["url_tags"] = s.meta.url_tags
                            cr_id = g.create_adcreative(acct, **spec)["id"]
                            creative_cache[t["post"]] = cr_id
                            time.sleep(PACE)
                        ad = g.create_ad(acct, name=t["name"], adset_id=aset_id,
                                         creative={"creative_id": cr_id}, status="PAUSED",
                                         conversion_domain=conv)
                        print(f"   [{band}] ✓ added {ad['id']}  «{t['name']}»")
                        time.sleep(PACE)
                    for a in to_del:
                        if a.get("effective_status") == "ACTIVE":
                            print(f"   [{band}] ⚠️ NOT deleting «{a.get('name')}» — it is ACTIVE")
                            continue
                        g._request("DELETE", a["id"])
                        print(f"   [{band}] ✗ deleted {a['id']}  «{a.get('name')}»")
                        time.sleep(PACE)
                except Exception as e:  # throttle etc. — next band survives
                    print(f"   ❌ [{band}] {str(e)[:130]} — continuing")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()

    print("DONE — ladder now carries lifetime top-3; still PAUSED for owner review."
          if CONFIRM else "DRY-RUN — set confirm=true to apply.")


if __name__ == "__main__":
    main()
