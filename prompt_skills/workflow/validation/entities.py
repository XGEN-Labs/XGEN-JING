"""Conservative distinction between internal labels and explicit physical codes."""

import re

# An explicit physical noun is required; quotations alone never exempt a label.
# Parenthesized tags remain internal labels, even after a physical noun.
PHYSICAL_PREFIX_RE = re.compile(
    r"(?:\b(?:rack|cabinet|room|gate|platform|shelf|locker|seat)\s+"
    r"|(?:机架|机柜|房间|房号|登机口|站台|货架|储物柜|座位)\s*)$",
    re.IGNORECASE,
)
PHYSICAL_SUFFIX_RE = re.compile(
    r"^[”\"’\']?\s*(?:(?:号)?(?:机架|机柜|房间|登机口|站台|货架|储物柜|座位)"
    r"|(?:boarding\s+)?(?:gate|room|rack|cabinet|platform|shelf|locker|seat)\b)",
    re.IGNORECASE,
)


def is_physical_identifier(text: str, match: re.Match, context: str = "") -> bool:
    """Only unbracketed B/O codes with explicit physical context are exempt."""
    if not match.group().startswith(("B", "O")):
        return False
    before, after = text[: match.start()], text[match.end() :]
    if before.rstrip().endswith(("(", "（", "[", "【")) or after.lstrip().startswith(
        (")", "）", "]", "】")
    ):
        return False
    if PHYSICAL_PREFIX_RE.search(before) or PHYSICAL_SUFFIX_RE.match(after):
        return True
    # Short destination references are valid only if this exact code is explicitly
    # bound to a physical noun elsewhere in the same case (never another case).
    destination = re.search(
        r"(?:前往|到达|走向|抵达|靠近|\b(?:towards?|to|at))\s*$", before, re.I
    )
    entrance = re.match(
        r"^(?:入口|的(?:路径|入口)|\s+(?:entrance|gate)\b)", after, re.I
    )
    if context and (destination or entrance):
        code = re.compile(
            r"(?<![A-Za-z0-9_])" + re.escape(match.group()) + r"(?![A-Za-z0-9_])"
        )
        return any(
            is_physical_identifier(context, other) for other in code.finditer(context)
        )
    return False
