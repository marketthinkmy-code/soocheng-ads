"""Permanent creative ban list — the hard gate added after the SECOND account ban.

Owner 2026-09-23, after MTC X SB 3.0 was disabled (`disable_reason=1`,
ADS_INTEGRITY_POLICY — the same code that killed the previous account in July):

    「list out all those rejected ads for me, and write a rule that not to advertise
     these ads anymore (even tho the ads are running well and had good cpa before)」

So this module answers ONE question — *has this creative ever been rejected?* — and
that answer outranks every CPL/CPA rule in the codebase. A banned creative is banned
as a **master asset**: renaming the ad, rewriting the caption, reusing the post,
moving accounts or re-uploading the file are all the same creative. Only a genuinely
re-cut clean master (a new file, with the violating lines removed) may run, and it
enters as a new creative — the original stays banned forever.

Matching is deliberately loose (casefold, drop 🌟 and ALL whitespace, then substring)
because the same footage ships under many ad names: «拼接：Video 5：Trading 早就不是
这样了！» and «video 5：trading 早就不是这样了！» are one master.
"""
from __future__ import annotations

from typing import Iterable, List, Optional


def norm_key(name: str) -> str:
    """Casefold, strip the 🌟 sold-chain marker, and remove every space.

    Whitespace removal is what makes CJK matching reliable: Meta ad names vary
    between «1 分钟赚 300» and «1分钟赚300» for the same video.
    """
    s = (name or "").replace("🌟", "").replace("\\", "")
    return "".join(s.split()).casefold()


def banned_reason(name: str, banned: Iterable[str]) -> Optional[str]:
    """The ban-list entry this ad name matches, or None when it is clean."""
    key = norm_key(name)
    if not key:
        return None
    for entry in banned or ():
        token = norm_key(entry)
        if token and token in key:
            return entry
    return None


def is_banned(name: str, banned: Iterable[str]) -> bool:
    """True when this ad/creative name matches a permanently banned master asset."""
    return banned_reason(name, banned) is not None


def filter_banned(names: Iterable[str], banned: Iterable[str]) -> List[tuple]:
    """[(name, matched_entry), ...] for every name that is banned — for build guards."""
    out = []
    for n in names:
        hit = banned_reason(n, banned)
        if hit:
            out.append((n, hit))
    return out
