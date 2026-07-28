"""
(en) String sanitization for logs and exception messages. API 4xx bodies may contain prompts, PII, or credentials; by default, pass text through this helper before logging or raising RuntimeError.

(kr) 로그·예외 메시지용 문자열 정제이다. API 4xx 본문 등에 프롬프트·PII·인증 값이 섞일 수 있으므로, 기본은 이 헬퍼를 거친 뒤만 logger / RuntimeError 에 넣는다.
"""
from __future__ import annotations

import json
import re
from typing import Any

_REDACTED = "[REDACTED]"

# (en) HTTP headers and Bearer tokens (JSON and plain text)
# (kr) HTTP 헤더·Bearer(JSON/평문 공통)
_REGEX_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?i)(Authorization\s*:\s*)(Bearer\s+)(\S+)",
            re.MULTILINE,
        ),
        rf"\1\2{_REDACTED}",
    ),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+/=]+\b"), f"Bearer {_REDACTED}"),
    (
        re.compile(
            r'(?i)("(?:api_key|access_token|refresh_token|authorization|token|secret|password)"\s*:\s*)"[^"]*"',
        ),
        rf'\1"{_REDACTED}"',
    ),
    (
        re.compile(
            r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|authorization)\s*=\s*\S+",
        ),
        rf"\1={_REDACTED}",
    ),
    (
        re.compile(r"(?i)(X-Api-Key\s*:\s*)\S+", re.MULTILINE),
        rf"\1{_REDACTED}",
    ),
    (
        re.compile(r"(?i)(X-Friendli-Team\s*:\s*)\S+", re.MULTILINE),
        rf"\1{_REDACTED}",
    ),
]

_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "token",
        "secret",
        "password",
        "x-api-key",
        "x-friendli-team",
    }
)

_CONTENT_KEYS = frozenset(
    {
        "messages",
        "prompt",
        "input",
        "content",
        "reasoning_content",
        "thinking",
        "reasoning",
        "tool_calls",
        "arguments",
        "system",
    }
)


def _redact_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            key_lower = key.lower()
            if key_lower in _SENSITIVE_KEYS:
                out[key] = _REDACTED
            elif key_lower in _CONTENT_KEYS:
                out[key] = _redact_content_value(key_lower, value)
            else:
                out[key] = _redact_json(value)
        return out
    if isinstance(obj, list):
        return [_redact_json(item) for item in obj]
    return obj


def _redact_content_value(key: str, value: Any) -> Any:
    if key == "messages" and isinstance(value, list):
        return {"_redacted": "messages", "count": len(value)}
    if isinstance(value, str):
        if not value.strip():
            return value
        return _REDACTED
    if isinstance(value, (list, dict)):
        return _REDACTED
    return _REDACTED


def _apply_regex(text: str) -> str:
    out = text
    for pattern, repl in _REGEX_REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def sanitize_for_log(text: str, *, max_len: int = 800) -> str:
    """
    (en) Sanitize a string before logging or raising. If JSON, mask large or sensitive keys such as messages/content then serialize; replace Bearer/api_key patterns; truncate with suffix ``...`` when longer than max_len.

    (kr) 로그·예외에 넣기 전 문자열을 정제한다. JSON이면 messages/content 등 대용량·민감 키를 마스킹 후 직렬화한다. Bearer·api_key 등 패턴을 치환한다. max_len 초과 시 잘림(접미사 ``...``)한다.
    """
    raw = text or ""
    if not raw.strip():
        return ""

    stripped = raw.strip()
    sanitized = stripped
    try:
        parsed = json.loads(stripped)
        sanitized = json.dumps(_redact_json(parsed), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError, ValueError):
        sanitized = stripped

    sanitized = _apply_regex(sanitized)
    if len(sanitized) <= max_len:
        return sanitized
    return sanitized[: max_len - 3] + "..."


__all__ = ["sanitize_for_log", "_REDACTED"]
