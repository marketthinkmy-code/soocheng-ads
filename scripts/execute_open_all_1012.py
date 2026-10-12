# -*- coding: utf-8 -*-
"""owner 2026-10-12 21:05「你全开」— switch on every position built tonight. A PAUSED ad / ad set still in review goes
ACTIVE now and delivers by itself once Meta approves it. Guard: anything DISAPPROVED / WITH_ISSUES is NOT opened and
is reported (ban rule: a rejected creative is never pushed); for LUXURY MY the whole ad set stays closed if any of its
4 ads is rejected (owner: 有一支被拒先不要开). CONFIRM=true writes; otherwise dry-run. No PII."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BAD = {"DISAPPROVED", "WITH_ISSUES"}
SG_ADS = {  # ad id -> label
    "120249852158430521": "LUXURY GOODS · 不选 forex",
    "120249853085330521": "🌟 PURCHASE LAL 5% · 不选 forex",
    "120249853088580521": "🌟 GOLF PICKBLEBALL · 不选 forex",
    "120249853091340521": "PRIORITY BANKING · 不选 forex",
}
SG_ADSETS = {"120249853227330521": "PURCHASE LAL 1% adset", "120249853228540521": "RETARGET LP 14D adset"}
MY_ADSET = ("120251390707370329", "LUXURY MY adset")
opened, held = [], []


def show(kind, label, e):
    iss = e.get("issues_info") or []
    why = ("; ".join((i.get("error_summary") or i.get("error_message") or "")[:60] for i in iss)) if iss else ""
    print(f"  {kind:<6} «{label}» {e.get('status')} / eff {e.get('effective_status')}" + (f"  ⚠️ {why}" if why else ""))
    return e


def main() -> None:
    # ── SG ──────────────────────────────────────────────────────────────────────
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    print("═══ SG ═══")
    for aid, label in SG_ADS.items():
        e = show("ad", label, g.get_object(aid, "id,name,status,effective_status,issues_info,adset{status},campaign{status}"))
        time.sleep(0.5)
        if e.get("effective_status") in BAD:
            held.append(f"{label}: {e.get('effective_status')} — not opened"); continue
        if (e.get("adset") or {}).get("status") != "ACTIVE" or (e.get("campaign") or {}).get("status") != "ACTIVE":
            held.append(f"{label}: carrier not ACTIVE — not opened"); continue
        if e.get("status") == "ACTIVE":
            opened.append(f"{label}: already ACTIVE"); continue
        if CONFIRM:
            g.update_status(aid, "ACTIVE"); opened.append(f"{label}: ad → ACTIVE"); time.sleep(0.8)
        else:
            print(f"         plan: ad → ACTIVE")
    for sid, label in SG_ADSETS.items():
        e = show("adset", label, g.get_object(sid, "id,name,status,effective_status,campaign{status}"))
        ads = g._get_all(sid + "/ads", {"fields": "id,name,status,effective_status,issues_info", "limit": "10"})
        time.sleep(0.5)
        bad = [a for a in ads if a.get("effective_status") in BAD]
        for a in ads:
            show("  ad", a.get("name") or "", a)
        if bad:
            held.append(f"{label}: {len(bad)} rejected ad(s) — not opened"); continue
        if e.get("status") == "ACTIVE":
            opened.append(f"{label}: already ACTIVE"); continue
        if CONFIRM:
            g.update_status(sid, "ACTIVE"); opened.append(f"{label}: adset → ACTIVE"); time.sleep(0.8)
        else:
            print(f"         plan: adset → ACTIVE")

    # ── MY 5.0 ───────────────────────────────────────────────────────────────────
    s2 = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g2 = graph_client(s2)
    print("\n═══ MY 5.0 ═══")
    sid, label = MY_ADSET
    e = show("adset", label, g2.get_object(sid, "id,name,status,effective_status,campaign{status,daily_budget}"))
    ads = g2._get_all(sid + "/ads", {"fields": "id,name,status,effective_status,issues_info", "limit": "10"})
    time.sleep(0.5)
    for a in ads:
        show("  ad", a.get("name") or "", a)
    bad = [a for a in ads if a.get("effective_status") in BAD]
    if bad:
        held.append(f"{label}: {len(bad)} rejected ad(s) — not opened (owner: 有一支被拒先不要开)")
    elif e.get("status") == "ACTIVE":
        opened.append(f"{label}: already ACTIVE")
    elif CONFIRM:
        g2.update_status(sid, "ACTIVE"); opened.append(f"{label}: adset → ACTIVE (CBO RM{int((e.get('campaign') or {}).get('daily_budget') or 0) / 100:.0f})"); time.sleep(0.8)
    else:
        print(f"         plan: adset → ACTIVE")

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。"); print("OPEN ALL DONE (dry-run)"); return
    time.sleep(5.0)
    print("\n── 验证 ──")
    for aid, label in SG_ADS.items():
        show("ad", label, g.get_object(aid, "id,name,status,effective_status,issues_info")); time.sleep(0.4)
    for sid2, label in SG_ADSETS.items():
        show("adset", label, g.get_object(sid2, "id,name,status,effective_status")); time.sleep(0.4)
    show("adset", MY_ADSET[1], g2.get_object(MY_ADSET[0], "id,name,status,effective_status"))
    print("\n开了: " + (" · ".join(opened) or "无"))
    if held:
        print("没开: " + " · ".join(held))
    print("OPEN ALL DONE")


if __name__ == "__main__":
    main()
