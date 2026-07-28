"""
(en) Provider-agnostic trial / tool-call record types shared by all M1–M10 metric modules.
A single trial = one run of a runner (naive or harness) on one task.
A pass^k batch = a list of trials grouped by task_id (k trials per task).

(kr) M1–M10 metric 모듈이 공유하는 provider 비의존 trial / tool-call 레코드 타입이다.
trial 한 건 = runner(naive 혹은 harness)가 task 하나를 1회 실행한 결과.
pass^k 배치 = task_id로 묶인 trial 리스트(태스크당 k trial).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ToolCallRecord:
    """
    (en) One tool invocation observed in a trial. `arguments` should be the parsed
    dict that was actually passed to the tool (not raw JSON string).

    (kr) trial에서 관측한 도구 호출 한 건. `arguments`는 도구로 실제 넘긴 파싱된 dict.
    """

    name: str
    arguments: Mapping[str, Any]
    result_repr: str | None = None
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class TrialResult:
    """
    (en) Unified record produced by both runners. Designed so M1–M10 can read a single
    list[TrialResult] without caring whether the runner was naive or harness.

    Fields mirror keys in `exaone.observability.fields` so harness traces can be mapped
    1:1; naive runner is responsible for filling the same shape.

    (kr) 두 runner가 공통으로 산출하는 통합 레코드. M1–M10이 runner 종류와 무관하게
    list[TrialResult] 하나만 보고 점수를 낼 수 있도록 설계했다.

    필드 명칭은 `exaone.observability.fields`와 정렬되어 있어 harness trace를 1:1
    매핑할 수 있고, naive runner는 동일한 shape를 직접 채워 넣는다.
    """

    trial_id: str
    task_id: str
    dataset: str
    runner: str  # "naive" | "harness"

    final_content: str = ""
    final_structured: Any = None
    tool_calls: list[ToolCallRecord] = field(default_factory=list)

    turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_latency_ms: float = 0.0

    finished: bool = True
    error: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return int(self.input_tokens) + int(self.output_tokens)


@dataclass(frozen=True)
class MetricSummary:
    """
    (en) Common summary container for M1–M10. `value` is the primary scalar reported
    in the dashboard; `breakdown` carries extra fields (e.g. strict/loose, repair gain).

    (kr) M1–M10 공통 요약 컨테이너. `value`는 대시보드에 노출하는 주요 스칼라이고,
    `breakdown`은 부가 필드(예: strict/loose, repair gain)를 담는다.
    """

    metric_id: str
    name: str
    value: float
    n: int
    ci_low: float | None = None
    ci_high: float | None = None
    breakdown: Mapping[str, float] = field(default_factory=dict)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "n": self.n,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "breakdown": dict(self.breakdown),
            "notes": self.notes,
        }


__all__ = ["ToolCallRecord", "TrialResult", "MetricSummary"]
