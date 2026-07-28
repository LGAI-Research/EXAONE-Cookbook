"""
(en) Production logging and tracing field-name conventions. Use these constants when aligning structured log (JSON) or OpenTelemetry attribute keys so aggregation and dashboards stay consistent across teams and services. Values are recommended string keys only, not enforced.

(kr) 실무용 로깅·트레이싱 필드명 규칙이다. 구조화 로그(JSON)나 OpenTelemetry attribute 키를 맞출 때 이 상수를 쓰면 팀/서비스 간 집계·대시보드가 일관된다. 값은 권장 문자열 키일 뿐, 강제는 아니다.
"""
from __future__ import annotations

# (en) Per-request identifiers
# (kr) 요청 단위 식별자
REQUEST_ID = "request_id"
SESSION_ID = "session_id"
TRACE_ID = "trace_id"
SPAN_ID = "span_id"

# (en) Model and endpoint
# (kr) 모델·엔드포인트
MODEL = "model"
# (en) Slug for logs without host/path (recommended)
# (kr) 로그에는 host/path를 제외한 슬러그를 쓰는 것을 권장한다
BASE_URL = "base_url"
LATENCY_MS = "latency_ms"

# (en) Agent run metadata
# (kr) 에이전트 실행 메타데이터
# (en) e.g. ToolAgent
# (kr) 예: ToolAgent
AGENT = "agent"
TURNS_USED = "turns_used"
ENABLE_THINKING = "enable_thinking"
TOOL_AGENT_KEY = "tool_agent_key"
ANSWER_TOOL_AGENT_KEY = "answer_tool_agent_key"
# (en) Deprecated aliases
# (kr) 사용 중단된 별칭
EXPERT_KEY = TOOL_AGENT_KEY
ANSWER_EXPERT_KEY = ANSWER_TOOL_AGENT_KEY
CONTEXT_SUFFICIENT = "context_sufficient"
ENRICH_STOP_REASON = "enrich_stop_reason"
TOOL_INVOCATIONS = "tool_invocations"
PROGRESS_ACTION = "progress_action"
DUPLICATES_BLOCKED = "duplicates_blocked"

# (en) Tool invocation
# (kr) 도구 호출
TOOL_NAME = "tool_name"
TOOL_CALL_ID = "tool_call_id"
TOOL_ERROR = "tool_error"

# (en) Retrieval
# (kr) 검색(Retrieval)
# (en) vector / graph / hybrid
# (kr) vector, graph, hybrid 전략
RETRIEVAL_STRATEGY = "retrieval_strategy"
CHUNK_COUNT = "chunk_count"
TOP_K = "top_k"

# (en) Structured output
# (kr) 구조화 출력
STRUCTURED_SUCCESS = "structured_success"
STRUCTURED_ERROR = "structured_error"

# (en) LLM response quality (empty content / reasoning-only / recovery)
# (kr) LLM 응답 품질(빈 content / reasoning-only / 복구)
LLM_EMPTY_CONTENT = "llm.empty_content"
LLM_REASONING_ONLY = "llm.reasoning_only"
LLM_EMPTY_RETRY_SUCCESS = "llm.empty_retry_success"
LLM_RESPONSE_PHASE = "llm.response_phase"
LLM_FINISH_REASON = "llm.finish_reason"
# (en) Ordered list of LLM calls for one ToolAgent.run (phase, schema_name, latency_ms, …)
# (kr) ToolAgent.run 1회당 LLM 호출 목록(phase, schema_name, latency_ms 등)
LLM_CALLS = "llm_calls"

# (en) Token usage (when the provider reports usage)
# (kr) 토큰 사용량(provider usage가 있을 때 반영)
INPUT_TOKENS = "input_tokens"
OUTPUT_TOKENS = "output_tokens"

__all__ = [
    "REQUEST_ID",
    "SESSION_ID",
    "TRACE_ID",
    "SPAN_ID",
    "MODEL",
    "BASE_URL",
    "LATENCY_MS",
    "AGENT",
    "TURNS_USED",
    "ENABLE_THINKING",
    "TOOL_AGENT_KEY",
    "ANSWER_TOOL_AGENT_KEY",
    "EXPERT_KEY",
    "ANSWER_EXPERT_KEY",
    "CONTEXT_SUFFICIENT",
    "ENRICH_STOP_REASON",
    "TOOL_INVOCATIONS",
    "PROGRESS_ACTION",
    "DUPLICATES_BLOCKED",
    "TOOL_NAME",
    "TOOL_CALL_ID",
    "TOOL_ERROR",
    "RETRIEVAL_STRATEGY",
    "CHUNK_COUNT",
    "TOP_K",
    "STRUCTURED_SUCCESS",
    "STRUCTURED_ERROR",
    "LLM_EMPTY_CONTENT",
    "LLM_REASONING_ONLY",
    "LLM_EMPTY_RETRY_SUCCESS",
    "LLM_RESPONSE_PHASE",
    "LLM_FINISH_REASON",
    "LLM_CALLS",
    "INPUT_TOKENS",
    "OUTPUT_TOKENS",
]
