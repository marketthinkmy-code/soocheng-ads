# -*- coding: utf-8 -*-
"""READ-ONLY (owner 10/30「先看完 paid student list，对回电话，65 开头 = 新加坡学生，看看新加坡报名最多的 top 3 ad set」).
No PII printed. 1) which tab is gid 1805763216. 2) Paid rows whose phone starts with 65 → group by UTM ad set (from the paid
row; if blank, from that person's Register rows — earliest and latest, matched by phone/email). 3) For context: Register rows
with +65 phones by UTM ad set."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

GID = 1805763216
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s.secrets.google_sa_json)
meta = sc._svc.spreadsheets().get(spreadsheetId=s.cpa.spreadsheet_id, fields="sheets.properties(sheetId,title)").execute()
tabs = {p["properties"]["sheetId"]: p["properties"]["title"] for p in meta["sheets"]}
tab = tabs.get(GID)
print(f"gid {GID} = «{tab}»  （全部分页: {list(tabs.values())}）")

digits = lambda v: re.sub(r"\D", "", v or "")
em = lambda v: (v or "").strip().lower()
is_sg = lambda p: digits(p).startswith("65")


def table(vals):
    hi = next(i for i, r in enumerate(vals[:8]) if any("UTM" in c for c in r))
    h = vals[hi]
    return h, [dict(zip(h, r)) for r in vals[hi + 1:] if any(x.strip() for x in r)]


def col(h, *keys):
    return next((c for c in h if all(k.lower() in c.lower() for k in keys)), None)


ph, paid = table(sc.read_tab(s.cpa.spreadsheet_id, tab))
rh, reg = table(sc.read_tab(s.cpa.spreadsheet_id, "Register"))
P = {k: col(ph, *v) for k, v in {"phone": ("phone",), "email": ("email",), "camp": ("utm", "campaign"), "set": ("utm", "set"),
                                    "ad": ("utm", "name"), "date": ("date",), "amt": ("amount",)}.items()}
R = {k: col(rh, *v) for k, v in {"phone": ("phone",), "email": ("email",), "camp": ("utm", "campaign"), "set": ("utm", "set"),
                                    "ad": ("utm", "name"), "date": ("created",), "src": ("source",)}.items()}
print("Paid 栏位对应:", P, "\nRegister 栏位对应:", R)
idx = defaultdict(list)
for r in reg:
    for k in (digits(r.get(R["phone"]))[-8:], em(r.get(R["email"]))):
        if k:
            idx[k].append(r)

sg_paid = [r for r in paid if is_sg(r.get(P["phone"]))]
print(f"\nPaid 共 {len(paid)} 行 · 65 开头 {len(sg_paid)} 行")
by_set, from_where, detail = Counter(), Counter(), defaultdict(lambda: {"camp": Counter(), "ad": Counter(), "dates": []})
for r in sg_paid:
    st, cp, ad, src = (r.get(P["set"]) or "").strip(), (r.get(P["camp"]) or "").strip(), (r.get(P["ad"]) or "").strip(), "paid 表"
    if not st:
        hits = idx.get(digits(r.get(P["phone"]))[-8:]) or idx.get(em(r.get(P["email"]))) or []
        hits = [h for h in hits if (h.get(R["set"]) or "").strip()]
        if hits:
            h = hits[0]
            st, cp, ad, src = h[R["set"]].strip(), (h.get(R["camp"]) or "").strip(), (h.get(R["ad"]) or "").strip(), "Register 第一笔"
        else:
            st, src = "(无 UTM)", "无"
    from_where[src] += 1
    by_set[st] += 1
    d = detail[st]
    d["camp"][cp[:60]] += 1; d["ad"][ad[:40]] += 1; d["dates"].append((r.get(P["date"]) or "")[:10])
print("UTM 来源:", dict(from_where))
print("\n新加坡学生（65 开头）· 按 ad set 排名:")
for st, n in by_set.most_common(12):
    d = detail[st]
    print(f"\n  {n:>3}  ad set «{st[:60]}»")
    print(f"       campaign: {'; '.join(f'{c} ×{k}' for c, k in d['camp'].most_common(3))}")
    print(f"       ad: {'; '.join(f'{c} ×{k}' for c, k in d['ad'].most_common(4))}")
    print(f"       成交日期: {', '.join(sorted(x for x in d['dates'] if x))[:120]}")

reg_sg = Counter((r.get(R["set"]) or "(无 UTM)").strip()[:60] for r in reg if is_sg(r.get(R["phone"])))
print(f"\n参考：Register 表 65 开头的报名 {sum(reg_sg.values())} 行 · 按 ad set 前 8:")
for st, n in reg_sg.most_common(8):
    print(f"   {n:>4}  {st}")
print("\nSG PAID ADSETS DONE (read-only)")
