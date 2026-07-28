"""
(en) M6 — IFEval verifiable instruction adherence (strict / loose).

Uses the Google IFEval checker registry under ``eval/ifeval/`` (vendored from
lm-evaluation-harness). For each trial:

- **strict**: ``test_instruction_following_strict`` on raw ``final_content``.
- **loose**: ``test_instruction_following_loose`` (IFEval upper-bound variants:
  drop first/last line, strip ``*``, etc.).

``repair_gain = loose − strict`` mirrors JSON-schema M6 naming; for IFEval it
captures how often harness-style response cleanup would flip a fail to pass.

Reference: Zhou et al. 2023 (IFEval), ``eval/metrics/m6_schema_adherence.py``.

(kr) M6 — IFEval verifiable instruction 준수(strict / loose).

``eval/ifeval/``의 Google IFEval checker registry 사용(lm-evaluation-harness vendored).
trial별:

- **strict**: raw ``final_content``에 ``test_instruction_following_strict`` 적용.
- **loose**: ``test_instruction_following_loose``(첫/마지막 줄 제거, ``*`` 제거 등 IFEval upper-bound).

``repair_gain = loose − strict``는 JSON schema M6와 이름을 맞춘 것이며, IFEval에서는
응답 정리로 fail→pass가 얼마나 되는지를 나타낸다.

참조: Zhou et al. 2023 (IFEval), ``eval/metrics/m6_schema_adherence.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from eval.ifeval.utils import InputExample, test_instruction_following_loose, test_instruction_following_strict
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


@dataclass(frozen=True)
class IFEvalSpec:
    """
    (en) Per-task IFEval payload from ``EvalTask.metadata["ifeval_instructions"]``.

    (kr) ``EvalTask.metadata["ifeval_instructions"]``에서 온 task별 IFEval payload.
    """

    prompt: str
    instructions: list[dict[str, Any]]


def spec_from_task_metadata(
    *,
    prompt: str,
    instructions: list[dict[str, Any]] | None,
) -> IFEvalSpec | None:
    """
    (en) Build ``IFEvalSpec`` when the instruction list is non-empty.

    (kr) instruction 리스트가 비어있지 않을 때 ``IFEvalSpec`` 생성.
    """
    rows = instructions or []
    if not rows:
        return None
    return IFEvalSpec(prompt=prompt, instructions=list(rows))


def _to_input_example(spec: IFEvalSpec, *, key: int = 0) -> InputExample:
    return InputExample(
        key=key,
        instruction_id_list=[str(row["id"]) for row in spec.instructions],
        prompt=spec.prompt,
        kwargs=[dict(row.get("kwargs") or {}) for row in spec.instructions],
    )


def score_trial(trial: TrialResult, spec: IFEvalSpec) -> tuple[bool, bool]:
    """
    (en) Returns (strict_pass, loose_pass) for one IFEval task response.

    (kr) IFEval task 응답 하나에 대한 (strict_pass, loose_pass) 반환.
    """
    inp = _to_input_example(spec)
    response = trial.final_content or ""
    strict = test_instruction_following_strict(inp, response)
    loose = test_instruction_following_loose(inp, response)
    return strict.follow_all_instructions, loose.follow_all_instructions


def compute(
    trials: Sequence[TrialResult],
    specs_by_task: Mapping[str, IFEvalSpec],
) -> MetricSummary:
    """
    (en) Aggregate strict / loose / repair-gain over IFEval tasks.

    (kr) IFEval task에 대해 strict / loose / repair-gain 집계.
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
            "mode": "ifeval",
        },
        notes="IFEval prompt-level strict/loose (all instructions must pass)",
    )


def merge_m6_summaries(parts: Sequence[MetricSummary]) -> MetricSummary:
    """
    (en) Weighted merge of multiple M6 summaries (e.g. JSON schema + IFEval batches).

    (kr) 여러 M6 요약(JSON schema + IFEval batch 등)을 가중 병합.
    """
    usable = [p for p in parts if p.n > 0]
    if not usable:
        raise ValueError("merge_m6_summaries requires at least one non-empty summary")
    if len(usable) == 1:
        return usable[0]

    total_n = sum(p.n for p in usable)
    strict = sum(float(p.breakdown.get("strict", p.value)) * p.n for p in usable) / total_n
    loose = sum(float(p.value) * p.n for p in usable) / total_n
    modes = sorted({str(p.breakdown.get("mode", "schema")) for p in usable})
    return MetricSummary(
        metric_id="M6",
        name="Schema Adherence",
        value=loose,
        n=total_n,
        ci_low=None,
        ci_high=None,
        breakdown={
            "strict": strict,
            "loose": loose,
            "repair_gain": loose - strict,
            "mode": "+".join(modes),
        },
        notes="merged M6: " + ", ".join(f"{p.n} from {p.breakdown.get('mode', 'schema')}" for p in usable),
    )


__all__ = [
    "IFEvalSpec",
    "spec_from_task_metadata",
    "score_trial",
    "compute",
    "merge_m6_summaries",
]
