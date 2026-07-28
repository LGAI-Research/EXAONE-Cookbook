"""
(en) Provider-agnostic data contract shared by every external benchmark loader
under `eval/datasets/`. Each loader (BFCL v3, tau-bench, IFEval, HaluBench, ...)
normalises its raw rows into `EvalTask` instances so that downstream
`eval/metrics/`, `eval/runners/`, and `eval/judges/` can stay decoupled from any
particular dataset format. No dependency on `exaone/`.

(kr) `eval/datasets/` 아래의 모든 외부 벤치마크 로더가 공유하는 provider 비의존 데이터 계약이다.
각 로더(BFCL v3, tau-bench, IFEval, HaluBench 등)는 원본 row를 `EvalTask` 인스턴스로 정규화하며,
이를 통해 하위의 `eval/metrics/`, `eval/runners/`, `eval/judges/`는 특정 데이터셋 포맷에 결합되지 않는다.
`exaone/`에 대한 의존성은 없다.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any


@dataclass
class ToolSpec:
    """
    (en) JSON-schema description of a single tool/function available to the model
    at evaluation time. Mirrors the OpenAI/Friendli `function` payload shape.

    (kr) 평가 시 모델이 사용할 수 있는 단일 도구/함수의 JSON 스키마 설명이다.
    OpenAI/Friendli의 `function` payload 형식과 동일한 구조를 가진다.
    """

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ExpectedToolCall:
    """
    (en) Ground-truth tool invocation. `arguments` must be canonical JSON (key
    order is irrelevant — metric code normalises before comparison).

    (kr) 정답 도구 호출이다. `arguments`는 canonical JSON이며, 지표 계산 코드가 비교 전 정규화한다(키 순서 무관).
    """

    name: str
    arguments: dict[str, Any]


@dataclass
class EvalTask:
    """
    (en) Unified evaluation task. Every loader emits a list of these regardless of
    the upstream benchmark. Optional fields exist so a single record can drive
    several metrics (M1 task success, M3 tool selection, M5 abstention, M6
    schema adherence, M9 faithfulness, ...). See `eval/README.md` section 3.3
    for the dataset → metric mapping.

    (kr) 통합 평가 태스크이다. 상위 벤치마크와 무관하게 모든 로더는 본 객체의 리스트를 반환한다.
    선택 필드를 두어 단일 record가 여러 지표(M1 과업 성공률, M3 도구 선택, M5 부재율, M6 스키마 준수, M9 신뢰성 등)에 사용될 수 있도록 한다.
    데이터셋 → 지표 매핑은 `eval/README.md` 3.3절을 참조한다.
    """

    task_id: str
    dataset: str
    category: str
    query: str
    system_prompt: str | None = None
    tools: list[ToolSpec] = field(default_factory=list)
    expected_tool_calls: list[ExpectedToolCall] | None = None
    expected_answer: Any = None
    expected_no_tools: bool = False
    json_schema: dict[str, Any] | None = None
    required_keys: list[str] | None = None
    rubric: str | None = None
    grounding_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        (en) Stable serialisation to a plain dict (round-trip safe with `from_dict`).
        (kr) plain dict으로의 안정적 직렬화이다(`from_dict`와 round-trip 호환).
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvalTask":
        """
        (en) Reconstruct an `EvalTask` from a dict produced by `to_dict`. Unknown
        keys are ignored; missing optional keys fall back to defaults.

        (kr) `to_dict`로 생성된 dict에서 `EvalTask`를 재구성한다.
        알 수 없는 키는 무시하고, 누락된 선택 키는 기본값으로 보완한다.
        """
        known = {f.name for f in fields(cls)}
        clean = {k: v for k, v in payload.items() if k in known}

        tools_raw = clean.get("tools") or []
        clean["tools"] = [
            t if isinstance(t, ToolSpec) else ToolSpec(**t) for t in tools_raw
        ]

        calls_raw = clean.get("expected_tool_calls")
        if calls_raw is not None:
            clean["expected_tool_calls"] = [
                c if isinstance(c, ExpectedToolCall) else ExpectedToolCall(**c)
                for c in calls_raw
            ]
        return cls(**clean)


def is_eval_task(obj: Any) -> bool:
    """
    (en) Light-weight type guard (avoids importing `EvalTask` at type-check time
    in modules that only need a runtime check).
    (kr) 런타임 타입 가드이다(타입 체크만 필요한 모듈에서 `EvalTask` import를 피할 수 있다).
    """
    return is_dataclass(obj) and isinstance(obj, EvalTask)
