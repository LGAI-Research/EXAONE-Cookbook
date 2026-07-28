"""
(en) Unicode post-processing for LLM/tool output strings.
Normalizes broken Unicode (surrogates, invalid escapes) in tool_calls arguments
so strings are always valid UTF-8.

(kr) LLM/툴 출력 문자열의 유니코드 후처리이다.
tool_calls arguments 등에서 깨진 유니코드(서로게이트, 잘못된 이스케이프)를 정규화해
항상 유효한 UTF-8 문자열로 만든다.
"""
from __future__ import annotations

import unicodedata
from typing import Any


def normalize_unicode_string(s: str) -> str:
    """
    (en) Normalize a single string to valid Unicode.
    Broken lone surrogates/invalid sequences become U+FFFD (REPLACEMENT CHARACTER) or are removed.
    Applies NFC normalization (unifies composed characters).

    (kr) 단일 문자열을 유효한 유니코드로 정규화한다.
    깨진 서로게이트/잘못된 시퀀스는 U+FFFD(REPLACEMENT CHARACTER)로 바꾸거나 제거한다.
    NFC 정규화(조합 문자 통일)를 적용한다.
    """
    if not isinstance(s, str) or not s:
        return s
    try:
        # (en) Broken lone surrogates (D800–DFFF): surrogatepass then decode with replace
        # (kr) 깨진 단독 서로게이트(D800–DFFF). surrogatepass 후 decode 시 replace한다
        out = s.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")
    except Exception:
        out = "".join(c if ord(c) < 0x110000 and not (0xD800 <= ord(c) <= 0xDFFF) else "\ufffd" for c in s)
    return unicodedata.normalize("NFC", out)


def normalize_json_string_values(obj: Any) -> Any:
    """
    (en) Walk dict/list/nested structures and normalize every str value with normalize_unicode_string.
    Call right after parsing tool_calls arguments so argument strings stay intact.

    (kr) dict/list/중첩 구조를 순회하며 모든 str 값을 normalize_unicode_string으로 정규화한다.
    tool_calls arguments 파싱 직후 호출해 인자 내 문자열이 깨지지 않도록 할 때 사용한다.
    """
    if isinstance(obj, str):
        return normalize_unicode_string(obj)
    if isinstance(obj, dict):
        return {k: normalize_json_string_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_json_string_values(item) for item in obj]
    return obj
