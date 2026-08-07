"""Read-only: the owner pointed at an EXISTING SG campaign (120248197444090521 on
act_893025326577600) as the template for the MY->SG clone. Resolve it fully (geo /
opt / pixel / ads) so we copy the owner's actual SG settings instead of guessing geo.
Also lists ALL campaigns on BOTH accounts with status so we can settle "6 vs 5". No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

SG = "act_893025326577600"           # [SG] MTC X SB
MY = "act_759339046918885"           # MTC X SB 3.0 (source, MY)
REF_CAMP = "120248197444090521"      # the campaign in the owner's link


def dump_campaign(g, cid: str) -> None:
    c = g.get_object(cid, "id,name,effective_status,objective,daily_budget,"
                          "lifetime_budget,bid_strategy,special_ad_categories,created_time")
    print(f"CAMP {c.get('id')}  {c.get('name')}  [{c.get('effective_status')}]")
    print(f"   objective={c.get('objective')} daily_budget={c.get('daily_budget')} "
          f"bid={c.get('bid_strategy')} cats={c.get('special_ad_categories')} "
          f"created={c.get('created_time')}")
    for aset in g._get_all(f"{cid}/adsets", {
            "fields": "id,name,effective_status,optimization_goal,billing_event,"
                      "promoted_object,daily_budget,start_time,targeting", "limit": "50"}):
        t = aset.get("targeting") or {}
        geo = (t.get("geo_locations") or {}).get("countries")
        cities = (t.get("geo_locations") or {}).get("cities")
        print(f"   ADSET {aset['id']} '{aset.get('name')}' [{aset.get('effective_status')}]")
        print(f"      opt={aset.get('optimization_goal')} bill={aset.get('billing_event')} "
              f"geo={geo} cities={cities} age={t.get('age_min')}-{t.get('age_max')} "
              f"locales={t.get('locales')}")
        print(f"      promoted={aset.get('promoted_object')}")
        for ad in g._get_all(f"{aset['id']}/ads", {
                "fields": "id,name,effective_status,creative{id,object_story_id,"
                          "effective_object_story_id,video_id,image_hash,"
                          "call_to_action_type}", "limit": "50"}):
            cr = ad.get("creative") or {}
            osid = cr.get("effective_object_story_id") or cr.get("object_story_id")
            print(f"      AD '{ad.get('name')}' [{ad.get('effective_status')}]  osid={osid}  "
                  f"vid={cr.get('video_id')} img={cr.get('image_hash')} "
                  f"cta={cr.get('call_to_action_type')}")


def list_camps(g, acct: str, label: str) -> None:
    print("=" * 80)
    print(f"{label} — ALL campaigns on {acct}")
    print("=" * 80)
    camps = g._get_all(f"{acct}/campaigns", {
        "fields": "id,name,effective_status,daily_budget,created_time", "limit": "300"})
    order = {"ACTIVE": 0, "PAUSED": 1}
    camps.sort(key=lambda c: (order.get(c.get("effective_status"), 2),
                              c.get("created_time") or ""))
    n_active = sum(1 for c in camps if c.get("effective_status") == "ACTIVE")
    print(f"{len(camps)} campaigns total · {n_active} ACTIVE\n")
    for c in camps:
        st = c.get("effective_status")
        mark = "▶" if st == "ACTIVE" else " "
        print(f"  {mark} [{st:>8}] {c.get('id')}  bud={c.get('daily_budget')}  "
              f"{c.get('name')}  (created {c.get('created_time')})")
    print()


def main() -> None:
    g = graph_client(load_settings())

    print("#" * 80)
    print(f"# REFERENCE SG CAMPAIGN the owner linked: {REF_CAMP}")
    print("#" * 80)
    try:
        dump_campaign(g, REF_CAMP)
    except Exception as exc:  # noqa: BLE001
        print("  ref campaign read failed:", exc)
    print()

    list_camps(g, SG, "SG DEST")
    list_camps(g, MY, "MY SOURCE")

    print("DONE.")


if __name__ == "__main__":
    main()
