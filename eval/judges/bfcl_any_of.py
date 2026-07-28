"""
(en) BFCL any-of judge — deterministic, no LLM required.

BFCL's `possible_answer` files give a list of accepted values per argument; this
judge scores a trial 1.0 iff the trial's tool calls include at least one call
that matches the gold function name AND every argument value is one of the
accepted alternatives (after `_canonical.normalize_scalar`).

It is used as the M1 scorer for BFCL `simple` / `multiple` / `parallel` tasks
where success means "the model would have produced one of the accepted calls".
For `irrelevance` use M5 (abstention) instead.

(kr) BFCL any-of judge — LLM 없이 결정론적 채점.

BFCL의 `possible_answer`는 인자별 허용값 리스트를 준다. 본 judge는 trial의 도구 호출
중 (정답 함수 이름과 일치하면서) 모든 인자 값이 허용 alternatives 중 하나에 해당하는
호출이 한 건이라도 있으면 1.0, 아니면 0.0을 반환한다(`_canonical.normalize_scalar` 적용).

BFCL `simple` / `multiple` / `parallel`의 M1 scorer로 쓴다. "모델이 허용된 호출 중
하나를 만들었으면 성공" 의미. `irrelevance`는 M5(abstention)로 별도 처리.
"""
from __future__ import annotations

from typing import Any, Mapping

from eval.metrics._canonical import normalize_bfcl_value, normalize_scalar
from eval.metrics.m3_tool_selection import normalize_tool_name
from eval.metrics.types import TrialResult


def _value_in_choices(value: Any, choices: list[Any]) -> bool:
    """
    (en) True iff `value` matches at least one of `choices` after normalization.
    Empty-string choice means "argument may be omitted"; ignored here because we
    only call this on values actually passed by the model.

    (kr) `value`가 정규화 후 `choices` 중 하나와 일치하면 True. BFCL의 빈 문자열 choice는
    "인자 생략 가능"을 의미하므로 본 함수(모델이 실제 전달한 값에만 호출)에서는 무시.
    """
    if not isinstance(choices, list):
        return normalize_bfcl_value(value) == normalize_bfcl_value(choices)
    nv = normalize_bfcl_value(value)
    for c in choices:
        if c == "":
            continue
        if normalize_bfcl_value(c) == nv:
            return True
        if isinstance(c, list) and any(normalize_bfcl_value(x) == nv for x in c):
            return True
    return False


def _call_matches_gold(
    call_name: str,
    call_args: Mapping[str, Any],
    gold_entry: Mapping[str, Mapping[str, list[Any]]],
) -> bool:
    """
    (en) BFCL gold entry shape: ``{"<func_name>": {"<arg>": [accepted_val_1, ...]}}``.
    Returns True iff `call_name` matches the gold func_name (after
    `normalize_tool_name`) AND every gold-required argument value the model
    passed is one of the accepted alternatives. Extra arguments the model passed
    that are not in the gold spec are ignored (BFCL evaluates per-argument).

    (kr) BFCL gold 항목 형식: ``{"<func_name>": {"<arg>": [accepted_val_1, ...]}}``.
    `call_name`이 gold func_name과 일치하고(정규화 후), gold가 요구한 인자 각각의 값이
    허용 alternatives 중 하나면 True. 모델이 전달한 추가 인자는 무시(BFCL은 인자 단위 평가).
    """
    for gold_func_name, gold_args in gold_entry.items():
        if normalize_tool_name(call_name) != normalize_tool_name(gold_func_name):
            continue
        ok = True
        for arg_name, choices in gold_args.items():
            if arg_name not in call_args:
                if isinstance(choices, list) and "" in choices:
                    continue
                ok = False
                break
            if not _value_in_choices(call_args[arg_name], choices):
                ok = False
                break
        if ok:
            return True
    return False


class BFCLAnyOfJudge:
    """
    (en) Judge callable. `gold` must contain `bfcl_ground_truth` (the list-of-dict
    shape preserved by `eval.datasets.bfcl_v3` in `EvalTask.metadata`).

    Scoring rule (matches BFCL v3 AST evaluator semantics):

    - For every gold entry (each ``{func_name: args}``), find a matching call in
      ``trial.tool_calls``. Score = 1.0 iff every gold entry has a match.
    - When the gold list has more than one entry (parallel/multiple), the model
      must produce a matching call for each (set semantics, not order).

    (kr) judge callable. `gold`에는 `bfcl_ground_truth`(`eval.datasets.bfcl_v3`가
    `EvalTask.metadata`에 보존한 list-of-dict 형식)가 포함되어야 한다.

    채점 규칙(BFCL v3 AST evaluator 의미와 일치):

    - 각 gold 항목(``{func_name: args}``)마다 ``trial.tool_calls``에서 매칭 호출을 찾는다.
      모든 gold 항목이 매칭되면 1.0.
    - gold 리스트가 여러 개(parallel/multiple)일 때, 모델은 각각에 대해 매칭 호출을
      만들어야 한다(순서 무관 set 의미).
    """

    def __call__(self, *, trial: TrialResult, gold: Mapping[str, Any]) -> float:
        gt = gold.get("bfcl_ground_truth")
        if not gt:
            return 0.0
        if not trial.tool_calls:
            return 0.0
        remaining_calls = [(c.name, dict(c.arguments)) for c in trial.tool_calls]
        for gold_entry in gt:
            match_idx = next(
                (
                    i
                    for i, (n, a) in enumerate(remaining_calls)
                    if _call_matches_gold(n, a, gold_entry)
                ),
                None,
            )
            if match_idx is None:
                return 0.0
            remaining_calls.pop(match_idx)
        return 1.0


__all__ = ["BFCLAnyOfJudge"]
