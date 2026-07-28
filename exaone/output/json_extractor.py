"""
(en) Extract only the first JSON value from LLM raw text (ignores Extra data, code blocks, surrounding prose).
Bracket-matching trims to the first object so parsing succeeds even when text follows the JSON.

(kr) LLM 원문에서 첫 번째 JSON 값만 추출한다(Extra data, 코드블록, 앞뒤 설명 무시).
괄호 매칭으로 첫 객체만 잘라 파싱해, JSON 뒤에 문자가 있어도 Extra data가 나지 않는다.
"""
from __future__ import annotations

import json
import re
from exaone.output.base_processor import BaseOutputProcessor, ProcessorResult

_THINKING_RE = re.compile(
    r"<think>.*?</think>",
    re.DOTALL | re.IGNORECASE,
)


def _strip_thinking_blocks(s: str) -> str:
    """
    (en) Remove <think>...</think> blocks. Preprocesses enable_thinking=True output.

    (kr) <think>...</think> 블록을 제거한다. enable_thinking=True 출력 전처리용이다.
    """
    return _THINKING_RE.sub("", s).strip()


def _extract_fenced_blocks(s: str) -> list[str]:
    """
    (en) Extract ```fence``` block contents in order without regex.

    (kr) 정규식 없이 ```fence``` 블록 내용을 순서대로 추출한다.
    """
    blocks: list[str] = []
    i = 0
    while True:
        start = s.find("```", i)
        if start < 0:
            break
        open_end = start + 3
        close = s.find("```", open_end)
        if close < 0:
            break
        inner = s[open_end:close].strip()
        if inner:
            lines = inner.splitlines()
            if lines:
                # (en) Drop first line if it is a language tag (json, javascript, etc.)
                # (kr) 첫 줄이 언어 태그(json, javascript 등)이면 제거한다
                first = lines[0].strip()
                if first.isalpha() and len(first) <= 20:
                    inner = "\n".join(lines[1:]).strip()
            if inner:
                blocks.append(inner)
        i = close + 3
    return blocks


def _candidate_texts(raw: str) -> list[str]:
    """
    (en) JSON extraction attempt order: inside code blocks, then full raw text.

    (kr) JSON 추출 시도 순서는 코드블록 내부, 원문 전체이다.
    """
    cleaned = _strip_thinking_blocks(raw.strip())
    if not cleaned:
        return []
    blocks = _extract_fenced_blocks(cleaned)
    return [*blocks, cleaned]


def _parse_first_json_value(text: str) -> object | None:
    """
    (en) Scan the string for the first JSON object/array and parse it.
    raw_decode reads only the first value safely even with leading/trailing prose.

    (kr) 문자열에서 첫 JSON object/array를 탐색해 파싱한다.
    앞뒤 설명/후행 텍스트가 있어도 raw_decode로 첫 값만 안전하게 읽는다.
    """
    decoder = json.JSONDecoder()
    for i, c in enumerate(text):
        if c not in ("{", "["):
            continue
        candidate = text[i:]
        try:
            value, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError as exc:
            # (en) Failure at/after the last non-space char means this looks like an
            # unclosed/truncated OUTERMOST value. Defer to the repair stage (which closes
            # brackets) instead of falling through to a smaller inner fragment — otherwise the
            # inner array/object would be validated against the top-level schema and fail.
            # (kr) 마지막 비공백 문자 이후에서 실패하면 미완·잘린 최상위 값으로 본다.
            # 안쪽 하위 조각으로 흘러가지 말고 (괄호를 닫는) repair 단계로 넘긴다 —
            # 그렇지 않으면 안쪽 배열/객체가 최상위 스키마로 검증돼 실패한다.
            if exc.pos >= len(candidate.rstrip()):
                return None
            continue
        if isinstance(value, (dict, list)):
            return value
    return None


def normalize_to_json_substring(raw: str) -> str | None:
    """
    (en) Return a substring from the start of the first JSON object/array.
    For legacy AutoRepair path compatibility.

    (kr) 첫 JSON object/array 시작 위치부터의 부분 문자열을 반환한다.
    레거시 AutoRepair 경로 호환용이다.
    """
    if not raw or not raw.strip():
        return None
    for candidate in _candidate_texts(raw):
        for i, c in enumerate(candidate):
            if c in ("{", "["):
                return candidate[i:]
    return None


class JsonExtractor(BaseOutputProcessor):
    """
    (en) Extract only the first JSON value from raw text.
    Allows code blocks, prose, and trailing text; parses the first object/array via raw_decode.

    (kr) 원문에서 첫 번째 JSON 값만 추출한다.
    코드블록/설명/후행 텍스트를 허용하고, raw_decode 기반으로 첫 object/array만 파싱한다.
    """

    def process(self, raw_text: str) -> ProcessorResult:
        if not raw_text or not raw_text.strip():
            return ProcessorResult(success=False, data=None, raw=raw_text, error="empty")
        candidates = _candidate_texts(raw_text)
        if not candidates:
            return ProcessorResult(success=False, data=None, raw=raw_text, error="empty")
        for candidate in candidates:
            data = _parse_first_json_value(candidate)
            if data is not None:
                return ProcessorResult(success=True, data=data, raw=raw_text)
        return ProcessorResult(
            success=False,
            data=None,
            raw=raw_text,
            error="no valid json object/array found",
        )
