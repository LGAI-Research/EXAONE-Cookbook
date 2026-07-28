"""
(en) Core-only environment variables. Loaded from a single root/.env and exposed only through getters here. Other core modules must not read os.environ directly; use getters from this module only.

(kr) core 전용 환경변수다. root/.env 한 곳에서만 로드하고, 여기서만 읽어 getter로 노출한다. 다른 core 모듈은 os.environ을 직접 쓰지 말고 이 모듈의 getter만 사용한다.
"""
from __future__ import annotations

import os
from pathlib import Path

# (en) Project root relative to exaone package (exaone/config.py -> exaone/ -> root)
# (kr) exaone 패키지 기준 프로젝트 루트(exaone/config.py -> exaone/ -> 루트)
_CORE_DIR = Path(__file__).resolve().parent
_ROOT = _CORE_DIR.parent
_ENV_PATH = _ROOT / ".env"

_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    if _ENV_PATH.is_file():
        with open(_ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"").strip()
                    if " #" in v:
                        v = v.split(" #", 1)[0].strip()
                    if k:
                        os.environ.setdefault(k, v)
    _loaded = True


def _env(key: str, default: str = "") -> str:
    _ensure_loaded()
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    v = _env(key)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    v = _env(key).lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


# (en) ----- Context length (128k recommended, 256k hard cap) -----
# (kr) ----- 컨텍스트 길이(128k 권장, 256k 상한) -----
def get_context_length_max_tokens() -> int:
    """
    (en) Model context upper bound in tokens. .env: CORE_CONTEXT_LENGTH_MAX_TOKENS (default 256000).

    (kr) 모델 컨텍스트 상한(토큰)이다. .env: CORE_CONTEXT_LENGTH_MAX_TOKENS (기본 256000).
    """
    return _env_int("CORE_CONTEXT_LENGTH_MAX_TOKENS", 256_000)


def get_context_length_recommended_tokens() -> int:
    """
    (en) Recommended context length in tokens. .env: CORE_CONTEXT_LENGTH_RECOMMENDED_TOKENS (default 128000).

    (kr) 권장 컨텍스트 길이(토큰)이다. .env: CORE_CONTEXT_LENGTH_RECOMMENDED_TOKENS (기본 128000).
    """
    return _env_int("CORE_CONTEXT_LENGTH_RECOMMENDED_TOKENS", 128_000)


def get_chars_per_token_estimate() -> int:
    """
    (en) Characters-per-token ratio for token estimation (mixed Korean/English). .env: CORE_CHARS_PER_TOKEN_ESTIMATE (default 4).

    (kr) 토큰 추정용 문자당 비율(한/영 혼합)이다. .env: CORE_CHARS_PER_TOKEN_ESTIMATE (기본 4).
    """
    return _env_int("CORE_CHARS_PER_TOKEN_ESTIMATE", 4)


def get_context_tool_verbatim_max_tokens() -> int:
    """
    (en) Maximum verbatim tool-result length in tokens when compressing context. .env: CORE_CONTEXT_TOOL_VERBATIM_MAX_TOKENS (default 4096).

    (kr) 압축 시 tool 결과 원문 보존 최대 길이(토큰)이다. .env: CORE_CONTEXT_TOOL_VERBATIM_MAX_TOKENS (기본 4096).
    """
    return _env_int("CORE_CONTEXT_TOOL_VERBATIM_MAX_TOKENS", 4_096)


# (en) ----- RAG / agent context caps -----
# (kr) ----- RAG·에이전트 컨텍스트 상한 -----
def get_default_max_context_chars() -> int:
    """
    (en) Maximum character count for context in RAG and similar paths. .env: CORE_DEFAULT_MAX_CONTEXT_CHARS (default 500000).

    (kr) RAG 등에서 컨텍스트로 넣을 최대 문자 수이다. .env: CORE_DEFAULT_MAX_CONTEXT_CHARS (기본 500000).
    """
    return _env_int("CORE_DEFAULT_MAX_CONTEXT_CHARS", 500_000)


# (en) ----- LLM HTTP, output tokens, concurrency, batch (same keys as .env.example) -----
# (kr) ----- LLM HTTP·출력 토큰·동시성·배치(.env.example과 동일 키) -----
def get_llm_connect_timeout_s() -> int:
    """
    (en) ExaoneAPIClient connect timeout in seconds. .env: CORE_LLM_CONNECT_TIMEOUT_S (default 20).

    (kr) ExaoneAPIClient 연결 타임아웃(초)이다. .env: CORE_LLM_CONNECT_TIMEOUT_S (기본 20).
    """
    v = _env_int("CORE_LLM_CONNECT_TIMEOUT_S", 20)
    return v if v >= 1 else 20


def get_llm_read_timeout_s() -> int:
    """
    (en) ExaoneAPIClient read timeout in seconds. .env: CORE_LLM_READ_TIMEOUT_S (default 120).

    (kr) ExaoneAPIClient 읽기 타임아웃(초)이다. .env: CORE_LLM_READ_TIMEOUT_S (기본 120).
    """
    v = _env_int("CORE_LLM_READ_TIMEOUT_S", 120)
    return v if v >= 1 else 120


def get_mcp_tool_timeout_s() -> int:
    """
    (en) Upper bound in seconds for MCP `session.call_tool`; used by Track 03 `mcp_demo` and notebooks. .env: MCP_TOOL_TIMEOUT_S (default 60).

    (kr) MCP `session.call_tool` 상한(초). Track 03 `mcp_demo`·노트북에서 사용. .env: MCP_TOOL_TIMEOUT_S (기본 60).
    """
    v = _env_int("MCP_TOOL_TIMEOUT_S", 60)
    return v if v >= 1 else 60


def get_max_new_tokens_default() -> int:
    """
    (en) Default max_new_tokens for generation. .env: CORE_MAX_NEW_TOKENS_DEFAULT (default 4096).

    (kr) 생성 max_new_tokens 기본값이다. .env: CORE_MAX_NEW_TOKENS_DEFAULT (기본 4096).
    """
    v = _env_int("CORE_MAX_NEW_TOKENS_DEFAULT", 4_096)
    return v if v >= 1 else 4_096


def get_max_new_tokens_cap_hint() -> int:
    """
    (en) Recommended ceiling before team review when raising max_new_tokens. .env: CORE_MAX_NEW_TOKENS_CAP_HINT (default 8192).

    (kr) max_new_tokens 상향 전 팀 리뷰 권장 상한이다. .env: CORE_MAX_NEW_TOKENS_CAP_HINT (기본 8192).
    """
    v = _env_int("CORE_MAX_NEW_TOKENS_CAP_HINT", 8_192)
    return v if v >= 1 else 8_192


def get_max_in_flight_per_worker() -> int:
    """
    (en) Recommended upper bound for concurrent LLM requests per process/worker. .env: CORE_MAX_IN_FLIGHT_PER_WORKER (default 8).

    (kr) 프로세스/워커당 동시 LLM 요청 권장 상한이다. .env: CORE_MAX_IN_FLIGHT_PER_WORKER (기본 8).
    """
    v = _env_int("CORE_MAX_IN_FLIGHT_PER_WORKER", 8)
    return v if v >= 1 else 8


def get_batch_concurrency() -> int:
    """
    (en) Recommended concurrency for batch and async multi-request workloads. .env: CORE_BATCH_CONCURRENCY (default 4).

    (kr) 배치·비동기 다건 동시성 권장값이다. .env: CORE_BATCH_CONCURRENCY (기본 4).
    """
    v = _env_int("CORE_BATCH_CONCURRENCY", 4)
    return v if v >= 1 else 4


def get_batch_min_interval_s() -> float:
    """
    (en) Minimum interval between batch requests in seconds. .env: CORE_BATCH_MIN_INTERVAL_S (default 0.05).

    (kr) 배치 요청 최소 간격(초)이다. .env: CORE_BATCH_MIN_INTERVAL_S (기본 0.05).
    """
    v = _env("CORE_BATCH_MIN_INTERVAL_S")
    if not v:
        return 0.05
    try:
        f = float(v)
        return f if f > 0 else 0.05
    except ValueError:
        return 0.05


# (en) ----- SSL -----
# (kr) ----- SSL 설정 -----
def get_disable_ssl_verify() -> bool:
    """
    (en) Disable HTTPS verification for Exaone API and similar endpoints. .env: DISABLE_SSL_VERIFY (default false).

    (kr) Exaone API 등 HTTPS 검증 비활성화 여부이다. .env: DISABLE_SSL_VERIFY (기본 false).
    """
    return _env_bool("DISABLE_SSL_VERIFY", False)


# (en) ----- In-memory memory (ledger / artifact; exaone.memory) -----
# (kr) ----- 인메모리 메모리(ledger / artifact; exaone.memory) -----
def get_memory_artifact_max_items() -> int:
    """
    (en) Default and recommended item cap for InMemoryArtifactStore; oldest items are removed when exceeded. .env: CORE_MEMORY_ARTIFACT_MAX_ITEMS (default 256).

    (kr) InMemoryArtifactStore 기본·권장 상한(개수)이다. 초과 시 가장 오래된 항목부터 제거한다. .env: CORE_MEMORY_ARTIFACT_MAX_ITEMS (기본 256).
    """
    v = _env_int("CORE_MEMORY_ARTIFACT_MAX_ITEMS", 256)
    return v if v >= 1 else 256


def get_memory_ledger_max_entries() -> int:
    """
    (en) Default and recommended row cap for InMemoryLedger; oldest entries are removed when exceeded. .env: CORE_MEMORY_LEDGER_MAX_ENTRIES (default 10000).

    (kr) InMemoryLedger 기본·권장 상한(행 수)이다. 초과 시 가장 오래된 항목부터 제거한다. .env: CORE_MEMORY_LEDGER_MAX_ENTRIES (기본 10000).
    """
    v = _env_int("CORE_MEMORY_LEDGER_MAX_ENTRIES", 10_000)
    return v if v >= 1 else 10_000


def load_project_env() -> Path | None:
    """
    (en) Read the repository root `.env` once and inject keys into `os.environ` via setdefault; existing keys are not overwritten. Returns `None` if `.env` is missing.

    (kr) 레포지토리 루트의 `.env`를 한 번 읽어 `os.environ`에 setdefault로 주입한다. 이미 설정된 키는 덮어쓰지 않는다. `.env`가 없으면 `None`을 반환한다.
    """
    _ensure_loaded()
    return _ENV_PATH if _ENV_PATH.is_file() else None


def project_root() -> Path:
    """
    (en) Repository root (parent directory of the `exaone/` package).

    (kr) 레포지토리 루트(`exaone/` 패키지의 부모 디렉터리)이다.
    """
    return _ROOT


def get_memory_tool_result_min_bytes() -> int:
    """
    (en) Minimum serialized byte size (approximate) before `store_large_tool_result` stores to an artifact. .env: CORE_MEMORY_TOOL_RESULT_MIN_BYTES (default 2048).

    (kr) `store_large_tool_result`가 artifact로 넘기기 직전 직렬화 최소 바이트(대략)이다. .env: CORE_MEMORY_TOOL_RESULT_MIN_BYTES (기본 2048).
    """
    v = _env_int("CORE_MEMORY_TOOL_RESULT_MIN_BYTES", 2_048)
    return v if v >= 1 else 2_048


__all__ = [
    "load_project_env",
    "project_root",
    "get_context_length_max_tokens",
    "get_context_length_recommended_tokens",
    "get_chars_per_token_estimate",
    "get_context_tool_verbatim_max_tokens",
    "get_default_max_context_chars",
    "get_llm_connect_timeout_s",
    "get_llm_read_timeout_s",
    "get_mcp_tool_timeout_s",
    "get_max_new_tokens_default",
    "get_max_new_tokens_cap_hint",
    "get_max_in_flight_per_worker",
    "get_batch_concurrency",
    "get_batch_min_interval_s",
    "get_disable_ssl_verify",
    "get_memory_artifact_max_items",
    "get_memory_ledger_max_entries",
    "get_memory_tool_result_min_bytes",
]
