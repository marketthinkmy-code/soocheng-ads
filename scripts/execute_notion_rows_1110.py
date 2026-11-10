# -*- coding: utf-8 -*-
"""owner 2026-11-10「approve，照改好的版本建」— write the 5 NEW VIDEO rows into the Notion Content Pipeline DB
(Video 57–61, from scripts/specs_newvideo_1110.json): Title · Type=Video · Brand · Hook (headline) · Caption · Source Link.
Status is left unset (owner preference). Idempotent by Title: an existing row is updated, not duplicated. CONFIRM=true writes."""
from __future__ import annotations

import json
import os

from adbot.clients.notion import NotionClient, rich_text_property, title_property
from adbot.notion_captions import fetch_captions
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
specs = json.load(open(REPO_ROOT / "scripts" / "specs_newvideo_1110.json", encoding="utf-8"))
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
db = s.notion.database_id
n = NotionClient(s.secrets.notion_token)
existing = {}
for p in n.query_database(db):
    t = "".join(x.get("plain_text", "") for x in (p["properties"].get("Title") or {}).get("title", []))
    existing[t.strip()] = p["id"]
for sp in specs:
    props = {"Title": title_property(sp["title"]), "Type": {"select": {"name": "Video"}},
             "Brand": rich_text_property("Stock Bloom"), "Hook": rich_text_property(sp["headline"]),
             "Caption": rich_text_property(sp["caption"]),
             "Source Link": {"url": f"https://drive.google.com/file/d/{sp['drive_src']}/view"}}
    pid = existing.get(sp["title"])
    print(f"  {'更新' if pid else '新建'} «{sp['title']}» · {sp['file']} · 标题 {sp['headline']} · 文案 {len(sp['caption'])} 字")
    if not CONFIRM:
        continue
    if pid:
        n.update_page_properties(pid, props)
    else:
        n._request("POST", "pages", json_body={"parent": {"database_id": db}, "properties": props})
if CONFIRM:
    caps = fetch_captions(n, db)
    for sp in specs:
        c = caps.get(f"video_{sp['n']}")
        ok = c and c["caption"] == sp["caption"] and c["headline"] == sp["headline"] and c["name"] == sp["title"]
        print(f"  回读 video_{sp['n']}: {'✅' if ok else '❌ ' + str(c and (c['name'], len(c['caption'])))}")
        assert ok
print("NOTION ROWS 1110 DONE" + ("" if CONFIRM else " (dry-run)"))
