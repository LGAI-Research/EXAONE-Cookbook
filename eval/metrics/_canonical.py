"""
(en) Argument / value normalization shared by M3, M4, M8.

Rules intentionally match `exaone.agents.next_step_planner.ToolInvocationKey`:
the canonical form of an arguments dict is `json.dumps(args, sort_keys=True, ensure_ascii=False)`.
For string values inside arguments we additionally apply case-insensitive,
whitespace-normalized comparison (BFCL v3 AST matcher convention) when comparing
against gold values.

(kr) M3, M4, M8가 공유하는 인자/값 정규화 모듈이다.

규칙은 의도적으로 `exaone.agents.next_step_planner.ToolInvocationKey`와 동일하다.
즉 인자 dict의 canonical form은 `json.dumps(args, sort_keys=True, ensure_ascii=False)`.
gold 값과 비교할 때 문자열 값은 BFCL v3 AST matcher 컨벤션에 따라 대소문자 무시 및
공백 정규화를 추가로 적용한다.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_TRIM_RE = re.compile(r"^[\s\u00a0\.\,\!\?\;\:\'\"\(\)\[\]\{\}]+|[\s\u00a0\.\,\!\?\;\:\'\"\(\)\[\]\{\}]+$")


def canonical_args(arguments: Mapping[str, Any] | None) -> str:
    """
    (en) Stable canonical JSON for an arguments dict (matches harness ledger key).

    (kr) 인자 dict를 안정적인 canonical JSON으로 직렬화한다(harness ledger 키와 동일).
    """
    return json.dumps(arguments or {}, sort_keys=True, ensure_ascii=False)


def canonical_call_key(name: str, arguments: Mapping[str, Any] | None) -> str:
    """
    (en) Canonical key for a single tool invocation; used for duplicate detection (M8).

    (kr) 단일 도구 호출의 canonical 키. 중복 탐지(M8)에 사용한다.
    """
    return f"{name}::{canonical_args(arguments)}"


def normalize_scalar(value: Any) -> Any:
    """
    (en) BFCL-style value normalization: lower-case, collapse internal whitespace,
    trim leading/trailing punctuation. Non-string values pass through unchanged.

    (kr) BFCL 스타일 값 정규화: 소문자화, 내부 공백 압축, 양 끝 구두점 제거.
    문자열이 아니면 원본을 그대로 반환한다.
    """
    if not isinstance(value, str):
        return value
    s = value.strip().lower()
    s = _WHITESPACE_RE.sub(" ", s)
    s = _PUNCT_TRIM_RE.sub("", s)
    return s


def normalize_arguments(arguments: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    (en) Recursively normalize string leaves inside an arguments dict for soft comparison.

    (kr) 인자 dict 내부 문자열 leaf를 재귀 정규화하여 soft 비교에 사용한다.
    """
    if arguments is None:
        return {}
    return {k: _normalize_value(v) for k, v in arguments.items()}


def _normalize_value(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _normalize_value(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [_normalize_value(vv) for vv in v]
    return normalize_scalar(v)


def normalize_bfcl_value(value: Any) -> Any:
    """
    (en) BFCL entity normalization: ``normalize_scalar`` plus optional prefix strip
    (e.g. ``company XYZ`` vs gold ``XYZ``).

    (kr) BFCL entity 정규화: ``normalize_scalar`` + 선택 prefix 제거
    (예: ``company XYZ`` vs gold ``XYZ``).
    """
    base = normalize_scalar(value)
    if not isinstance(base, str):
        return base
    s = base
    for prefix in ("company ", "product ", "the "):
        if s.startswith(prefix):
            s = s[len(prefix) :].strip()
    return s


def values_match(pred: Any, gold: Any) -> bool:
    """
    (en) BFCL-style value equality: scalars after normalize; lists order-insensitive when
    both are lists of scalars; dicts compared key-wise (recursive).

    (kr) BFCL 스타일 값 비교: 스칼라는 정규화 후 일치, 양쪽이 스칼라 list면 순서 무시,
    dict는 키 단위 재귀 비교.
    """
    if isinstance(pred, dict) and isinstance(gold, dict):
        if set(pred.keys()) != set(gold.keys()):
            return False
        return all(values_match(pred[k], gold[k]) for k in gold.keys())
    if isinstance(pred, list) and isinstance(gold, list):
        if len(pred) != len(gold):
            return False
        if all(not isinstance(x, (dict, list)) for x in pred + gold):
            return sorted(normalize_scalar(x) for x in pred) == sorted(
                normalize_scalar(x) for x in gold
            )
        return all(values_match(p, g) for p, g in zip(pred, gold))
    return normalize_scalar(pred) == normalize_scalar(gold)


__all__ = [
    "canonical_args",
    "canonical_call_key",
    "normalize_scalar",
    "normalize_bfcl_value",
    "normalize_arguments",
    "values_match",
]
