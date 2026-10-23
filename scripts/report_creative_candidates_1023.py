# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-23: owner「stock bloom 还有什么广告适合跑的吗？可以 scale 的吗？」
Every creative in the Paid Student List (sales by creative over 180d / 90d / 30d, last sale), flagged:
⛔ banned (compliance gate) · ▶ running now in a Webinarkit campaign (MY 5.0 / SG) · asset found in SG / MY 3.0
(an ad by that creative name, any status — so we can reuse its video/image without re-upload) + its format.
No PII."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter, defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()


def main() -> None:
    sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    vals = SheetsClient(sg.secrets.google_sa_json).read_tab(sg.cpa.spreadsheet_id, sg.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(vals, 2399.0)
    by = defaultdict(lambda: {"180": 0, "90": 0, "30": 0, "last": None, "sg": 0, "my": 0})
    for x in sales:
        if not x.date or not x.ad:
            continue
        age = (TODAY - x.date).days
        if age > 180:
            continue
        k = cpa.creative_key(x.ad)
        r = by[k]
        r["180"] += 1
        r["90"] += age <= 90
        r["30"] += age <= 30
        r["last"] = max(r["last"] or x.date, x.date)
        r["sg" if "[sg]" in (x.campaign or "") else "my"] += 1
    running, assets = set(), defaultdict(set)
    for label, cfg in (("SG", "config.sg.yaml"), ("MY5", "config.my5.yaml"), ("MY3", "config.yaml")):
        st = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(st)
        try:
            ads = g._get_all(st.meta.account_path + "/ads", {"fields": "name,effective_status,campaign{name},creative{object_type,video_id,image_hash}", "limit": "500"})
        except Exception as exc:                                         # noqa: BLE001
            print(f"  {label}: can't list ads ({str(exc)[:80]})"); continue
        for a in ads:
            k = cpa.creative_key(a.get("name"))
            cr = a.get("creative") or {}
            fmt = "video" if cr.get("video_id") else ("image" if cr.get("image_hash") else (cr.get("object_type") or "?").lower())
            assets[k].add(f"{label}:{fmt}")
            if a.get("effective_status") == "ACTIVE" and "webinarkit" in ((a.get("campaign") or {}).get("name") or "").lower():
                running.add(k)
        time.sleep(1)
    banned = sg.compliance.banned_creatives
    print(f"{'素材':<40} {'180d':>4} {'90d':>4} {'30d':>4} {'SG/MY':>6} {'最后成交':>10}  状态 · 素材在哪")
    for k, r in sorted(by.items(), key=lambda kv: (-kv[1]["90"], -kv[1]["180"])):
        tag = "⛔禁" if compliance.is_banned(k, banned) or "🚫" in k else ("▶在跑" if k in running else "可用?")
        print(f"{k[:40]:<40} {r['180']:>4} {r['90']:>4} {r['30']:>4} {r['sg']:>3}/{r['my']:<2} {str(r['last']):>10}  {tag} · {','.join(sorted(assets.get(k, []))) or '—找不到'}")
    print("\nCANDIDATES DONE (read-only)")


if __name__ == "__main__":
    main()
