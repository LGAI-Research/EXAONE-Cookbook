"""
(en) Attempt to repair corrupted or truncated JSON strings.
Used only when extraction fails; normal and Extra data cases are handled by JsonExtractor.

Tries distinct strategies in order inside one call (deterministic multi-strategy).

(kr) 손상/잘림된 JSON 문자열 복구를 시도한다.
추출 실패 시에만 사용하며, 정상·Extra data는 JsonExtractor가 처리한다.

내부에서 서로 다른 전략을 순서대로 시도한다(결정적 multi-strategy).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from exaone.output.base_processor import BaseOutputProcessor, ProcessorResult
from exaone.output.json_extractor import JsonExtractor, normalize_to_json_substring


class AutoRepair(BaseOutputProcessor):
    """
    (en) Repairs truncated or corrupted JSON. Tries strategies sequentially within one ``process()`` call.

    (kr) 잘린·손상된 JSON을 복구한다. 한 번의 ``process()`` 호출 안에서 전략을 순차 시도한다.
    """

    supports_retry: bool = False

    def __init__(self) -> None:
        self._extractor = JsonExtractor()

    def process(self, raw_text: str) -> ProcessorResult:
        extracted = self._extractor.process(raw_text)
        if extracted.success:
            return extracted

        repaired = self.repair(raw_text)
        if repaired.success:
            return repaired

        # (en) Preserve the original extractor error when repair also fails.
        # (kr) 복구도 실패하면 원래 extractor 오류를 유지한다.
        return ProcessorResult(
            success=False,
            data=None,
            raw=raw_text,
            error=extracted.error or repaired.error or "json repair failed",
        )

    def repair(self, raw_text: str) -> ProcessorResult:
        """
        (en) Run only the deterministic repair strategies (no first-value extraction),
        so a corrupted object is rebuilt instead of collapsing to an inner sub-value
        (e.g. a valid array nested inside a broken object).

        (kr) 추출 단계 없이 결정적 복구 전략만 실행한다. 손상된 object 가 내부 하위값
        (예: 깨진 object 안의 유효한 배열)으로 떨어지지 않고 object 로 복구되게 한다.
        """
        s = normalize_to_json_substring(raw_text)
        if not s or not s.strip():
            return ProcessorResult(
                success=False, data=None, raw=raw_text, error="json repair failed"
            )

        last_error = "json repair failed"
        strategies: tuple[Callable[[str], str | None], ...] = (
            self._strategy_brackets,
            self._strategy_unclosed_string,
            self._strategy_truncate_trailing,
        )
        for strategy in strategies:
            repaired = strategy(s)
            if not repaired:
                continue
            data = self._try_parse(repaired)
            if data is not None:
                return ProcessorResult(success=True, data=data, raw=repaired)
            last_error = "json repair failed after strategy"

        return ProcessorResult(
            success=False,
            data=None,
            raw=raw_text,
            error=last_error,
        )

    def _strategy_brackets(self, s: str) -> str:
        return self._repair_brackets(s)

    def _strategy_unclosed_string(self, s: str) -> str | None:
        if not self._ends_inside_string(s):
            return None
        return self._repair_brackets(s + '"')

    def _strategy_truncate_trailing(self, s: str) -> str | None:
        """
        (en) Truncate an incomplete trailing field, then close brackets.

        (kr) 끝의 불완전 필드를 잘라낸 뒤 괄호를 닫는다.
        """
        trimmed = s.rstrip()
        for cut in range(len(trimmed) - 1, max(0, len(trimmed) - 500), -1):
            if trimmed[cut] not in (",", ":"):
                continue
            candidate = trimmed[:cut].rstrip().rstrip(",")
            if not candidate:
                continue
            repaired = self._repair_brackets(candidate)
            if self._try_parse(repaired) is not None:
                return repaired
        return None

    @staticmethod
    def _try_parse(s: str) -> Any | None:
        try:
            data, _ = json.JSONDecoder().raw_decode(s)
            return data
        except json.JSONDecodeError:
            return None

    def _repair_brackets(self, s: str) -> str:
        """
        (en) Close a string that looks like truncated JSON into a valid form.

        (kr) 끝이 잘린 JSON처럼 보이는 문자열을 닫아서 유효한 형태로 만든다.
        """
        s = s.rstrip()
        s = re.sub(r",\s*([}\]])", r"\1", s)
        s = re.sub(r",\s*$", "", s)
        open_braces, open_brackets = self._count_unclosed(s)
        return s + "]" * open_brackets + "}" * open_braces

    @staticmethod
    def _ends_inside_string(s: str) -> bool:
        in_string = False
        escape = False
        for c in s:
            if escape:
                escape = False
                continue
            if c == "\\" and in_string:
                escape = True
                continue
            if c == '"':
                in_string = not in_string
        return in_string

    @staticmethod
    def _count_unclosed(s: str) -> tuple[int, int]:
        """
        (en) Return counts of unclosed { and [ ignoring brackets inside strings.

        (kr) 문자열 내부 괄호를 무시하고 실제 미닫힌 { 와 [ 개수를 반환한다.
        """
        brace_depth = 0
        bracket_depth = 0
        in_string = False
        escape = False
        for c in s:
            if escape:
                escape = False
                continue
            if c == "\\" and in_string:
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                brace_depth += 1
            elif c == "}":
                brace_depth -= 1
            elif c == "[":
                bracket_depth += 1
            elif c == "]":
                bracket_depth -= 1
        return max(0, brace_depth), max(0, bracket_depth)
