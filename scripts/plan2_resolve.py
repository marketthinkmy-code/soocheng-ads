"""Read-only prep for the revised plan (Luxury Goods / Business Owner / Investment):
  1) resolve real Meta interest ids for the 3 groups, and
  2) rank today+yesterday (2026-07-14..15) ads by RESULTS (COMPLETE_REGISTRATION) per
     market — MY (act_759339046918885) and SG (act_893025326577600) separately — with
     each ad's reusable post id.
No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

GROUPS = {
    "LUXURY GOODS": ["Luxury goods", "Luxury watches", "Rolex", "Jewellery",
                     "Luxury yacht", "Wealth management", "Private banking"],
    "BUSINESS OWNER": ["Small business owners", "Business owner", "Entrepreneurship",
                       "Entrepreneur", "Startup company", "Chief executive officer"],
    "INVESTMENT": ["Investment", "Investment management", "Stock market", "Finance",
                   "Day trading", "Financial planning"],
}
ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]
SINCE, UNTIL = "2026-07-14", "2026-07-15"


def main() -> None:
    g = graph_client(load_settings())

    print("#" * 84)
    print("# INTERESTS")
    print("#" * 84)
    for grp, terms in GROUPS.items():
        print(f"\n=== {grp} ===")
        for t in terms:
            try:
                res = g._request("GET", "search",
                                 params={"type": "adinterest", "q": t, "limit": "2"})
            except Exception as exc:  # noqa: BLE001
                print(f"# {t}: ERR {str(exc)[:60]}")
                continue
            rows = res.get("data", []) or []
            if not rows:
                print(f"# {t}: (no interest)")
                continue
            for it in rows[:1]:
                aud = it.get("audience_size_lower_bound") or it.get("audience_size")
                print(f"   {t:32} id={it.get('id')}  «{it.get('name')}»  ~{aud}")

    print("\n" + "#" * 84)
    print(f"# ADS BY RESULTS · today+yesterday ({SINCE}..{UNTIL}) · per market")
    print("#" * 84)
    token = result_action_type("COMPLETE_REGISTRATION")
    for label, acct in ACCTS:
        try:
            ins = {r.get("ad_id"): r for r in g.account_insights(
                acct, level="ad", fields="ad_id,spend,actions",
                time_range={"since": SINCE, "until": UNTIL})}
            ads = g._get_all(f"{acct}/ads", {
                "fields": "id,name,effective_status,creative{effective_object_story_id,"
                          "object_story_id,image_hash,video_id}", "limit": "400"})
        except Exception as exc:  # noqa: BLE001
            print(f"\n{label} {acct}: read failed {str(exc)[:60]}")
            continue
        rows = []
        for a in ads:
            r = ins.get(a["id"]) or {}
            try:
                spend = float(r.get("spend") or 0)
            except (TypeError, ValueError):
                spend = 0.0
            regs = extract_results(r.get("actions"), token)
            if regs <= 0 and spend <= 0:
                continue
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id")
            kind = "vid" if cr.get("video_id") else ("img" if cr.get("image_hash") else "?")
            rows.append((regs, spend / regs if regs > 0 else None, spend,
                         a.get("name", ""), post, kind, a.get("effective_status")))
        rows.sort(key=lambda x: (-x[0], x[1] if x[1] is not None else 9e9))
        print(f"\n=== {label} ({acct}) — by results ===")
        print("  results  CPL   spend  type [status]  post_id  name")
        for regs, cpl, spend, name, post, kind, st in rows[:10]:
            cpls = f"{cpl:5.1f}" if cpl is not None else "  -  "
            print(f"   {regs:4.0f}   {cpls}  {spend:5.0f}  {kind:>4} [{st:>8}]  {post}  {name[:38]}")
        if not rows:
            print("  (no delivery in this window)")

    print("\nDONE.")


if __name__ == "__main__":
    main()
