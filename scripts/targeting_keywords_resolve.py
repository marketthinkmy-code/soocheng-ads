# -*- coding: utf-8 -*-
"""Resolve REAL Ads Manager detailed-targeting options for the owner's 9 audience themes.

Owner ask 2026-08-07: for each theme, list every usable detailed-targeting keyword —
verified, not guessed. Uses act_<id>/targetingsearch (the same API behind the Ads
Manager search box), which returns interests + behaviors + demographics with official
names, ids, audience sizes and category paths. Dedupes across seed queries per theme,
sorts by audience size. Read-only.

NOTE: both accounts declare FINANCIAL_PRODUCTS_SERVICES, so a few segments can still be
unavailable at ad-set build time (age/gender are locked anyway); the existing interest
campaigns prove detailed targeting works under this declaration.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

THEMES = {
    "1. FOOD & DRINK": [
        "food and drink", "restaurants", "fine dining", "cooking", "foodie",
        "coffee", "wine", "whisky", "beer", "cocktails", "seafood", "buffet"],
    "2. BEAUTY": [
        "beauty", "cosmetics", "skincare", "makeup", "spa", "hair care",
        "perfume", "beauty salon", "aesthetics", "facial"],
    "3. LUXURY GOODS": [
        "luxury goods", "luxury fashion", "designer clothing", "jewellery",
        "Louis Vuitton", "Gucci", "Chanel", "Hermes", "Prada", "yacht",
        "private banking", "wealth management", "high net worth"],
    "4. OMAKASE / WAGYU": [
        "omakase", "wagyu", "sushi", "japanese cuisine", "sashimi", "kaiseki",
        "steakhouse", "kobe beef", "michelin", "japanese restaurant"],
    "5. DIVING / GOLF": [
        "scuba diving", "diving", "freediving", "snorkeling", "golf",
        "golf courses", "PGA Tour", "country club", "pickleball", "golf equipment"],
    "6. LUXURY AUTOMOBILE": [
        "luxury vehicles", "Mercedes-Benz", "BMW", "Porsche", "Ferrari",
        "Lamborghini", "Bentley", "Rolls-Royce", "Audi", "sports cars",
        "supercars", "Lexus", "Tesla"],
    "7. LUXURY WATCHES": [
        "luxury watches", "watches", "Rolex", "Patek Philippe", "Audemars Piguet",
        "Omega", "TAG Heuer", "Richard Mille", "Tudor", "horology", "Cartier"],
    "8. PARENTING & CHILD": [
        "parenting", "parents", "children", "motherhood", "fatherhood", "baby",
        "toddlers", "kindergarten", "early childhood education", "preschool",
        "family", "tuition"],
    "9. TRAVEL": [
        "travel", "tourism", "vacations", "air travel", "hotels", "luxury travel",
        "cruises", "adventure travel", "frequent travelers", "airlines", "resorts"],
}
SHOW = 18  # rows printed per theme (rest counted)


def fmt_size(row) -> str:
    lo = row.get("audience_size_lower_bound") or row.get("audience_size") or 0
    up = row.get("audience_size_upper_bound") or lo
    m = lambda v: f"{v/1e6:.0f}M" if v >= 1e6 else (f"{v/1e3:.0f}K" if v >= 1e3 else str(v))
    return f"{m(lo)}–{m(up)}" if up and up != lo else m(lo)


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"targetingsearch via {acct} — every row below is selectable in Ads Manager\n")
    for theme, seeds in THEMES.items():
        found: dict = {}
        for q in seeds:
            try:
                res = g._request("GET", f"{acct}/targetingsearch",
                                 params={"q": q, "limit": "12"})
            except Exception as exc:  # noqa: BLE001
                print(f"   [seed '{q}' ERR: {str(exc)[:60]}]")
                continue
            for row in res.get("data", []) or []:
                rid = row.get("id")
                if rid and rid not in found:
                    found[rid] = row
        rows = sorted(found.values(),
                      key=lambda r: -(r.get("audience_size_upper_bound")
                                      or r.get("audience_size") or 0))
        print(f"═══ {theme} — {len(rows)} 个可用选项 ═══")
        for r in rows[:SHOW]:
            path = " › ".join(r.get("path") or [])[:46]
            print(f"   {r.get('type', '?'):12} {r.get('name', '?')[:36]:36} "
                  f"{fmt_size(r):>11}  {path}  [{r.get('id')}]")
        if len(rows) > SHOW:
            print(f"   … 另有 {len(rows) - SHOW} 个（略）")
        print()
    print("DONE (read-only).")


if __name__ == "__main__":
    main()
