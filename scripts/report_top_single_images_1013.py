# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-13「去 study 我的 paid student list…给我 top 2 单图广告」.

Paid Student List → every paid enrolment's utm_ad name → keep the SINGLE-IMAGE ads → rank by paid
enrolments (lifetime / 90d / 30d) and revenue, SG vs MY split, where each sold (utm_campaign / adset).
Ban gate = adbot.compliance against the union of every config's banned_creatives (+ 🚫 mark).
Then every Meta ad carrying those images in SG / MY 5.0 / MY 3.0 (disabled, read-only) / MY 2
(disabled, read-only): status, review state, post id for reuse, lifetime spend → CPA.
Prints ad / campaign names, dates, counts and RM only — no buyer PII."""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections import Counter, defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

ACCOUNTS = (("SG", "act_893025326577600"), ("MY 5.0", "act_2285351942292267"),
            ("MY 3.0 封", "act_759339046918885"), ("MY 2 封", "act_2282909119125229"))
EDITION = ("hook：", "hook:", "重拍：", "重拍:", "拼接：", "拼接:")
IMG_RE = re.compile(r"^(single\s*image|singleimage|image|单图|静态图|图片)\s*\d*\s*[：:\-]?\s*", re.I)
TOP_META = 8


def strip_prefix(name: str) -> str:
    s = (name or "").replace("🌟", "").replace("🚫", "").strip()
    changed = True
    while changed:
        changed = False
        for p in EDITION:
            if s.casefold().startswith(p):
                s, changed = s[len(p):].strip(), True
    return s


def fmt_of(name: str) -> str:
    s = strip_prefix(name).casefold()
    if s.startswith("video") or "freestyle" in s or s.startswith("m2video") or "视频" in s:
        return "video"
    if "carousel" in s or "轮播" in s:
        return "carousel"
    if IMG_RE.match(s) or "single image" in s or "单图" in s:
        return "image"
    return "?"


def descriptor(name: str) -> str:
    s = strip_prefix(name)
    m = IMG_RE.match(s)
    d = s[m.end():].strip() if m else s
    return d or s


def gkey(name: str) -> str:
    return compliance.norm_key(descriptor(name))


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    banned = set()
    for cfg in ("config.yaml", "config.sg.yaml", "config.my5.yaml"):
        banned.update(load_settings(REPO_ROOT / "config" / cfg).compliance.banned_creatives or [])
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, cols, header = cpa.parse_sales(vals, 2399.0)
    hidx = next((i for i, r in enumerate(vals[:8]) if r == header), 0)
    raw = defaultdict(Counter)                       # norm(ad) -> raw spellings
    ai = cols.get("ad", -1)
    for row in vals[hidx + 1:]:
        if 0 <= ai < len(row) and (row[ai] or "").strip():
            raw[cpa.norm(row[ai])][row[ai].strip()] += 1

    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    dated = [x.date for x in sales if x.date]
    with_ad = [x for x in sales if x.ad]
    print(f"═══ Paid Student List：{len(sales)} 笔付费 · 有 utm_ad 的 {len(with_ad)} 笔 · "
          f"日期 {min(dated) if dated else '?'} → {max(dated) if dated else '?'}（今天 {today}）═══")
    fmt_n, fmt_rev = Counter(), Counter()
    for x in with_ad:
        f = fmt_of(x.ad); fmt_n[f] += 1; fmt_rev[f] += x.amount
    print("  格式拆分：" + " · ".join(f"{k} {fmt_n[k]} 笔 RM{fmt_rev[k]:,.0f}" for k in ("video", "image", "carousel", "?")))

    groups = defaultdict(list)
    for x in with_ad:
        if fmt_of(x.ad) == "image":
            groups[gkey(x.ad)].append(x)

    def disp(k):
        names = Counter()
        for x in groups[k]:
            names.update(raw.get(x.ad) or Counter({x.ad: 1}))
        return names

    ranked = sorted(groups, key=lambda k: (-len(groups[k]), -sum(x.amount for x in groups[k])))
    print(f"\n═══ 单图广告排名（按付费人数）— {len(ranked)} 个单图素材 ═══")
    print(f"{'#':>2} {'付费':>4} {'收入RM':>9} {'90d':>4} {'30d':>4} {'SG':>3} {'MY':>3}  {'首单 → 末单':<23} 素材")
    for i, k in enumerate(ranked, 1):
        xs = groups[k]
        n90 = sum(1 for x in xs if x.date and x.date > today - dt.timedelta(days=90))
        n30 = sum(1 for x in xs if x.date and x.date > today - dt.timedelta(days=30))
        sg = sum(1 for x in xs if "[sg]" in (x.campaign or ""))
        ds = sorted(x.date for x in xs if x.date)
        names = disp(k)
        top_name = names.most_common(1)[0][0]
        reason = None
        for nm in names:
            reason = reason or compliance.banned_reason(nm, banned)
        flag = f"  ⛔禁跑（{reason}）" if reason else ""
        span = f"{ds[0]} → {ds[-1]}" if ds else "无日期"
        print(f"{i:>2} {len(xs):>4} {sum(x.amount for x in xs):>9,.0f} {n90:>4} {n30:>4} {sg:>3} {len(xs) - sg:>3}  {span:<23} {top_name[:46]}{flag}")
        if i <= TOP_META:
            print(f"      写法: {' | '.join(f'{n[:34]}×{c}' for n, c in names.most_common(4))}")
            camp = Counter(x.campaign for x in xs)
            print(f"      成交 campaign: {' · '.join(f'{c[:40]}×{n}' for c, n in camp.most_common(4))}")
            adset = Counter(x.adset for x in xs if x.adset)
            if adset:
                print(f"      成交 ad set: {' · '.join(f'{c[:30]}×{n}' for c, n in adset.most_common(3))}")
            months = Counter(x.date.strftime('%Y-%m') for x in xs if x.date)
            print(f"      按月: {' · '.join(f'{m} {n}' for m, n in sorted(months.items()))}")

    other = Counter(x.ad for x in with_ad if fmt_of(x.ad) == "?")
    print(f"\n═══ 格式没认出来的 utm_ad（前 20，核对有没有单图漏掉）═══")
    for nm, n in other.most_common(20):
        print(f"  {n:>3}  {nm[:70]}")

    top_keys = ranked[:TOP_META]
    g = graph_client(s)
    spend_by = defaultdict(float)
    seen_accounts, failed = [], []
    print(f"\n═══ Meta 里带前 {TOP_META} 名单图的 ad（SG / MY 5.0 / MY 3.0 封 / MY 2 封）═══")
    for label, acct in ACCOUNTS:
        try:
            time.sleep(1.2)
            ads = g._get_all(acct + "/ads", {
                "fields": "id,name,status,effective_status,created_time,campaign{name},"
                          "creative{id,effective_object_story_id,object_story_id},ad_review_feedback",
                "limit": "500"})
            time.sleep(1.2)
            try:
                ins = g.account_insights(acct, level="ad", fields="ad_id,ad_name,spend", date_preset="maximum")
            except Exception as exc:                             # noqa: BLE001
                ins = []
                failed.append(f"{label} spend: {str(exc)[:80]}")
            sp = {r.get("ad_id"): float(r.get("spend") or 0) for r in ins}
            seen_accounts.append(label)
        except Exception as exc:                                 # noqa: BLE001
            failed.append(f"{label}: {str(exc)[:100]}")
            print(f"  ❌ {label} 读不到：{str(exc)[:120]}")
            continue
        img_ads = [a for a in ads if fmt_of(a.get("name") or "") == "image"]
        for a in img_ads:
            spend_by[gkey(a.get("name") or "")] += sp.get(a["id"], 0.0)
        hits = [a for a in img_ads if gkey(a.get("name") or "") in top_keys]
        print(f"\n  ── {label}：{len(ads)} 支 ad · 单图 {len(img_ads)} 支 · 前 {TOP_META} 名素材 {len(hits)} 支 ──")
        hits.sort(key=lambda a: (top_keys.index(gkey(a.get("name") or "")), -(sp.get(a["id"], 0.0))))
        for a in hits[:40]:
            k = gkey(a.get("name") or "")
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id") or "—"
            fb = a.get("ad_review_feedback") or {}
            fb_s = (" 审核:" + json.dumps(fb, ensure_ascii=False)[:110]) if fb else ""
            print(f"   #{top_keys.index(k) + 1} «{(a.get('name') or '')[:34]}» {a.get('status')}/{a.get('effective_status')} "
                  f"created {(a.get('created_time') or '')[:10]} spend RM{sp.get(a['id'], 0.0):,.0f} "
                  f"@ {((a.get('campaign') or {}).get('name') or '')[:34]} · post {post}{fb_s}")

    print(f"\n═══ 前 {TOP_META} 名单图：lifetime spend / 付费 / CPA（读到的账户：{', '.join(seen_accounts)}）═══")
    for i, k in enumerate(top_keys, 1):
        n = len(groups[k]); rev = sum(x.amount for x in groups[k]); spd = spend_by.get(k, 0.0)
        cpa_s = f"CPA RM{spd / n:,.0f}" if spd and n else "CPA —（没读到花费）"
        roas = f"ROAS {rev / spd:.1f}x" if spd else ""
        print(f"  #{i} {disp(k).most_common(1)[0][0][:40]:<40} 花费 RM{spd:>9,.0f} · 付费 {n} · {cpa_s} {roas}")
    if failed:
        print("  ⚠️ 没读全：" + " | ".join(failed))
    print("\nTOP SINGLE IMAGES DONE (read-only)")


if __name__ == "__main__":
    main()
