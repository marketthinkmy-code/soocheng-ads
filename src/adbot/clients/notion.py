"""Thin Notion REST API client — reads the Content Pipeline database for ad copy.

The build pulls vetted copy from Notion (the operator's single source of truth) so it never
depends on the LLM for approved creatives. Read-only: this client only queries the database
and reads page bodies; it never writes. Auth is a Notion internal-integration token
(NOTION_TOKEN); the database must be shared with that integration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"  # stable; supports /databases/{id}/query


class NotionError(RuntimeError):
    def __init__(self, status: int, payload: Dict[str, Any]):
        self.status = status
        self.payload = payload
        msg = (payload or {}).get("message") or str(payload)
        super().__init__(f"[{status}] {msg}")


class _Retryable(Exception):
    """Internal marker for transient failures worth retrying."""


class NotionClient:
    def __init__(self, token: str, *, version: str = NOTION_VERSION,
                 session: Optional[requests.Session] = None, timeout: int = 30):
        self.token = token
        self.version = version
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}",
                "Notion-Version": self.version,
                "Content-Type": "application/json"}

    @retry(reraise=True, stop=stop_after_attempt(4),
           wait=wait_exponential(multiplier=2, min=2, max=20),
           retry=retry_if_exception_type(_Retryable))
    def _request(self, method: str, path: str, *, params: Optional[Dict] = None,
                 json_body: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{API_BASE}/{path.lstrip('/')}"
        try:
            resp = self.session.request(method, url, headers=self._headers(),
                                        params=params, json=json_body, timeout=self.timeout)
        except requests.RequestException as exc:
            raise _Retryable(str(exc)) from exc
        if resp.status_code in (429, 500, 502, 503, 504):
            raise _Retryable(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}
        if resp.status_code >= 400:
            raise NotionError(resp.status_code, payload)
        return payload

    def query_database(self, database_id: str) -> List[Dict[str, Any]]:
        """Return every page (row) in the database, following pagination."""
        out: List[Dict[str, Any]] = []
        body: Dict[str, Any] = {"page_size": 100}
        while True:
            page = self._request("POST", f"databases/{database_id}/query", json_body=body)
            out.extend(page.get("results", []))
            if not page.get("has_more"):
                return out
            body["start_cursor"] = page.get("next_cursor")

    def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Return a block's (or page's) child blocks, following pagination."""
        out: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            page = self._request("GET", f"blocks/{block_id}/children", params=params)
            out.extend(page.get("results", []))
            if not page.get("has_more"):
                return out
            cursor = page.get("next_cursor")

    def update_page_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH a page's properties (needs the integration's 'Update content' capability)."""
        return self._request("PATCH", f"pages/{page_id}", json_body={"properties": properties})


def _chunks(value: str, size: int = 2000) -> List[str]:
    # Notion caps a single rich_text/title text object at 2000 chars; split longer copy.
    return [value[i:i + size] for i in range(0, len(value), size)] or [""]


def title_property(value: str) -> Dict[str, Any]:
    return {"title": [{"text": {"content": c}} for c in _chunks(value)]}


def rich_text_property(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": c}} for c in _chunks(value)]}


def rich_text_to_plain(rich_text: List[Dict[str, Any]]) -> str:
    """Join a Notion rich_text array into a plain string."""
    return "".join(rt.get("plain_text", "") for rt in (rich_text or []))


# Block types whose rich_text we treat as a line of copy (skip media/dividers/etc.).
_TEXT_BLOCK_TYPES = (
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item", "quote", "callout", "to_do",
)


def block_to_line(block: Dict[str, Any]) -> Optional[str]:
    """One text block -> one caption line ('' for an empty paragraph). None to skip."""
    btype = block.get("type")
    if btype not in _TEXT_BLOCK_TYPES:
        return None
    return rich_text_to_plain(block.get(btype, {}).get("rich_text", []))


def page_body_text(notion: NotionClient, page_id: str) -> str:
    """Concatenate a page's text blocks into the caption body (preserving blank lines)."""
    lines: List[str] = []
    for block in notion.get_block_children(page_id):
        line = block_to_line(block)
        if line is not None:
            lines.append(line)
    return "\n".join(lines).strip()
