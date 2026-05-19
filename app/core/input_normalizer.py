import re
from typing import Any

# 10k characters keeps requests bounded for predictable latency/cost while still
# fitting common resume, meeting-note, and idea-dump payload sizes.
MAX_INPUT_LENGTH = 10000
INJECTION_PATTERNS = [
    r"ignore\s+previous",
    r"system\s+prompt",
    r"developer\s+message",
    r"act\s+as",
    r"override\s+instructions",
]


def _strip_html_tags(value: str) -> str:
    out: list[str] = []
    in_tag = False
    for ch in value:
        if ch == "<":
            in_tag = True
            continue
        if ch == ">":
            in_tag = False
            continue
        if not in_tag:
            out.append(ch)
    return "".join(out)


def _sanitize_text(value: str) -> str:
    text = _strip_html_tags(value)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    for pattern in INJECTION_PATTERNS:
        text = re.sub(pattern, "[filtered]", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_INPUT_LENGTH]


def normalize_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    normalized: dict[str, Any] = {}
    token_chars = 0
    for key, value in payload.items():
        if isinstance(value, str):
            clean = _sanitize_text(value)
            normalized[key] = clean
            token_chars += len(clean)
        else:
            normalized[key] = value
    token_estimate = max(1, token_chars // 4)
    return normalized, token_estimate
