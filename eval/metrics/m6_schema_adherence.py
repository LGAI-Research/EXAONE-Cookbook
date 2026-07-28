"""
(en) M6 — Schema Adherence (strict / loose).

- strict: extraction succeeds **and** all required keys / JSON schema constraints pass
  using only `JsonExtractor`. This mirrors a naive caller that does `json.loads` and
  validates.
- loose: same, but allowed to use `JsonExtractor → AutoRepair` (the harness pipeline).

`repair_gain = loose − strict` is the net contribution of the harness repair stage.

Heavy lifting is delegated to the production `exaone.output` modules so the metric
measures exactly what the harness ships. Imports are lazy so the module still loads
in an environment without `exaone/` (e.g. for offline unit tests against fixtures).

Reference: IFEval strict / loose accuracy (Zhou et al. 2023), PLAYBOOK Part 7.1.

(kr) M6 — Schema Adherence (strict / loose).

- strict: `JsonExtractor`만으로 추출 성공 **및** 필수 키 / JSON 스키마 통과.
  naive 호출부가 `json.loads` + 검증하는 케이스에 대응.
- loose: 동일 검증이되 `JsonExtractor → AutoRepair`(하네스 파이프라인) 사용 허용.

`repair_gain = loose − strict`는 하네스 repair 단계의 순 기여분.

핵심 로직은 `exaone.output` 모듈에 위임해 하네스와 동일한 정의를 측정한다. `exaone/`
없이도 모듈이 import되도록 lazy import.

참조: IFEval strict / loose accuracy (Zhou et al. 2023), PLAYBOOK Part 7.1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


@dataclass(frozen=True)
class SchemaSpec:
    """
    (en) Per-task schema expectation; either or both fields may be set.

    (kr) 태스크별 스키마 기대치; 둘 중 하나 또는 둘 다 설정 가능.
    """

    required_keys: list[str] | None = None
    json_schema: dict[str, Any] | None = None


def _load_extractors():
    """
    (en) Lazy import so tests can run without the full harness installed.
    Returns (JsonExtractor, AutoRepair, SchemaValidator) or raises ImportError.

    (kr) 전체 하네스 미설치 환경에서도 import할 수 있도록 lazy import.
    """
    from exaone.output import AutoRepair, JsonExtractor, SchemaValidator

    return JsonExtractor, AutoRepair, SchemaValidator


def _validate(data: Any, spec: SchemaSpec, SchemaValidator) -> bool:
    validator = SchemaValidator(
        required_keys=spec.required_keys,
        json_schema=spec.json_schema,
    )
    return bool(validator.validate_data(data).success)


def score_trial(
    trial: TrialResult,
    spec: SchemaSpec,
) -> tuple[bool, bool]:
    """
    (en) Returns (strict_pass, loose_pass).

    (kr) (strict 통과 여부, loose 통과 여부)를 반환.
    """
    JsonExtractor, AutoRepair, SchemaValidator = _load_extractors()
    raw = trial.final_content or ""
    extractor = JsonExtractor()
    repair = AutoRepair()

    strict_pass = False
    extracted = extractor.process(raw)
    if extracted.success and extracted.data is not None:
        strict_pass = _validate(extracted.data, spec, SchemaValidator)

    loose_pass = strict_pass
    if not loose_pass:
        repaired = repair.process(raw)
        if repaired.success and repaired.data is not None:
            loose_pass = _validate(repaired.data, spec, SchemaValidator)

    return strict_pass, loose_pass


def compute(
    trials: Sequence[TrialResult],
    specs_by_task: Mapping[str, SchemaSpec],
) -> MetricSummary:
    """
    (en) Compute strict / loose / repair-gain across trials.

    (kr) trial 전체에 대해 strict / loose / repair-gain을 계산.
    """
    strict_scores: list[float] = []
    loose_scores: list[float] = []
    for t in trials:
        spec = specs_by_task.get(t.task_id)
        if spec is None:
            continue
        s, l = score_trial(t, spec)
        strict_scores.append(1.0 if s else 0.0)
        loose_scores.append(1.0 if l else 0.0)

    strict = mean(strict_scores)
    loose = mean(loose_scores)
    lo, hi = bootstrap_ci(loose_scores)
    return MetricSummary(
        metric_id="M6",
        name="Schema Adherence",
        value=loose,
        n=len(loose_scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "strict": strict,
            "loose": loose,
            "repair_gain": loose - strict,
            "mode": "json_schema",
        },
        notes="loose = strict + AutoRepair recovery",
    )


__all__ = ["SchemaSpec", "score_trial", "compute"]
