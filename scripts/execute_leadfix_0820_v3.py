# -*- coding: utf-8 -*-
"""Lead-fix 8/20 v3 — owner «都一起执行吧»: revive+scale the approved sellers, and
add the recency picks into the MY LAL ladder. Everything here is idempotent or
compare-and-set (the owner is working in Ads Manager concurrently — a drifted
budget is skipped with a report, never double-scaled).

MY: revive DAY TRADING solo-炒过那么多 + budget 100→150 ·
    revive INVESTMENT solo-你敢吗 + budget 260→338 ·
    revive twin TRAVEL as «STOCKBLOOM | 用我的方法 | 1-1-1» solo-用我的方法,
    budget 320→100 ·
    ladder campaign: +炒过那么多 +你敢吗 into all 5 band ad sets, rename 1-5-3→1-5-5
SG: revive GOLF PICKBLEBALL solo-我只有一个目的 + budget 220→330 ·
    revive RUNNING solo-你敢吗 + budget 250→325
(“solo” = only the driver ad is flipped ACTIVE; sibling ads keep their stored
status — the diag shows they are all PAUSED, so nothing else wakes up.)
"""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
N = cpa.norm

LADDER_CAMP = "120248446935660575"
LADDER_NAME_NEW = "STOCKBLOOM | PURCHASE LAL 1-5% | 1-5-5"
LADDER_ADSETS = {"1%": "120248446939860575", "1-2%": "120248446964010575",
                 "2-3%": "120248446989680575", "3-4%": "120248447012860575",
                 "4-5%": "120248447034920575"}
LADDER_ADDS = ["video 12：炒过那么多，累而且不稳定", "video 2：你敢吗？"]

REVIVES = {
    "MY": [
        {"cid": "120247921988670575", "label": "DAY TRADING (炒过那么多)",
         "driver": "video 12：炒过那么多，累而且不稳定",
         "expect": 10000, "new": 15000},
        {"cid": "120247585357770575", "label": "INVESTMENT (你敢吗)",
         "driver": "video 2：你敢吗？", "expect": 26000, "new": 33800},
        {"cid": "120247525704130575", "label": "用我的方法 (原同名 TRAVEL 双胞胎)",
         "driver": "video 1: 用我的方法，你也可以有将多",
         "expect": 32000, "new": 10000,
         "rename": "STOCKBLOOM | 用我的方法 | 1-1-1"},
    ],
    "SG": [
        {"cid": "120248220643620521", "label": "GOLF PICKBLEBALL (我只有一个目的)",
         "driver": "video 2: 我只有一个目的", "expect": 22000, "new": 33000},
        {"cid": "120248231846030521", "label": "RUNNING (你敢吗)",
         "driver": "video 2：你敢吗？", "expect": 25000, "new": 32500},
    ],
}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Lead-fix v3 — revive+scale + MY ladder additions — {mode}\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"═══ [{label}] {acct} ═══")

        for r in REVIVES[label]:
            try:
                c = g._request("GET", r["cid"],
                               params={"fields": "name,status,daily_budget"})
                cur = int(c.get("daily_budget") or 0)
                print(f"  ● {r['label']}  «{c.get('name')}»  [{c.get('status')}] "
                      f"RM{cur/100:.0f}/day")
                if not CONFIRM:
                    print(f"     ▶ would: rename={r.get('rename') or '-'} · "
                          f"budget {r['expect']/100:.0f}→{r['new']/100:.0f} (CAS) · "
                          f"campaign+adsets ACTIVE · driver ad ACTIVE")
                    continue
                if r.get("rename") and c.get("name") != r["rename"]:
                    g._request("POST", r["cid"], data={"name": r["rename"]})
                    print(f"     ✏️ renamed → «{r['rename']}»")
                    time.sleep(PACE)
                if cur == r["new"]:
                    print(f"     · budget already RM{r['new']/100:.0f} — skip")
                elif cur != r["expect"]:
                    print(f"     ⛔ budget now RM{cur/100:.0f} ≠ expected "
                          f"RM{r['expect']/100:.0f} — NOT scaling (owner moved it?)")
                else:
                    g._request("POST", r["cid"], data={"daily_budget": r["new"]})
                    print(f"     💰 budget RM{cur/100:.0f} → RM{r['new']/100:.0f}/day")
                    time.sleep(PACE)
                if c.get("status") != "ACTIVE":
                    g.update_status(r["cid"], "ACTIVE")
                    print(f"     ▶ campaign → ACTIVE")
                    time.sleep(PACE)
                for aset in g._get_all(f"{r['cid']}/adsets",
                                       {"fields": "id,name,status", "limit": "10"}):
                    if aset.get("status") != "ACTIVE":
                        g.update_status(aset["id"], "ACTIVE")
                        print(f"     ▶ adset «{(aset.get('name') or '')[:36]}» → ACTIVE")
                        time.sleep(PACE)
                others = []
                for a in g._get_all(f"{r['cid']}/ads",
                                    {"fields": "id,name,status", "limit": "20"}):
                    if N(a.get("name") or "") == N(r["driver"]):
                        if a.get("status") != "ACTIVE":
                            g.update_status(a["id"], "ACTIVE")
                            print(f"     ▶ driver ad «{a.get('name')}» → ACTIVE")
                            time.sleep(PACE)
                        else:
                            print(f"     · driver ad already ACTIVE")
                    else:
                        others.append(f"«{(a.get('name') or '')[:24]}»[{a.get('status')}]")
                if others:
                    print(f"     队友保持原状: {', '.join(others)}")
                print(f"     ✅ {r['label']} live")
            except Exception as e:
                print(f"     ❌ {r['label']}: {str(e)[:130]} — continuing")

        # ── MY only: add recency picks into the LAL ladder ──
        if label == "MY":
            try:
                ads = g._get_all(
                    f"{acct}/ads",
                    {"fields": "name,effective_status,"
                               "creative{effective_object_story_id,object_story_id}",
                     "limit": "300"})
                time.sleep(2)

                def find_post(name):
                    cands = []
                    for a in ads:
                        if N(a.get("name") or "") != N(name):
                            continue
                        cr = a.get("creative") or {}
                        post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                        if post:
                            cands.append((0 if a.get("effective_status") == "ACTIVE" else 1,
                                          post, a.get("name")))
                    if not cands:
                        return None, None
                    cands.sort()
                    return cands[0][1], cands[0][2]

                camp = g._request("GET", LADDER_CAMP, params={"fields": "name"})
                print(f"  ● LAL ladder «{camp.get('name')}» — 加 {len(LADDER_ADDS)} 支 × 5 band")
                targets = []
                for nm in LADDER_ADDS:
                    post, disp = find_post(nm)
                    if not post:
                        print(f"     ⛔ «{nm[:30]}» 无可用 post — skip")
                        continue
                    targets.append({"name": disp, "post": post})
                    print(f"     pick «{disp}»  post={post}")
                if CONFIRM and targets:
                    if camp.get("name") != LADDER_NAME_NEW:
                        g._request("POST", LADDER_CAMP, data={"name": LADDER_NAME_NEW})
                        print(f"     ✏️ renamed campaign → «{LADDER_NAME_NEW}»")
                        time.sleep(PACE)
                    cr_cache = {}
                    for band, aset_id in LADDER_ADSETS.items():
                        have = {a.get("name") for a in g._get_all(
                            f"{aset_id}/ads", {"fields": "name", "limit": "20"})}
                        for t in targets:
                            if t["name"] in have:
                                print(f"     [{band}] «{t['name']}» 已在 — skip")
                                continue
                            cr_id = cr_cache.get(t["post"])
                            if not cr_id:
                                spec = {"name": f"MY | LAL ladder | {t['name']}",
                                        "object_story_id": t["post"]}
                                if s.meta.url_tags:
                                    spec["url_tags"] = s.meta.url_tags
                                cr_id = g.create_adcreative(acct, **spec)["id"]
                                cr_cache[t["post"]] = cr_id
                                time.sleep(PACE)
                            ad = g.create_ad(acct, name=t["name"], adset_id=aset_id,
                                             creative={"creative_id": cr_id},
                                             status="PAUSED", conversion_domain=conv)
                            print(f"     [{band}] ✓ added {ad['id']} «{t['name']}»")
                            time.sleep(PACE)
                elif not CONFIRM:
                    print(f"     ▶ would rename → 1-5-5 and add the picks into all 5 bands")
            except Exception as e:
                print(f"     ❌ ladder additions: {str(e)[:130]} — continuing")
        print()

    print("V3 DONE — revives live, ladder extended (still PAUSED)."
          if CONFIRM else "DRY-RUN — set confirm=true.")


if __name__ == "__main__":
    main()
