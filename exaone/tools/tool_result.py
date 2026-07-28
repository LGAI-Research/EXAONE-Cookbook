"""
(en) Shared result types for tool and external source lookups (reference impl, MCP clients, etc.).

(kr) 도구·외부 소스 조회용 공용 결과 타입이다(참조 구현·MCP 클라이언트 등).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

# (en) Policy B: transport OK + zero hits → outcome=EMPTY, ok=True, content="", metadata.empty=True
# (kr) Policy B. transport OK + 0건 → outcome=EMPTY, ok=True, content="", metadata.empty=True

# (en) Promote only when MCP/third-party tools send legacy wire (ok=false + error below) for zero hits
# (kr) MCP·서드파티 tool이 예전 wire(ok=false + 아래 error)로 0건을 보낼 때만 승격한다
_EXTERNAL_EMPTY_ERROR_HINTS = (
    "no results",
    "no matching",
    "empty context",
    "empty result",
    "no graph results",
    "no vector results",
)


class ToolOutcome(str, Enum):
    """
    (en) Machine-readable classification of tool execution outcomes.

    (kr) 도구 실행 결과의 machine-readable 분류이다.
    """

    SUCCESS = "success"
    EMPTY = "empty"
    VALIDATION_ERROR = "validation_error"
    UNAVAILABLE = "unavailable"
    TRANSPORT_ERROR = "transport_error"


def _wire_error_means_empty(error: str | None) -> bool:
    if not error:
        return False
    lowered = error.lower()
    return any(hint in lowered for hint in _EXTERNAL_EMPTY_ERROR_HINTS)


def _infer_outcome_from_wire(
    *,
    outcome_raw: Any,
    ok: Any,
    content: str,
    error_str: str,
    metadata: dict[str, Any],
) -> ToolOutcome:
    if outcome_raw is not None:
        try:
            return ToolOutcome(str(outcome_raw))
        except ValueError:
            return ToolOutcome.TRANSPORT_ERROR

    if metadata.get("empty") is True:
        return ToolOutcome.EMPTY

    if ok is True:
        if not content.strip() or _wire_error_means_empty(error_str):
            return ToolOutcome.EMPTY
        return ToolOutcome.SUCCESS

    if ok is False:
        if _wire_error_means_empty(error_str):
            return ToolOutcome.EMPTY
        return ToolOutcome.TRANSPORT_ERROR

    if _wire_error_means_empty(error_str):
        return ToolOutcome.EMPTY
    if error_str:
        return ToolOutcome.TRANSPORT_ERROR
    if not content.strip():
        return ToolOutcome.EMPTY
    return ToolOutcome.SUCCESS


def _apply_outcome_fields(
    outcome: ToolOutcome,
    *,
    content: str,
    error_str: str,
    metadata: dict[str, Any],
) -> tuple[str, str | None, dict[str, Any]]:
    if outcome == ToolOutcome.EMPTY:
        if error_str and "empty_reason" not in metadata:
            metadata.setdefault("empty_reason", error_str)
        metadata["empty"] = True
        return "", None, metadata

    if outcome == ToolOutcome.SUCCESS:
        return content, None, metadata

    return "", error_str or "tool failed", metadata


def _coerce_wire_dict(raw: dict[str, Any] | None) -> dict[str, Any]:
    """
    (en) Normalize an external wire dict into a dict for ``ToolResultModel.model_validate``.

    (kr) 외부 wire dict를 ``ToolResultModel.model_validate``에 넣을 정규화 dict로 변환한다.
    """
    if not isinstance(raw, dict):
        raw = {}

    content = str(raw.get("content") or "")
    source = str(raw.get("source") or "")
    error_val = raw.get("error")
    error_str = str(error_val).strip() if error_val is not None else ""
    metadata = dict(raw.get("metadata") or {})
    ok = raw.get("ok")

    outcome = _infer_outcome_from_wire(
        outcome_raw=raw.get("outcome"),
        ok=ok,
        content=content,
        error_str=error_str,
        metadata=metadata,
    )

    if ok is True and outcome not in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY):
        outcome = ToolOutcome.EMPTY if not content.strip() else ToolOutcome.SUCCESS
    if ok is False and outcome == ToolOutcome.SUCCESS:
        outcome = ToolOutcome.TRANSPORT_ERROR

    content, error_str, metadata = _apply_outcome_fields(
        outcome,
        content=content,
        error_str=error_str,
        metadata=metadata,
    )

    return {
        "ok": outcome in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY),
        "outcome": outcome.value,
        "content": content if outcome == ToolOutcome.SUCCESS else "",
        "source": source,
        "error": error_str,
        "metadata": metadata,
    }


def _assert_tool_result_invariants(
    *,
    outcome: ToolOutcome,
    content: str,
    error: str | None,
    metadata: dict[str, Any],
) -> None:
    ok = outcome in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY)
    if ok:
        if error:
            raise ValueError("ok=True requires error=None")
        if outcome == ToolOutcome.EMPTY:
            if content.strip():
                raise ValueError("EMPTY outcome requires content=''")
            if not metadata.get("empty"):
                raise ValueError("EMPTY outcome requires metadata['empty']=True")
    else:
        if not (error or "").strip():
            raise ValueError("ok=False requires non-empty error")
        if content.strip():
            raise ValueError("failure outcomes must not set content")


@dataclass
class ToolResult:
    """
    (en) Shared tool result.

    - Policy B: zero hits (transport OK) uses ``empty()`` → ``ok=True``, ``content=""``,
      ``metadata["empty"]=True``.
    - Failures (validation, config, transport) use ``validation_error`` / ``unavailable`` / ``failure`` →
      ``ok=False`` with non-empty ``error``.
    - Internal code should use factories only. External wire dicts follow a single path:
      ``ToolResultModel.parse_wire`` → ``ToolResult.from_dict`` / ``validate_payload``.

    (kr) 공용 tool result이다.

    - Policy B: 결과 0건(transport OK)은 ``empty()`` → ``ok=True``, ``content=""``,
      ``metadata["empty"]=True``이다.
    - 실패(검증·설정·transport)는 ``validation_error`` / ``unavailable`` / ``failure`` →
      ``ok=False``와 non-empty ``error``이다.
    - 내부 코드는 팩토리만 사용한다. 외부 wire dict는
      ``ToolResultModel.parse_wire`` → ``ToolResult.from_dict`` / ``validate_payload`` 한 경로로 처리한다.
    """

    outcome: ToolOutcome
    content: str = ""
    source: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY)

    @property
    def is_empty(self) -> bool:
        return self.outcome == ToolOutcome.EMPTY

    @property
    def has_content(self) -> bool:
        return self.outcome == ToolOutcome.SUCCESS and bool(self.content.strip())

    def __post_init__(self) -> None:
        if self.outcome == ToolOutcome.EMPTY and not self.metadata.get("empty"):
            self.metadata = {**self.metadata, "empty": True}
        _assert_tool_result_invariants(
            outcome=self.outcome,
            content=self.content,
            error=self.error,
            metadata=self.metadata,
        )

    @classmethod
    def _from_model(cls, model: ToolResultModel) -> ToolResult:
        return cls(
            outcome=model.outcome,
            content=model.content,
            source=model.source,
            error=model.error,
            metadata=dict(model.metadata),
        )

    @classmethod
    def success(
        cls,
        *,
        content: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return cls(
            outcome=ToolOutcome.SUCCESS,
            content=content,
            source=source,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def empty(
        cls,
        *,
        source: str,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        meta = dict(metadata or {})
        meta["empty"] = True
        if reason:
            meta["empty_reason"] = reason
        return cls(
            outcome=ToolOutcome.EMPTY,
            content="",
            source=source,
            metadata=meta,
        )

    @classmethod
    def failure(
        cls,
        *,
        source: str,
        error: str,
        outcome: ToolOutcome = ToolOutcome.TRANSPORT_ERROR,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        if outcome in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY):
            raise ValueError(f"failure() does not accept outcome={outcome!r}")
        return cls(
            outcome=outcome,
            source=source,
            error=error,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def validation_error(
        cls,
        *,
        source: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return cls.failure(
            source=source,
            error=error,
            outcome=ToolOutcome.VALIDATION_ERROR,
            metadata=metadata,
        )

    @classmethod
    def unavailable(
        cls,
        *,
        source: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return cls.failure(
            source=source,
            error=error,
            outcome=ToolOutcome.UNAVAILABLE,
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ToolResult:
        """
        (en) External wire dict → ``parse_wire`` → ``ToolResult``.

        (kr) 외부 wire dict를 ``parse_wire`` 경유하여 ``ToolResult``로 변환한다.
        """
        return cls._from_model(ToolResultModel.parse_wire(raw))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "outcome": self.outcome.value,
            "content": self.content,
            "source": self.source,
            "error": self.error,
            "metadata": self.metadata,
        }


class ToolResultModel(BaseModel):
    """
    (en) Wire-format schema (MCP client boundary).

    Pipeline: ``_coerce_wire_dict`` → ``model_validate`` → (``ToolResult`` | ``dict``).

    (kr) Wire-format 스키마이다(MCP client 경계).

    파이프라인: ``_coerce_wire_dict`` → ``model_validate`` → (``ToolResult`` | ``dict``)이다.
    """

    ok: bool
    outcome: ToolOutcome
    content: str = ""
    source: str = ""
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_invariants(self) -> ToolResultModel:
        _assert_tool_result_invariants(
            outcome=self.outcome,
            content=self.content,
            error=self.error,
            metadata=self.metadata,
        )
        if self.ok != (self.outcome in (ToolOutcome.SUCCESS, ToolOutcome.EMPTY)):
            raise ValueError("ok must match outcome")
        return self

    @classmethod
    def parse_wire(cls, raw: dict[str, Any] | None) -> ToolResultModel:
        """
        (en) External dict → wire normalization → Pydantic validation. Common entry for ``from_dict`` / ``validate_payload``.

        (kr) 외부 dict를 wire 정규화한 뒤 Pydantic 검증한다. ``from_dict`` / ``validate_payload``의 공통 진입점이다.
        """
        return cls.model_validate(_coerce_wire_dict(raw))

    @classmethod
    def validate_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """
        (en) ``parse_wire`` → dict for the tool loop.

        (kr) ``parse_wire``를 거쳐 tool loop용 dict를 반환한다.
        """
        return cls.parse_wire(payload).model_dump()


__all__ = ["ToolOutcome", "ToolResult", "ToolResultModel"]
