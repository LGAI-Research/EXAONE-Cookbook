"""
(en) Bootstrap confidence interval helper for metric summaries. Pure stdlib so eval/
remains lightweight; no numpy / scipy dependency.

(kr) metric 요약용 bootstrap 신뢰구간 헬퍼. eval/ 모듈을 가볍게 유지하기 위해 numpy/
scipy 의존성 없이 표준 라이브러리만 사용한다.
"""
from __future__ import annotations

import random
import statistics
from typing import Sequence


def bootstrap_ci(
    samples: Sequence[float],
    *,
    n_resample: int = 1000,
    alpha: float = 0.05,
    seed: int | None = 42,
) -> tuple[float, float]:
    """
    (en) Percentile bootstrap (1 − alpha) CI for the mean of `samples`.
    Returns (low, high). Empty input -> (nan, nan); singleton -> (x, x).

    (kr) `samples` 평균에 대한 percentile bootstrap (1 − alpha) 신뢰구간.
    빈 입력은 (nan, nan), 단일 원소는 (x, x)를 반환한다.
    """
    if not samples:
        return float("nan"), float("nan")
    if len(samples) == 1:
        return float(samples[0]), float(samples[0])
    rng = random.Random(seed)
    n = len(samples)
    means: list[float] = []
    for _ in range(n_resample):
        means.append(
            statistics.fmean(samples[rng.randrange(n)] for _ in range(n))
        )
    means.sort()
    lo_idx = max(0, int((alpha / 2) * n_resample) - 1)
    hi_idx = min(n_resample - 1, int((1 - alpha / 2) * n_resample) - 1)
    return float(means[lo_idx]), float(means[hi_idx])


def mean(samples: Sequence[float]) -> float:
    """
    (en) Defensive mean: returns 0.0 on empty input (vs raising).

    (kr) 방어적 평균: 빈 입력에는 0.0을 반환한다.
    """
    if not samples:
        return 0.0
    return float(statistics.fmean(samples))


__all__ = ["bootstrap_ci", "mean"]
