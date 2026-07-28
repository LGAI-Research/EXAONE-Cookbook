"""
(en) Public API for the M1–M10 metric suite. Each `mN_*` module exposes a `compute(...)`
function returning a `MetricSummary`; this package re-exports them under short aliases
so callers can write:

```python
from eval.metrics import m1_task_success, m2_pass_k, ...
summary = m1_task_success.compute(trials, golds, mode="exact")
```

`MetricSummary`, `TrialResult`, `ToolCallRecord` and the helper `bootstrap_ci` are also
re-exported for convenience.

(kr) M1–M10 metric 스위트의 public API. 각 `mN_*` 모듈은 `MetricSummary`를 반환하는
`compute(...)` 함수를 노출하며, 이 패키지는 짧은 별칭으로 재노출한다.

```python
from eval.metrics import m1_task_success, m2_pass_k, ...
summary = m1_task_success.compute(trials, golds, mode="exact")
```

`MetricSummary`, `TrialResult`, `ToolCallRecord`와 헬퍼 `bootstrap_ci`도 편의를 위해
재노출한다.
"""
from __future__ import annotations

from eval.metrics import (
    m1_task_success,
    m10_empty_recovery,
    m2_pass_k,
    m3_tool_selection,
    m4_argument_f1,
    m5_abstention,
    m6_ifeval,
    m6_schema_adherence,
    m7_efficiency,
    m8_redundancy,
    m9_faithfulness,
)
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, ToolCallRecord, TrialResult

__all__ = [
    "m1_task_success",
    "m10_empty_recovery",
    "m2_pass_k",
    "m3_tool_selection",
    "m4_argument_f1",
    "m5_abstention",
    "m6_ifeval",
    "m6_schema_adherence",
    "m7_efficiency",
    "m8_redundancy",
    "m9_faithfulness",
    "MetricSummary",
    "TrialResult",
    "ToolCallRecord",
    "bootstrap_ci",
    "mean",
]
