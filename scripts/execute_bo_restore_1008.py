# -*- coding: utf-8 -*-
"""Restore the TEAM's Business Owner interest set on MY 5.0 — hard-locked.

Activity log (10/8): Thelyin set this group at 16:06, 16:25 and again 16:33 SGT; my re-lock
runs (16:26, 16:57) overwrote it with the old-account clone — a misread of「硬锁回 … 兴趣」.
This puts THEIR list back, with the owner's rules applied: age 28–65 hard, Advantage+ OFF,
one OR-group (interests + behaviour + job titles), geo MY, Chinese. Names are resolved to ids
through the targeting search API and printed; CONFIRM=true writes targeting only."""
from __future__ import annotations

import json
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BO_ADSET = "120251329164990329"
# (name as Ads Manager shows it, category hint from the activity log's parenthetical)
INTERESTS = [
    ("Small business", "business and finance"), ("creative entrepreneurship", "business and financial industries"),
    ("business plan", "business activities"), ("Small and medium enterprises", "business and finance"),
    ("Self-employment", "careers"), ("business model", "business and financial industries"),
    ("Passive income", "business and finance"), ("Start-up company", "business and finance"),
    ("Entrepreneurship", "business and finance"), ("Sole proprietorship", "business and finance"),
    ("Business", "business and finance"), ("Home business", "business and finance"),
]
KNOWN_INTEREST_IDS = {"Start-up company": "6003325004380", "Entrepreneurship": "6003371567474",
                      "Business": "6003402305839"}   # Meta's name is «Business (business and finance)» — seen in the dry-run candidates
BEHAVIORS = [{"id": "6002714898572", "name": "Small business owners"}]
JOB_TITLES = ["Chief executive officer", "Owner", "Owner and Founder", "Founder", "Managing Director"]
KNOWN_JOB_IDS = {"Chief executive officer": "103113219728224", "Owner": "110722838955052",
                 "Founder": "849873341726582", "Managing Director": "874842615892965"}


def resolve(g, kind, name, hint=""):
    """Exact name match first; else name match whose category path/topic carries the hint.
    Prints the top candidates so a miss can be judged by eye."""
    rows = g._get_all("search", {"type": kind, "q": name, "limit": "50"})
    key = name.casefold()
    exact = [r for r in rows if (r.get("name") or "").casefold() == key]
    if len(exact) == 1 or (exact and not hint):
        return exact[0]
    h = hint.casefold().replace("&", "and")
    def cat(r):
        return " ".join([str(x) for x in (r.get("path") or [])] + [str(r.get("topic") or ""),
                        str(r.get("disambiguation_category") or "")]).casefold().replace("&", "and")
    hinted = [r for r in exact if h and h in cat(r)]
    if hinted:
        return hinted[0]
    loose = [r for r in rows if key in (r.get("name") or "").casefold() and (not h or h in cat(r))]
    if len(loose) == 1:
        return loose[0]
    for r in rows[:5]:
        print(f"      候选: {r.get('id')} «{r.get('name')}» path={r.get('path')} topic={r.get('topic')}"
              f" disamb={r.get('disambiguation_category')} aud={r.get('audience_size_upper_bound')}")
    return exact[0] if exact else None


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    interests, missing = [], []
    for nm, hint in INTERESTS:
        if nm in KNOWN_INTEREST_IDS:
            interests.append({"id": KNOWN_INTEREST_IDS[nm], "name": nm}); continue
        hit = resolve(g, "adinterest", nm, hint)
        if hit:
            interests.append({"id": hit["id"], "name": hit.get("name")})
            print(f"  interest «{nm}» → {hit['id']} (受众上限 {hit.get('audience_size_upper_bound')})")
        else:
            missing.append(("interest", nm)); print(f"  interest «{nm}» → ❌ 找不到精确匹配")
        time.sleep(0.5)
    jobs = []
    for nm in JOB_TITLES:
        if nm in KNOWN_JOB_IDS:
            jobs.append({"id": KNOWN_JOB_IDS[nm], "name": nm}); continue
        hit = resolve(g, "adworkposition", nm)
        if hit:
            jobs.append({"id": hit["id"], "name": hit.get("name")})
            print(f"  job «{nm}» → {hit['id']}")
        else:
            missing.append(("job", nm)); print(f"  job «{nm}» → ❌ 找不到精确匹配")
        time.sleep(0.5)

    cur = g._request("GET", BO_ADSET, params={"fields": "name,status,targeting"})
    ct = cur.get("targeting") or {}
    t = {
        "geo_locations": ct.get("geo_locations") or {"countries": ["MY"], "location_types": ["home", "recent"]},
        "age_min": 28, "age_max": 65,
        "targeting_automation": {"advantage_audience": 0},
        "locales": ct.get("locales") or s.meta.targeting.locales,
        "flexible_spec": [{"interests": interests, "behaviors": BEHAVIORS, "work_positions": jobs}],
    }
    print(f"\n▶ «{cur.get('name')}» [{cur.get('status')}] 现在: age {ct.get('age_min')}-{ct.get('age_max')}"
          f" adv+={(ct.get('targeting_automation') or {}).get('advantage_audience')}"
          f" interests={[i.get('name') for fs in (ct.get('flexible_spec') or []) for i in fs.get('interests', [])]}")
    print(f"  改成: {json.dumps(t, ensure_ascii=False)[:900]}")
    if missing:
        print(f"\n⚠️ 没解析到：{missing} — 这几项不会进 spec，先回报。")
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才写（只改 targeting，广告不重审）。"); return
    g.update_targeting(BO_ADSET, t)
    time.sleep(3)
    o = g._request("GET", BO_ADSET, params={"fields": "name,status,effective_status,targeting{age_min,age_max,targeting_automation,flexible_spec}"})
    ot = o.get("targeting") or {}
    print(f"  复查 «{o.get('name')}» [{o.get('status')}/{o.get('effective_status')}] age {ot.get('age_min')}-{ot.get('age_max')}"
          f" adv+={(ot.get('targeting_automation') or {}).get('advantage_audience')}"
          f" interests={[i.get('name') for fs in (ot.get('flexible_spec') or []) for i in fs.get('interests', [])]}"
          f" jobs={[i.get('name') for fs in (ot.get('flexible_spec') or []) for i in fs.get('work_positions', [])]}")
    print("BO RESTORE DONE")


if __name__ == "__main__":
    main()
