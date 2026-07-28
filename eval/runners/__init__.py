"""
(en) Runners turn one `EvalTask` into one `TrialResult` (the input schema for
`eval/metrics/`). Two implementations are provided:

- `naive_runner.run_trial` — pure `requests.post` against any OpenAI-compatible
  endpoint (Friendli default). No recovery, no ledger, no JSON repair.
- `harness_runner.run_trial` — `exaone.agents.ToolAgent.run()` wrapper. All harness
  features active (empty-200 retry, ToolInvocationLedger, NextStepPlanner, ...).

Both runners return the same `TrialResult` shape so M1–M10 can score them with
identical code paths.

(kr) Runner는 단일 `EvalTask`를 단일 `TrialResult`(`eval/metrics/`의 입력 스키마)로 변환한다.
두 구현을 제공한다.

- `naive_runner.run_trial` — OpenAI 호환 엔드포인트(기본값 Friendli)에 순수 `requests.post`.
  복구·ledger·JSON repair 모두 없음.
- `harness_runner.run_trial` — `exaone.agents.ToolAgent.run()` 래퍼. 하네스 기능 전체 활성화.

두 runner는 동일한 `TrialResult`를 반환하므로 M1–M10이 같은 코드 경로로 채점할 수 있다.
"""
from __future__ import annotations

from eval.runners import common, harness_runner, naive_runner, tau_bench_runner

__all__ = ["common", "naive_runner", "harness_runner", "tau_bench_runner"]
