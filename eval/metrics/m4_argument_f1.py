"""
(en) M4 — Argument F1 (parameter validity).

For each (predicted call, gold call) pair we measure how well the predicted argument
dict matches the gold dict. The per-call F1 is computed over **key-value pairs**:

- key set match: predicted argument names ∩ gold argument names.
- value match: BFCL-style `values_match` per shared key.
- precision = matched_pairs / |pred_args|
- recall    = matched_pairs / |gold_args|
- F1        = 2pr / (p + r)

A trial's score is the average F1 across its (call, gold) pairings; calls are paired
greedily by tool name (after `m3_tool_selection.normalize_tool_name`). Extra predicted
calls without a gold counterpart contribute 0 to precision; extra gold calls without a
predicted counterpart contribute 0 to recall.

Reference: BFCL v3 AST sub-tree matching, Toolscore Argument F1 (weight 0.30).

(kr) M4 — Argument F1 (인자 정확도).

(예측 호출, 정답 호출) 쌍마다 인자 dict 일치도를 측정한다. 호출당 F1은 **key-value 쌍**
기준으로 계산한다.

- key 집합 매칭: 예측 인자 이름 ∩ 정답 인자 이름.
- 값 매칭: 공통 키에 대해 BFCL 스타일 `values_match`.
- precision = matched_pairs / |pred_args|
- recall    = matched_pairs / |gold_args|
- F1        = 2pr / (p + r)

trial 점수는 (호출, 정답) 쌍별 F1의 평균. 호출 매칭은 도구 이름(`m3.normalize_tool_name`
적용 후) 기준 그리디 매칭. 정답이 없는 예측 호출은 precision에 0 기여, 예측이 없는 정답
호출은 recall에 0 기여.

참조: BFCL v3 AST sub-tree matching, Toolscore Argument F1 (가중치 0.30).
"""
from __future__ import annotations

from typing import Mapping, Sequence

from eval.metrics._canonical import values_match
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, ToolCallRecord, TrialResult
from eval.metrics.m3_tool_selection import normalize_tool_name


def _arg_f1(pred_args: Mapping[str, object], gold_args: Mapping[str, object]) -> float:
    shared = set(pred_args.keys()) & set(gold_args.keys())
    matched = sum(1 for k in shared if values_match(pred_args[k], gold_args[k]))
    if not pred_args and not gold_args:
        return 1.0
    p = matched / len(pred_args) if pred_args else 0.0
    r = matched / len(gold_args) if gold_args else 0.0
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def _pair_calls(
    pred: Sequence[ToolCallRecord], gold: Sequence[ToolCallRecord]
) -> list[tuple[ToolCallRecord | None, ToolCallRecord | None]]:
    """
    (en) Greedy pairing by normalized tool name (first-match). Unmatched calls on
    either side are returned as (call, None) or (None, call).

    (kr) 정규화된 도구 이름 기준 그리디 매칭(first-match). 한쪽에만 남은 호출은
    (call, None) 또는 (None, call)로 반환.
    """
    remaining_gold = list(gold)
    pairs: list[tuple[ToolCallRecord | None, ToolCallRecord | None]] = []
    for p in pred:
        pname = normalize_tool_name(p.name)
        match_idx = next(
            (i for i, g in enumerate(remaining_gold) if normalize_tool_name(g.name) == pname),
            None,
        )
        if match_idx is None:
            pairs.append((p, None))
        else:
            pairs.append((p, remaining_gold.pop(match_idx)))
    for g in remaining_gold:
        pairs.append((None, g))
    return pairs


def score_trial(trial: TrialResult, gold: Sequence[ToolCallRecord]) -> float:
    """
    (en) Average call-level F1 for one trial. Returns 1.0 when both sides have no calls.

    (kr) trial 한 건의 호출 단위 F1 평균. 양쪽 모두 호출이 없으면 1.0.
    """
    pairs = _pair_calls(trial.tool_calls, gold)
    if not pairs:
        return 1.0
    scores: list[float] = []
    for p, g in pairs:
        if p is None or g is None:
            scores.append(0.0)
        else:
            scores.append(_arg_f1(p.arguments, g.arguments))
    return mean(scores)


def compute(
    trials: Sequence[TrialResult],
    gold_calls_by_task: Mapping[str, Sequence[ToolCallRecord]],
) -> MetricSummary:
    """
    (en) Average per-trial argument F1 across all trials.

    (kr) 모든 trial의 인자 F1 평균.
    """
    scores: list[float] = []
    for t in trials:
        gold = gold_calls_by_task.get(t.task_id)
        if gold is None:
            continue
        scores.append(score_trial(t, gold))

    value = mean(scores)
    lo, hi = bootstrap_ci(scores)
    return MetricSummary(
        metric_id="M4",
        name="Argument F1",
        value=value,
        n=len(scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={},
        notes="key-value F1 averaged over greedy name-paired calls",
    )


__all__ = ["score_trial", "compute"]
