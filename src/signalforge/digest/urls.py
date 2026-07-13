"""Pure HTTP/HTTPS URL extraction and canonicalization."""

import re
from urllib.parse import urlsplit, urlunsplit

URL_PATTERN = re.compile(r"https?://[^\s<>\[\]{}\"']+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,;:!?"


def extract_urls(text: str) -> tuple[str, ...]:
    """Return unique canonical URLs in first-seen order."""
    result: list[str] = []
    seen: set[str] = set()
    for match in URL_PATTERN.finditer(text):
        candidate = match.group(0).rstrip(TRAILING_PUNCTUATION)
        candidate = _trim_unmatched_closing_parentheses(candidate)
        canonical = canonicalize_url(candidate)
        if canonical is not None and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return tuple(result)


def canonicalize_url(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None

    hostname = parsed.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "", parsed.query, ""))


def _trim_unmatched_closing_parentheses(value: str) -> str:
    while value.endswith(")") and value.count(")") > value.count("("):
        value = value[:-1]
    return value
