# -*- coding: utf-8 -*-
"""READ-ONLY audit of PR #93 (owner 2026-11-19「先修好 PR #93，一定要看完 campaign、ad set、ad」).
For every Paid row of the last 60 days: the Paid row's own UTM and every registration of the same person
(Register tab, since 10/29, on/before the purchase date), each checked level by level against the real Meta tree
of MY 5.0 + SG — campaign ✅/❌ → ad set (inside THAT campaign) ✅/❌ → ad (inside THAT ad set) ✅/❌ — with the
Meta ad id it lands on. Also flags any key that lands on more than one Meta ad. No PII (row number, date, Source, UTM only)."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import re

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

loose = lambda a: re.sub(r"[\W_]+", "", re.sub(r"^(?:single\s*image|image|video)\s*\d*\s*[：:]\s*", "", cpa.norm(a)))
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
CUT, SINCE = TODAY - dt.timedelta(days=60), dt.date(2026, 10, 29)
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
paid_v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
reg_v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.register_tab)

# ---- Meta tree: campaign key -> ad set key -> ad key -> [ads]
tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
exact_ix = defaultdict(list)
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,adset{name},campaign{name}", "limit": "500"}):
        rec = (label, a["campaign"]["name"], a["adset"]["name"], a["name"], a["id"], a["effective_status"])
        tree[_mkey(a["campaign"]["name"])][_mkey(a["adset"]["name"])][loose(a["name"])].append(rec)
        exact_ix[(_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"]))].append(rec)


def check(c, s, a):
    """Strict (what the monitor uses): campaign AND ad set AND exact ad name."""
    ck, sk, ak = _mkey(cpa.norm(c)), _mkey(cpa.norm(s)), cpa.norm(a)
    if not c.strip():
        return "（无 UTM）", []
    if ck not in tree:
        return "campaign ❌", []
    if sk not in tree[ck]:
        return "campaign ✅ · ad set ❌", []
    hits = exact_ix.get((ck, sk, ak), [])
    if not hits:
        near = tree[ck][sk].get(loose(a), [])
        return "campaign ✅ · ad set ✅ · ad ❌" + (f"（名字只是相近：{near[0][3]} · ad {near[0][4]}，不算）" if near else ""), []
    return "campaign ✅ · ad set ✅ · ad ✅" + (f" ⚠️ 落在 {len(hits)} 支 ad" if len(hits) > 1 else ""), hits


hi, cols = cpa._sales_header(paid_v)
pk = [cpa._hkey(h) for h in paid_v[hi]]
pe, pp, psrc = cpa._col(pk, "email"), cpa._col(pk, "phonenumber", "phone"), cpa._col(pk, "source")
cell = lambda r, i: r[i] if 0 <= i < len(r) else ""
rk, rrows = cpa._named_table(reg_v, "utmcampaign")
rd, rc = cpa._col(rk, "createddate", "date"), cpa._col(rk, "utmcampaign")
rs, ra = cpa._col(rk, "utmadsset", "utmadset"), cpa._col(rk, "utmadsname", "utmadname")
re_, rp = cpa._col(rk, "email"), cpa._col(rk, "phonenumber", "phone")
regs_by_person = defaultdict(list)
for r in rrows:
    d = cpa.parse_date(cell(r, rd))
    if d and d >= SINCE and cell(r, rc).strip():
        for k in cpa.contact_keys(cell(r, re_), cell(r, rp)):
            regs_by_person[k].append((d, cell(r, rc), cell(r, rs), cell(r, ra)))

credited = defaultdict(set)   # ad id -> paid row numbers (PR #93 logic)
n_rows = n_reg = 0
print(f"今天 {TODAY} · Paid 60 天窗口 > {CUT} · 报名表从 {SINCE} 起")
for rid, r in enumerate(paid_v[hi + 1:]):
    d = cpa.parse_date(cell(r, cols.get("date", -1)))
    if not d or d <= CUT:
        continue
    n_rows += 1
    pc, ps, pa = (cell(r, cols.get(x, -1)) for x in ("campaign", "adset", "ad"))
    v, hits = check(pc, ps, pa)
    for h in hits:
        credited[h[4]].add(rid)
    regs = sorted({x for k in cpa.contact_keys(cell(r, pe), cell(r, pp)) for x in regs_by_person.get(k, []) if x[0] <= d})
    if not hits and not regs:
        continue
    print(f"\n● Paid 第 {rid + 1} 行 · {d} · Source {cell(r, psrc) or '—'}")
    print(f"   Paid 自带 UTM: {pc or '—'} › {ps or '—'} · {pa or '—'}  →  {v}" + "".join(f"\n        = {h[0]} {h[1]} › {h[2]} · {h[3]} · ad {h[4]} ({h[5]})" for h in hits))
    for i, (rdte, c, s_, a) in enumerate(regs):
        v2, hits2 = check(c, s_, a)
        is_last = i == len(regs) - 1
        last = " ← 最后一次报名（只算这一次）" if is_last else " （之前的报名，不算）"
        print(f"   报名 {rdte}: {c} › {s_ or '—'} · {a or '—'}  →  {v2}{last}"
              + "".join(f"\n        = {h[0]} {h[1]} › {h[2]} · {h[3]} · ad {h[4]} ({h[5]})" for h in hits2))
        if is_last:
            for h in hits2:
                credited[h[4]].add(rid)
            n_reg += bool(hits2)
print(f"\n60 天 Paid 行 {n_rows}；三层都对上的报名记录 {n_reg}")
print("\n== PR #93 逻辑下每支 ad 认到的 Paid 行:")
allads = {h[4]: h for k1 in tree.values() for k2 in k1.values() for hs in k2.values() for h in hs}
for aid, rows in sorted(credited.items(), key=lambda x: allads[x[0]][1]):
    h = allads[aid]
    print(f"   {h[0]} {h[1]} › {h[2]} · {h[3]} · ad {aid} ({h[5]}) · {len(rows)} 单 · Paid 行 {sorted(x + 1 for x in rows)}")
dup = [(k0, k1, k2, hs) for k0, v1 in tree.items() for k1, v2 in v1.items() for k2, hs in v2.items() if len(hs) > 1]
print(f"\n== 同一个 campaign+ad set 里名字对得上不止一支 ad 的 key: {len(dup)}")
for k0, k1, k2, hs in dup[:20]:
    print("   " + " | ".join(f"{h[0]} {h[1]} › {h[2]} · {h[3]} · ad {h[4]} ({h[5]})" for h in hs))
print("\nPR93 AUDIT DONE (read-only)")
