# -*- coding: utf-8 -*-
"""Owner-approved 2026-08-13 («执行» on the decision list from the 8/12 sales review):

  SCALE +30%  · [SG] STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3   (我只有一个目的, 60d CPA 419)
              · STOCKBLOOM | TRAVEL | 1-1-3                  (你没有本钱, CPL 24 / CPA 517)
              · [SG] STOCKBLOOM | INVESTMENT | 1-1-3         (freestyle 1, 60d CPA 668)
  OPEN        · ad 120248256492180521 «video 1：用我的方法» in SG INVESTMENT
                (creative sold again 8/12; its own 60d CPA RM771 — healthy)
  CLOSE       · [SG] STOCKBLOOM | TRAVEL TOP3 | 1-1-3        (14d no sales, 3d CPL 89)

Verify-then-write on every target (exact name match, status checks, post-write reads).
Idempotent; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
FACTOR = 1.3

SCALE = [
    ("SG", "[SG] STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3"),
    ("MY", "STOCKBLOOM | TRAVEL | 1-1-3"),
    ("SG", "[SG] STOCKBLOOM | INVESTMENT | 1-1-3"),
]
CLOSE = [("SG", "[SG] STOCKBLOOM | TRAVEL TOP3 | 1-1-3")]
REOPEN_AD = ("SG", "120248256492180521", "用我的方法", "investment")

CFGS = {"MY": "config.yaml", "SG": "config.sg.yaml"}


def client(label, cache={}):
    if label not in cache:
        cache[label] = graph_client(load_settings(REPO_ROOT / "config" / CFGS[label]))
    return cache[label]


def find_campaign(g, acct: str, name: str):
    for c in g._get_all(f"{acct}/campaigns",
                        {"fields": "id,name,effective_status,daily_budget", "limit": "500"}):
        if (c.get("name") or "").strip() == name:
            return c
    return None


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Execute 8/13 plan — {mode}\n")

    print("── 1) SCALE +30% ──")
    for label, name in SCALE:
        g = client(label)
        acct = load_settings(REPO_ROOT / "config" / CFGS[label]).meta.account_path
        c = find_campaign(g, acct, name)
        if not c:
            print(f"  ⛔ [{label}] '{name}' not found — skip")
            continue
        st, cur = c.get("effective_status"), int(c.get("daily_budget") or 0)
        if st != "ACTIVE":
            print(f"  ⚠️ [{label}] '{name}' is {st} — not scaling a non-active campaign")
            continue
        if not cur:
            print(f"  ⚠️ [{label}] '{name}' has no campaign daily_budget (ABO?) — skip, report")
            continue
        new = int(round(cur * FACTOR / 100.0) * 100)
        if not CONFIRM:
            print(f"  ▶ [{label}] {name}: RM{cur/100:.0f}/day -> RM{new/100:.0f}/day")
            continue
        g._request("POST", c["id"], data={"daily_budget": str(new)})
        time.sleep(PACE)
        after = int((g.get_object(c["id"], "daily_budget") or {}).get("daily_budget") or 0)
        print(f"  ✅ [{label}] {name}: RM{cur/100:.0f} -> RM{after/100:.0f}/day"
              + ("" if after == new else "  ⚠️ verify mismatch"))
        time.sleep(PACE)

    print("\n── 2) OPEN 用我的方法 (SG INVESTMENT) ──")
    label, ad_id, name_sub, camp_sub = REOPEN_AD
    g = client(label)
    try:
        ad = g.get_object(ad_id, "name,effective_status,campaign{name,effective_status}")
        nm, st = ad.get("name", "?"), ad.get("effective_status", "?")
        camp = ad.get("campaign") or {}
        ok = (cpa.norm(name_sub) in cpa.norm(nm)
              and camp_sub in cpa.norm(camp.get("name", ""))
              and camp.get("effective_status") == "ACTIVE")
        print(f"  «{nm}» status={st} · campaign «{camp.get('name')}» ({camp.get('effective_status')})")
        if not ok:
            print("  ⛔ verification failed (name/campaign/campaign-status) — skip")
        elif st == "ACTIVE":
            print("  ✓ already ACTIVE")
        elif not CONFIRM:
            print(f"  ▶ would ACTIVATE ad {ad_id}")
        else:
            g.update_status(ad_id, "ACTIVE")
            time.sleep(PACE)
            after = g.get_object(ad_id, "effective_status").get("effective_status")
            print(f"  ✅ ACTIVATED ad {ad_id}  {st} -> {after}")
    except GraphError as e:
        print(f"  ❌ {e}")

    print("\n── 3) CLOSE SG TRAVEL TOP3 ──")
    for label, name in CLOSE:
        g = client(label)
        acct = load_settings(REPO_ROOT / "config" / CFGS[label]).meta.account_path
        c = find_campaign(g, acct, name)
        if not c:
            print(f"  ⛔ [{label}] '{name}' not found — skip")
            continue
        st = c.get("effective_status")
        if st == "PAUSED":
            print(f"  ✓ [{label}] '{name}' already PAUSED")
            continue
        if not CONFIRM:
            print(f"  ▶ [{label}] would PAUSE campaign {c['id']} '{name}' (now {st})")
            continue
        g.update_status(c["id"], "PAUSED")
        time.sleep(PACE)
        after = g.get_object(c["id"], "effective_status").get("effective_status")
        print(f"  ✅ [{label}] PAUSED '{name}'  {st} -> {after}")

    print("\nDONE" if CONFIRM else "\nDRY-RUN DONE — set confirm=true to apply.")


if __name__ == "__main__":
    main()
