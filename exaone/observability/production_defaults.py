"""
(en) Recommended defaults for cost, quota, and concurrency (guidelines). Adjust for environment, model, and Friendli limits. May overlap with config getters; this module centralizes production advisory numbers.

(kr) 비용·쿼터·동시성 권장 기본값(가이드라인)이다. 환경·모델·Friendli 한도에 따라 조정한다. config getter와 중복될 수 있으나 ‘실무 권고 숫자’를 한곳에 두기 위한 모듈이다.
"""
from __future__ import annotations

# (en) HTTP client (ExaoneAPIClient): reference connect/read timeout caps
# (kr) HTTP 클라이언트(ExaoneAPIClient) 연결·읽기 타임아웃 상한 참고
RECOMMEND_CONNECT_TIMEOUT_S = 20
RECOMMEND_READ_TIMEOUT_S = 120

# (en) Max concurrent LLM requests per process/worker (OOM and rate-limit relief)
# (kr) 프로세스·워커당 동시 LLM 요청 수(OOM·레이트리밋 완화)
RECOMMEND_MAX_IN_FLIGHT_PER_WORKER = 8

# (en) Batch (async multi-request): use sleep/backoff to smooth QPS and bursts
# (kr) 배치(비동기 다건). QPS·버스트 완화를 위해 sleep/backoff를 함께 쓴다
RECOMMEND_BATCH_CONCURRENCY = 4
# (en) ~20 req/s cap feel (reference only)
# (kr) 약 20 req/s 상한 느낌(참고)
RECOMMEND_BATCH_MIN_INTERVAL_S = 0.05

# (en) max_new_tokens: context cap, cost, latency — recommended ceiling (details in CORE_* env)
# (kr) max_new_tokens. 컨텍스트 상한·비용·지연 권장 상한(세부는 CORE_* env)
RECOMMEND_MAX_NEW_TOKENS_DEFAULT = 4096
# (en) Team review recommended before raising above this
# (kr) 이 값 이상으로 올리기 전 팀 리뷰를 권장한다
RECOMMEND_MAX_NEW_TOKENS_CAP_HINT = 8192

__all__ = [
    "RECOMMEND_CONNECT_TIMEOUT_S",
    "RECOMMEND_READ_TIMEOUT_S",
    "RECOMMEND_MAX_IN_FLIGHT_PER_WORKER",
    "RECOMMEND_BATCH_CONCURRENCY",
    "RECOMMEND_BATCH_MIN_INTERVAL_S",
    "RECOMMEND_MAX_NEW_TOKENS_DEFAULT",
    "RECOMMEND_MAX_NEW_TOKENS_CAP_HINT",
]
