# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-22「為什麼今天 SG 的都沒有 leads？」— live today-only
diagnosis, SG + MY contrast:

  per running ad: TODAY spend + registrations (exact Results bucket) + status;
  account totals; ads spending with zero regs vs ads not spending at all;
  landing-page reachability probe from the runner (both accounts share the LP —
  if money burns account-wide with 0 regs, suspect LP/pixel, not creatives)."""
from __future__ import annotations

import datetime as dt
import time

import requests

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings


def main() -> None:
    today = ((dt.datetime.utcnow() + dt.timedelta(hours=8)).date()).isoformat()
    rng = {"since": today, "until": today}

    try:
        t0 = time.time()
        r = requests.get("https://soochenginvesting.com/", timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        print(f"LP 探测: HTTP {r.status_code} · {time.time() - t0:.1f}s · {len(r.content)} bytes"
              f" · pixel 片段{'✓' if 'fbq(' in r.text or 'facebook' in r.text.lower() else '✗ 页面里没看到'}")
    except Exception as e:  # noqa: BLE001
        print(f"LP 探测: ❌ 打不开 — {type(e).__name__}: {str(e)[:120]}")
    print()

    for label, cfg in (("SG", "config.sg.yaml"), ("MY", "config.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        token = result_action_type(s.meta.conversion_event)
        ads = g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "id,name,effective_status,campaign{name},"
                       "adset{name,promoted_object}", "limit": "500"})
        time.sleep(1.2)
        ins = {r0.get("ad_id"): r0 for r0 in g.account_insights(
            s.meta.account_path, level="ad", fields="ad_id,spend,actions",
            time_range=rng)}
        time.sleep(1.2)

        rows, tot_sp, tot_rg = [], 0.0, 0.0
        idle = []
        for a in ads:
            ev = ((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type")
            if (ev or "").upper() != "COMPLETE_REGISTRATION":
                continue
            live = a.get("effective_status") == "ACTIVE"
            r0 = ins.get(a["id"]) or {}
            sp = float(r0.get("spend") or 0)
            rg = extract_results(r0.get("actions"), token)
            if not live and sp <= 0:
                continue
            tot_sp += sp
            tot_rg += rg
            if live and sp <= 0:
                idle.append(a)
                continue
            rows.append((sp, rg, a))
        rows.sort(key=lambda x: -x[0])
        cpl = f"RM{tot_sp / tot_rg:.0f}" if tot_rg else "∞"
        print(f"═══ [{label}] 今天（{today}）花 RM{tot_sp:,.0f} · {tot_rg:.0f} regs · CPL {cpl} ═══")
        for sp, rg, a in rows:
            mark = "✅" if rg else ("🕳" if sp > 0 else "·")
            st_e = a.get("effective_status")
            flag = "" if st_e == "ACTIVE" else f" [{st_e}]"
            print(f"  {mark} RM{sp:>6.0f} / {rg:.0f} regs  «{(a.get('name') or '')[:32]}»"
                  f" @ «{((a.get('campaign') or {}).get('name') or '')[:28]}»{flag}")
        if idle:
            print(f"  —— 开着但今天 0 花费（{len(idle)} 支，投不出去/刚开）——")
            for a in idle[:12]:
                print(f"  ⚠ RM0  «{(a.get('name') or '')[:32]}» @ "
                      f"«{((a.get('campaign') or {}).get('name') or '')[:28]}» [{a.get('effective_status')}]")
        print()
    print("TODAY DIAG DONE (read-only)")


if __name__ == "__main__":
    main()
