"""Read-only monitor-coverage report. For both accounts —
  MY 3.0  act_759339046918885   (swept by adbot-monitor.yml)
  SG      act_893025326577600   (swept by adbot-monitor-sg.yml)
list every ACTIVE campaign and, per campaign, how many ACTIVE ads are optimized for
COMPLETE_REGISTRATION (= exactly what the hourly CPL monitor evaluates). Confirms which
active campaigns are in monitor scope. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

ACCTS = [("MY 3.0", "act_759339046918885"), ("SG", "act_893025326577600")]
WANT = "COMPLETE_REGISTRATION"


def main() -> None:
    g = graph_client(load_settings())
    for label, acct in ACCTS:
        camps = g._get_all(f"{acct}/campaigns",
                           {"fields": "id,name,effective_status", "limit": "400"})
        active = [c for c in camps if c.get("effective_status") == "ACTIVE"]
        print(f"\n{'='*72}")
        print(f"{label}  {acct}  —  {len(active)} ACTIVE campaigns (of {len(camps)} total)")
        print('='*72)
        tot_reg = 0
        for c in sorted(active, key=lambda x: x.get("name", "")):
            ads = g._get_all(f"{c['id']}/ads",
                             {"fields": "id,effective_status,adset{promoted_object}",
                              "limit": "200"})
            act_ads = [a for a in ads if a.get("effective_status") == "ACTIVE"]
            reg = [a for a in act_ads
                   if (((a.get("adset") or {}).get("promoted_object") or {})
                       .get("custom_event_type", "").upper() == WANT)]
            tot_reg += len(reg)
            flag = "✓ monitored" if reg else "—  no active reg-ad"
            print(f"  {len(reg):2d} reg-ad  {flag:20}  {c.get('name','')[:50]}")
        print(f"  → {label}: {len(active)} active campaigns · "
              f"{tot_reg} active COMPLETE_REGISTRATION ads in monitor scope")
    print("\nDONE.")


if __name__ == "__main__":
    main()
