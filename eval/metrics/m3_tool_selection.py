"""
(en) M3 — Tool Selection Accuracy (TSA).

Strict (BFCL): predicted multiset of tool names must equal gold multiset.
Soft (Jaccard): |pred ∩ gold| / |pred ∪ gold| on sets — useful when partial credit
is acceptable.

Tool names are normalized: the harness uses `<tool_agent_key>__<tool_name>` (e.g.
`rag__retrieve`) while gold often uses the logical form (`rag.retrieve` / `retrieve`).
We strip the catalog prefix and any `.` / `__` separators so both forms match.

Reference: BFCL v3 AST matching, Toolscore Selection Accuracy (weight 0.40).

(kr) M3 — Tool Selection Accuracy (TSA).

Strict (BFCL): 예측 도구 이름 multiset이 정답 multiset과 정확히 일치해야 한다.
Soft (Jaccard): 집합 기준 |pred ∩ gold| / |pred ∪ gold|. 부분 점수가 허용되는 환경.

도구 이름 정규화: harness는 `<tool_agent_key>__<tool_name>` (예: `rag__retrieve`),
정답은 보통 logical form(`rag.retrieve` / `retrieve`). 카탈로그 prefix와 `.` / `__`
구분자를 제거해 두 형식이 모두 매칭되도록 한다.

참조: BFCL v3 AST matching, Toolscore Selection Accuracy (가중치 0.40).
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping, Sequence

from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, ToolCallRecord, TrialResult


def normalize_tool_name(name: str) -> str:
    """
    (en) Drop catalog/agent prefix and unify separators so `rag__retrieve`,
    `rag.retrieve`, `retrieve` all collapse to `retrieve`.

    (kr) 카탈로그/에이전트 prefix를 제거하고 구분자를 통일해 `rag__retrieve`,
    `rag.retrieve`, `retrieve`를 모두 `retrieve`로 정규화한다.
    """
    n = name.strip()
    for sep in ("__", "."):
        if sep in n:
            n = n.rsplit(sep, 1)[-1]
    return n.lower()


def _pred_names(trial: TrialResult) -> list[str]:
    return [normalize_tool_name(tc.name) for tc in trial.tool_calls]


def _gold_names(gold_calls: Iterable[ToolCallRecord]) -> list[str]:
    return [normalize_tool_name(tc.name) for tc in gold_calls]


def strict_match(pred: Iterable[str], gold: Iterable[str]) -> bool:
    """
    (en) Multiset equality (counts matter, order does not).

    (kr) Multiset 동등(개수 일치, 순서 무관).
    """
    return Counter(pred) == Counter(gold)


def jaccard(pred: Iterable[str], gold: Iterable[str]) -> float:
    """
    (en) Set Jaccard similarity. Empty ∪ empty -> 1.0 (no decision is no error).

    (kr) 집합 Jaccard 유사도. 공집합끼리는 1.0(판단할 게 없으면 무오류).
    """
    p, g = set(pred), set(gold)
    if not p and not g:
        return 1.0
    return len(p & g) / len(p | g)


def compute(
    trials: Sequence[TrialResult],
    gold_calls_by_task: Mapping[str, Sequence[ToolCallRecord]],
) -> MetricSummary:
    """
    (en) Compute strict + Jaccard across trials. Skips tasks lacking gold.

    (kr) trial 전체에 대해 strict + Jaccard를 계산. gold가 없는 태스크는 제외.
    """
    strict: list[float] = []
    soft: list[float] = []
    for t in trials:
        gold = gold_calls_by_task.get(t.task_id)
        if gold is None:
            continue
        p = _pred_names(t)
        g = _gold_names(gold)
        strict.append(1.0 if strict_match(p, g) else 0.0)
        soft.append(jaccard(p, g))

    value = mean(strict)
    lo, hi = bootstrap_ci(strict)
    return MetricSummary(
        metric_id="M3",
        name="Tool Selection Accuracy",
        value=value,
        n=len(strict),
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "strict": value,
            "jaccard": mean(soft),
        },
        notes="strict = multiset equality; jaccard = set similarity",
    )


__all__ = ["normalize_tool_name", "strict_match", "jaccard", "compute"]
