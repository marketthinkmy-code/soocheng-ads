"""Owner-authorized pause of the specific waste / runaway-CPL ads flagged 2026-07-10.

Safe by construction:
  * resolves each target by campaign tag + distinctive ad-name substring,
  * EXCLUDES any '[SG]' campaign (the SG twins of the same creative stay untouched),
  * requires EXACTLY ONE match, else skips and prints the candidates (never guesses),
  * only pauses ACTIVE ads,
  * dry-run unless CONFIRM_PAUSE is true — prints what it WOULD do first.
Logs every real pause to pause_log.json. No un-pausing.
"""
from __future__ import annotations

import os

from adbot import state
from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM_PAUSE", "").lower() in ("1", "true", "yes")

# (campaign-name tag [MY only], distinctive ad-name substring, reason, human note)
TARGETS = [
    ("1-1-10", "采访的角度",   "manual_waste_0reg", "Video 2：采访的角度 — 0 reg, still spending"),
    ("1-1-10", "你不是不会赚", "manual_waste_0reg", "Video 9：你不是不会赚 — 0 reg, still spending"),
    ("1-1-9",  "用我的方法",   "manual_high_cpl",   "video 1：用我的方法 — CPL 12→85"),
    ("1-1-10", "是在等死",     "manual_high_cpl",   "Video 8：你的钱放 FD，是在等死 — CPL 11→57"),
]


def _camp(a):
    return (a.get("campaign") or {}).get("name") or ""


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    ads = g._get_all(f"{s.meta.account_path}/ads",
                     {"fields": "id,name,effective_status,campaign{name}", "limit": "400"})
    print(f"CONFIRM_PAUSE={CONFIRM}  ({'LIVE — will pause' if CONFIRM else 'DRY RUN — prints only'})\n")
    paused = 0
    for tag, name_sub, reason, note in TARGETS:
        cands = [a for a in ads if tag in _camp(a) and "[SG]" not in _camp(a)
                 and name_sub in (a.get("name") or "")]
        print(f"── target: campaign~“{tag}” (MY only) · name~“{name_sub}”  [{note}]")
        if len(cands) != 1:
            print(f"   ⚠ matched {len(cands)} ads — SKIP (need exactly 1):")
            for a in cands:
                print(f"     {a['id']} [{a.get('effective_status')}] {_camp(a)} | {a.get('name')}")
            continue
        a = cands[0]
        st = a.get("effective_status")
        print(f"   match: {a['id']} [{st}] {_camp(a)} | {a.get('name')}")
        if st != "ACTIVE":
            print(f"   SKIP — already {st}, nothing to pause")
            continue
        if not CONFIRM:
            print("   WOULD PAUSE (dry-run)")
            continue
        g.update_status(a["id"], "PAUSED")
        after = g.get_object(a["id"], "effective_status").get("effective_status")
        state.append_pause_log(a["id"], "ad", reason, {"note": note})
        print(f"   PAUSED  {st} → {after}")
        paused += 1
    print(f"\nSUMMARY: {'paused ' + str(paused) if CONFIRM else 'dry-run, paused 0'} of {len(TARGETS)} targets.\nDONE.")


if __name__ == "__main__":
    main()
