"""
(en) Exaone API abstraction layer and shared interface for calling the K-EXAONE-236B-A23B model over HTTP (requests).

- base_url: OpenAI-compatible base URL (e.g. https://api.friendli.ai/serverless/v1). The client appends /chat/completions automatically.
- Single-agent flow (not multi-agent): reasoning (thinking) → tool calling → (repeat).
- Sampling: Hugging Face guidelines — temperature=1.0, top_p=0.95, do_sample=True; greedy decoding is forbidden.
- Context: up to 256k tokens; staying within 128k is recommended.

(kr) Exaone API 추상화 레이어이며, K-EXAONE-236B-A23B 모델을 HTTP(requests)로 호출하는 공통 인터페이스를 제공한다.

- base_url: OpenAI 호환 base URL(예: https://api.friendli.ai/serverless/v1)이며, /chat/completions 경로는 클라이언트가 자동으로 추가한다.
- 멀티에이전트가 아닌 싱글 에이전트 흐름은 reasoning(thinking) → tool calling → (반복)이다.
- Sampling: Hugging Face 가이드라인에 따라 temperature=1.0, top_p=0.95, do_sample=True를 사용하며 greedy 디코딩은 금지한다.
- Context: 최대 256k 토큰이며 128k 이내 유지를 권장한다.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator

from exaone.config import (
    get_disable_ssl_verify,
    get_llm_connect_timeout_s,
    get_llm_read_timeout_s,
    get_max_new_tokens_default,
)
from exaone.context_management.constants import (
    CONTEXT_LENGTH_MAX_TOKENS,
    CONTEXT_LENGTH_RECOMMENDED_TOKENS,
)

logger = logging.getLogger(__name__)

# (en) Max length for 4xx body in logs/exceptions (avoid prompt/PII/key leakage)
# (kr) 4xx 응답 본문 로그·예외용 최대 길이(프롬프트/PII·키 노출 방지)
_LOG_ERROR_BODY_MAX_LEN = 800

# (en) Sampling: greedy decoding forbidden (infinite repetition). HF guidelines
# (kr) 샘플링. greedy 디코딩 금지(무한 반복). HF 가이드라인
# (en) At 0, temperature converges to greedy — never use
# (kr) 0이면 greedy에 수렴하므로 절대 사용하지 않는다
TEMPERATURE_MIN = 0.01
TEMPERATURE_DEFAULT = 1.0
TOP_P_DEFAULT = 0.95

# (en) ----- Shared types (no DB/infra dependency) -----
# (kr) ----- 공통 타입(DB/인프라 의존 없음) -----


@dataclass
class ExaoneMessage:
    """
    (en) One chat message. Use tool_call_id when role='tool'; use tool_calls on role='assistant'.

    (kr) 채팅 메시지 단위이다. role='tool'일 때 tool_call_id를, role='assistant'에서는 tool_calls를 사용한다.
    """
    # (en) "system" | "user" | "assistant" | "tool" | "tool_declare"
    # (kr) role 값: system, user, assistant, tool, tool_declare
    role: str
    # (en) Text or multimodal content
    # (kr) 텍스트 또는 멀티모달 콘텐츠
    content: str | list[dict[str, Any]]
    name: str | None = None
    # (en) Used on role="tool" response messages
    # (kr) role="tool" 응답 메시지에서 사용
    tool_call_id: str | None = None
    # (en) Used on role="assistant" messages
    # (kr) role="assistant" 메시지에서 사용
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            d["name"] = self.name
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        return d


@dataclass
class ExaoneResponse:
    """
    (en) Model response wrapper for a single agent: content (and optional reasoning); if tool_calls are present, run tools and call the model again.

    (kr) 모델 응답 래퍼이다. 싱글 에이전트에서는 content(reasoning)와 tool_calls가 있으면 도구 실행 후 재호출한다.
    """
    content: str
    raw: Any = None
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    # (en) When set, attach tool results and loop the same agent
    # (kr) 있으면 tool 결과를 붙이고 같은 에이전트로 반복한다
    tool_calls: list[dict[str, Any]] | None = None
    # (en) API round-trip latency in ms (eval/base_agent compatibility)
    # (kr) API 호출 소요 시간(밀리초). eval/base_agent 호환용
    latency_ms: float | None = None
    # (en) Chain-of-thought from API when enable_thinking
    # (kr) enable_thinking 시 API가 반환하는 chain-of-thought(사고 과정)
    reasoning_content: str | None = None


def _validate_sampling(temperature: float, top_p: float, do_sample: bool) -> None:
    """
    (en) Enforce Hugging Face sampling guidelines: greedy decoding is never allowed (infinite repetition risk).

    (kr) Hugging Face 샘플링 가이드라인을 적용하며 greedy 디코딩은 절대 허용하지 않는다(무한 반복 위험).
    """
    if do_sample is False:
        raise ValueError(
            "do_sample=False(greedy)는 무한 반복 이슈로 사용 금지. "
            "반드시 do_sample=True 로 호출하세요."
        )
    if temperature < TEMPERATURE_MIN:
        raise ValueError(
            f"temperature는 최소 {TEMPERATURE_MIN} 이상이어야 합니다 (greedy 금지). "
            f"가이드라인: temperature={TEMPERATURE_DEFAULT}, top_p={TOP_P_DEFAULT}"
        )
    if not (0 < top_p <= 1.0):
        raise ValueError("top_p는 0 초과 1 이하여야 합니다.")


@dataclass
class ExaoneGenerateOptions:
    """
    (en) Generation options following Hugging Face guidelines (temperature=1.0, top_p=0.95, do_sample=True).
    enable_thinking: when True, use the single-agent reasoning (think) step.
    tools: list of tool schemas; when set, tool calling is available after reasoning.
    Never use greedy decoding (temperature=0 or do_sample=False).

    (kr) 생성 옵션으로 Hugging Face 가이드라인(temperature=1.0, top_p=0.95, do_sample=True)을 따른다.
    enable_thinking: True이면 싱글 에이전트의 reasoning(think) 단계를 사용한다.
    tools: 도구 스키마 리스트이며 있으면 reasoning 이후 tool calling이 가능하다.
    greedy(temperature=0 / do_sample=False)는 절대 사용하지 않는다.
    """
    max_new_tokens: int = field(default_factory=get_max_new_tokens_default)
    temperature: float = TEMPERATURE_DEFAULT
    top_p: float = TOP_P_DEFAULT
    do_sample: bool = True
    # (en) Single-agent reasoning (think) step
    # (kr) 싱글 에이전트 reasoning(think) 단계
    enable_thinking: bool = True
    tools: list[dict[str, Any]] | None = None
    response_format: dict[str, Any] | None = None
    # (en) OpenAI-style frequency_penalty; None = not sent. Helps break repetition/whitespace
    # runaway that otherwise truncates structured output at max_tokens.
    # (kr) OpenAI 식 frequency_penalty; None 이면 미전송. 구조화 출력을 max_tokens 에서 자르는
    # 반복·공백 폭주를 억제한다.
    frequency_penalty: float | None = None

    def __post_init__(self) -> None:
        _validate_sampling(self.temperature, self.top_p, self.do_sample)
        if self.max_new_tokens > CONTEXT_LENGTH_RECOMMENDED_TOKENS:
            logger.warning(
                "max_new_tokens (%d) exceeds recommended context limit (%d). "
                "Performance may degrade beyond 128k tokens.",
                self.max_new_tokens, CONTEXT_LENGTH_RECOMMENDED_TOKENS,
            )


# (en) ----- Client interface -----
# (kr) ----- 클라이언트 인터페이스 -----


class ExaoneClient(ABC):
    """
    (en) Common interface for calling Exaone models.

    (kr) Exaone 모델 호출 공통 인터페이스이다.
    """

    DEFAULT_MODEL = "LGAI-EXAONE/K-EXAONE-236B-A23B"

    @abstractmethod
    def chat(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> ExaoneResponse:
        """
        (en) Return a chat completion response for the given message list.

        (kr) 메시지 리스트로 채팅 완료 응답을 반환한다.
        """
        ...

    def chat_stream(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> Iterator[Any]:
        """
        (en) Stream normalized LlmStreamChunk values.
        Default: one-shot chat() then emit text/reasoning/tool_call/done chunks (provider-agnostic).

        (kr) 정규화된 LlmStreamChunk 값을 스트리밍한다.
        기본 구현은 일회성 chat() 후 text/reasoning/tool_call/done 청크를 보낸다(프로바이더 비의존).
        """
        from exaone.llm.streaming import LlmStreamChunk

        resp = self.chat(messages, options=options)
        if resp.reasoning_content:
            yield LlmStreamChunk(kind="reasoning", text=resp.reasoning_content)
        if resp.content:
            yield LlmStreamChunk(kind="text", text=resp.content)
        if resp.tool_calls:
            yield LlmStreamChunk(kind="tool_call", tool_calls=list(resp.tool_calls))
        yield LlmStreamChunk(
            kind="done",
            finish_reason=resp.finish_reason,
            usage=dict(resp.usage or {}),
        )


# (en) ----- Default API client (OpenAPI-compatible endpoint) -----
# (kr) ----- API 호출 기본 구현(OpenAPI 호환 엔드포인트) -----


# (en) Default request timeouts (seconds). From root/.env CORE_LLM_* via exaone.config
# (kr) 기본 요청 타임아웃(초). root/.env의 CORE_LLM_*(exaone.config)
DEFAULT_CONNECT_TIMEOUT = get_llm_connect_timeout_s()
DEFAULT_READ_TIMEOUT = get_llm_read_timeout_s()


class ExaoneAPIClient(ExaoneClient):
    """
    (en) HTTP API client using requests.
    base_url is an OpenAI-compatible base URL (e.g. https://api.friendli.ai/serverless/v1); /chat/completions is appended automatically.
    4xx response bodies may contain prompts, PII, or credentials; they are sanitized with ``exaone.observability.sanitize_for_log`` before logging or exceptions.

    (kr) requests 기반 HTTP API 클라이언트이다.
    base_url은 OpenAI 호환 base URL(예: https://api.friendli.ai/serverless/v1)이며 /chat/completions 경로는 자동으로 추가된다.
    4xx 응답 본문에는 프롬프트·PII·인증 값이 섞일 수 있어 ``exaone.observability.sanitize_for_log``로 정제한 뒤 로그·예외에만 넣는다.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ):
        url = base_url.rstrip("/")
        # (en) /chat/completions is appended on each request
        # (kr) /chat/completions 경로는 요청 시 자동으로 붙인다
        if url.endswith("/chat/completions"):
            url = url[: -len("/chat/completions")]
        self.base_url = url
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key
        # (en) timeout: int sets both connect and read; tuple is (connect, read) seconds
        # (kr) timeout: int이면 connect·read 모두 그 값, tuple이면 (connect, read) 초
        if timeout is None:
            self._connect_timeout = DEFAULT_CONNECT_TIMEOUT
            self._read_timeout = DEFAULT_READ_TIMEOUT
        elif isinstance(timeout, (list, tuple)):
            self._connect_timeout = int(timeout[0]) if len(timeout) > 0 else DEFAULT_CONNECT_TIMEOUT
            self._read_timeout = int(timeout[1]) if len(timeout) > 1 else DEFAULT_READ_TIMEOUT
        else:
            t = int(timeout)
            self._connect_timeout = t
            self._read_timeout = t

    @staticmethod
    def _sanitize_error_body(text: str) -> str:
        from exaone.observability.log_sanitize import sanitize_for_log

        return sanitize_for_log(text, max_len=_LOG_ERROR_BODY_MAX_LEN)

    def _log_and_raise_client_error(self, resp: Any) -> None:
        """
        (en) On 4xx, sanitize the response body (may contain prompts, PII, or keys) before logging or raising.
        Does not use raise_for_status() because the raw body can end up in the exception string.

        (kr) 4xx 응답 본문은 프롬프트·PII·키가 섞일 수 있어 sanitize 후 로그·예외만 남긴다.
        raise_for_status()는 raw body가 예외 str에 들어갈 수 있어 사용하지 않는다.
        """
        safe_body = self._sanitize_error_body(resp.text or "")
        detail = safe_body or "(empty body)"
        logger.error(
            "API %s — request rejected (sanitized excerpt): %s — %s",
            resp.status_code,
            detail,
            self.base_url,
        )
        raise RuntimeError(f"API {resp.status_code} — request rejected: {detail}")

    @staticmethod
    def _log_client_error_warning(resp: Any, *, context: str, base_url: str) -> None:
        safe_body = ExaoneAPIClient._sanitize_error_body(resp.text or "")
        detail = safe_body or "(empty body)"
        logger.warning(
            "API %s — %s (sanitized excerpt): %s — %s",
            resp.status_code,
            context,
            detail,
            base_url,
        )

    @staticmethod
    def _parse_response_with_output_pipeline(text: str) -> dict[str, Any]:
        """
        (en) Parse the response body via exaone/output post-processing (JsonExtractor, then AutoRepair on failure).
        Uses the first valid JSON when extra data or multiple JSON objects are appended.
        If content is empty and more JSON follows, tries that segment to fill content.

        (kr) 응답 본문을 exaone/output 후처리(JsonExtractor → 실패 시 AutoRepair)로 파싱한다.
        Extra data·여러 JSON이 붙은 경우에도 첫 번째 유효 JSON을 사용한다.
        content가 비어 있고 뒤에 또 JSON이 있으면 그쪽을 시도해 채운다.
        """
        from exaone.output import JsonExtractor, AutoRepair

        raw = (text or "").strip()
        if not raw:
            raise ValueError("Empty response body")

        extractor = JsonExtractor()
        repair = AutoRepair()

        import json

        # (en) The HTTP transport envelope is always well-formed JSON from the server — decode
        # it directly. raw_decode reads the first JSON value and ignores trailing extra data.
        # Only fall back to the prose JSON pipeline for genuinely broken bodies, so a fenced
        # JSON/code block inside the model's content is never mistaken for the envelope.
        # (kr) HTTP 전송 봉투는 서버가 항상 정상 JSON 으로 준다 — 곧바로 디코드한다. raw_decode 는
        # 첫 JSON 값만 읽고 뒤 extra data 는 무시한다. 진짜 깨진 본문만 산문용 JSON 파이프라인으로
        # 폴백하여, 답변 content 안의 코드펜스 JSON 을 봉투로 오인하지 않는다.
        try:
            data, _ = json.JSONDecoder().raw_decode(raw)
            if not isinstance(data, dict):
                raise ValueError("top-level JSON is not an object")
        except (json.JSONDecodeError, ValueError):
            result = extractor.process(raw)
            if not result.success:
                result = repair.process(raw)
            if not result.success or result.data is None:
                data, _ = json.JSONDecoder().raw_decode(raw)
                return data
            data = result.data
        # (en) If chat-completion shape but content empty, try trailing JSON
        # (kr) chat completion 형태인데 content가 비어 있으면 뒤쪽 JSON을 시도한다
        choices = data.get("choices") or []
        content = (choices[0].get("message") or {}).get("content") if choices else None
        if isinstance(content, str) and content.strip():
            return data

        # (en) No content in first JSON — if body has "}\s*{", try second JSON
        # (kr) 첫 JSON에 content 없음. 본문에 "}\s*{"가 있으면 두 번째 JSON을 확인한다
        import re
        rest_match = re.search(r"\}\s*\{", raw)
        if rest_match:
            # (en) From '{' through end of body
            # (kr) 본문에서 '{'부터 끝까지
            rest = raw[rest_match.end() - 1 :].strip()
            result2 = extractor.process(rest)
            if result2.success and result2.data:
                d2 = result2.data
                if d2.get("error"):
                    # (en) HTTP 200 but body includes inference error (e.g. 6004)
                    # (kr) API가 200이지만 본문에 inference 에러(6004 등)가 붙어 있는 경우
                    custom = d2.get("custom_status") or {}
                    msg = d2.get("error") or "Unknown error"
                    if custom.get("Description"):
                        msg = f"{msg}: {custom['Description']}"
                    if custom.get("Code"):
                        msg = f"[{custom['Code']}] {msg}"
                    raise RuntimeError(msg)
                c2 = (d2.get("choices") or [{}])[0].get("message") or {}
                if (c2.get("content") or "").strip():
                    return d2
        return data

    def _prepare_chat_request(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None,
    ) -> tuple[list[ExaoneMessage], ExaoneGenerateOptions]:
        """
        (en) Enforce input + reserved_new_tokens <= CONTEXT_LENGTH_MAX_TOKENS (hard cap).

        (kr) input + reserved_new_tokens <= CONTEXT_LENGTH_MAX_TOKENS(하드 캡)을 만족하도록 준비한다.
        """
        from exaone.context_management.budget import prepare_messages_for_llm_chat

        opts = options or ExaoneGenerateOptions()
        capped_msgs, capped_reserved = prepare_messages_for_llm_chat(
            messages,
            reserved_new_tokens=opts.max_new_tokens,
            max_context_tokens=CONTEXT_LENGTH_MAX_TOKENS,
        )
        if capped_reserved == opts.max_new_tokens and capped_msgs is messages:
            return messages, opts
        capped_opts = ExaoneGenerateOptions(
            max_new_tokens=capped_reserved,
            temperature=opts.temperature,
            top_p=opts.top_p,
            do_sample=opts.do_sample,
            enable_thinking=opts.enable_thinking,
            tools=opts.tools,
            response_format=getattr(opts, "response_format", None),
        )
        return capped_msgs, capped_opts

    @staticmethod
    def _response_from_completion_data(data: dict[str, Any], *, latency_ms: float) -> ExaoneResponse:
        """
        (en) Parse OpenAI-compatible completion JSON (content and reasoning remain separate fields).

        (kr) OpenAI 호환 completion JSON을 파싱하며 content와 reasoning은 별도 필드로 유지한다.
        """
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        usage = data.get("usage") or {}
        content = msg.get("content") or ""
        if not isinstance(content, str):
            content = (
                "".join(str(c) for c in content)
                if isinstance(content, (list, tuple))
                else str(content)
            )
        reasoning = (
            msg.get("reasoning_content")
            or msg.get("thinking")
            or msg.get("reasoning")
            or choice.get("reasoning_content")
        )
        reasoning_content = reasoning.strip() if isinstance(reasoning, str) and reasoning.strip() else None
        return ExaoneResponse(
            content=content,
            raw=data,
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            tool_calls=msg.get("tool_calls"),
            latency_ms=latency_ms,
            reasoning_content=reasoning_content,
        )

    def _execute_chat_http(
        self,
        messages: list[ExaoneMessage],
        opts: ExaoneGenerateOptions,
    ) -> ExaoneResponse:
        """
        (en) Single HTTP round-trip with transport-level retries on 5xx and connection errors.

        (kr) 5xx·연결 오류 시 전송 계층 재시도를 포함한 단일 HTTP 왕복을 수행한다.
        """
        import os
        import random
        import time

        import requests

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": opts.max_new_tokens,
            "temperature": max(opts.temperature, TEMPERATURE_MIN),
            "top_p": opts.top_p,
            "chat_template_kwargs": {"enable_thinking": opts.enable_thinking},
        }
        if opts.tools:
            payload["tools"] = opts.tools
        if opts.response_format:
            payload["response_format"] = opts.response_format
        if opts.frequency_penalty is not None:
            payload["frequency_penalty"] = opts.frequency_penalty

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        friendli_team = os.environ.get("FRIENDLI_TEAM_ID")
        if friendli_team:
            headers["X-Friendli-Team"] = friendli_team
        verify_ssl = not get_disable_ssl_verify()

        max_retries = 3
        http_resp = None
        latency_ms = 0.0
        for attempt in range(max_retries + 1):
            t0 = time.monotonic()
            try:
                http_resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=(self._connect_timeout, self._read_timeout),
                    verify=verify_ssl,
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                latency_ms = (time.monotonic() - t0) * 1000
                if attempt < max_retries:
                    backoff = (2**attempt) + random.uniform(0, 0.5 * (2**attempt))
                    logger.warning(
                        "API connection error — retry %d/%d (backoff %.1fs): %s",
                        attempt + 1,
                        max_retries,
                        backoff,
                        e,
                    )
                    time.sleep(backoff)
                    continue
                raise
            latency_ms = (time.monotonic() - t0) * 1000
            if http_resp.status_code >= 500 and attempt < max_retries:
                backoff = (2**attempt) + random.uniform(0, 0.5 * (2**attempt))
                logger.warning(
                    "API %s — retry %d/%d (backoff %.1fs): %s",
                    http_resp.status_code,
                    attempt + 1,
                    max_retries,
                    backoff,
                    self.base_url,
                )
                time.sleep(backoff)
                continue
            break
        if http_resp is not None and http_resp.status_code >= 500:
            logger.error(
                "API %s — all %d retries exhausted: %s",
                http_resp.status_code,
                max_retries,
                self.base_url,
            )
        if http_resp is None:
            raise RuntimeError("No response after retries")
        if 400 <= http_resp.status_code < 500:
            self._log_and_raise_client_error(http_resp)
        http_resp.raise_for_status()
        data = self._parse_response_with_output_pipeline(http_resp.text)
        return self._response_from_completion_data(data, latency_ms=latency_ms)

    def chat(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> ExaoneResponse:
        from exaone.context_management.messages import estimate_tokens_from_messages
        from exaone.llm.response_quality import (
            EMPTY_CONTENT_NUDGE,
            log_llm_response_quality,
            needs_content_recovery,
        )

        messages, opts = self._prepare_chat_request(messages, options)
        estimated_input_tokens = estimate_tokens_from_messages(messages)
        estimated_total = estimated_input_tokens + opts.max_new_tokens
        if estimated_total > CONTEXT_LENGTH_RECOMMENDED_TOKENS:
            logger.warning(
                "Estimated tokens (%d input + %d output = %d) exceed "
                "recommended limit (%d). Consider reducing context.",
                estimated_input_tokens,
                opts.max_new_tokens,
                estimated_total,
                CONTEXT_LENGTH_RECOMMENDED_TOKENS,
            )

        resp = self._execute_chat_http(messages, opts)
        log_llm_response_quality(resp, phase="initial", enable_thinking=opts.enable_thinking)
        if not needs_content_recovery(resp):
            return resp

        retry_opts = ExaoneGenerateOptions(
            max_new_tokens=opts.max_new_tokens,
            temperature=opts.temperature,
            top_p=opts.top_p,
            do_sample=opts.do_sample,
            enable_thinking=False,
            tools=opts.tools,
            response_format=getattr(opts, "response_format", None),
        )
        retry = self._execute_chat_http(messages, retry_opts)
        log_llm_response_quality(
            retry, phase="thinking_off_retry", enable_thinking=False
        )
        if not needs_content_recovery(retry):
            log_llm_response_quality(
                retry, phase="thinking_off_retry", enable_thinking=False, recovered=True
            )
            return retry

        nudge_messages = list(messages) + [
            ExaoneMessage(role="user", content=EMPTY_CONTENT_NUDGE),
        ]
        nudge = self._execute_chat_http(nudge_messages, retry_opts)
        log_llm_response_quality(nudge, phase="nudge_retry", enable_thinking=False)
        if not needs_content_recovery(nudge):
            log_llm_response_quality(
                nudge, phase="nudge_retry", enable_thinking=False, recovered=True
            )
        return nudge

    def chat_stream(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> Iterator[Any]:
        """
        (en) OpenAI-compatible SSE stream mapped to LlmStreamChunk; falls back to chat() if streaming is unsupported.

        (kr) OpenAI 호환 SSE 스트림을 LlmStreamChunk로 변환하며 스트리밍 미지원 시 chat()으로 폴백한다.
        """
        import os
        import random
        import time

        import requests

        from exaone.llm.streaming import LlmStreamChunk, iter_openai_compatible_sse

        messages, opts = self._prepare_chat_request(messages, options)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": opts.max_new_tokens,
            "temperature": max(opts.temperature, TEMPERATURE_MIN),
            "top_p": opts.top_p,
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": opts.enable_thinking},
        }
        if opts.tools:
            payload["tools"] = opts.tools
        if opts.response_format:
            payload["response_format"] = opts.response_format
        if opts.frequency_penalty is not None:
            payload["frequency_penalty"] = opts.frequency_penalty

        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        friendli_team = os.environ.get("FRIENDLI_TEAM_ID")
        if friendli_team:
            headers["X-Friendli-Team"] = friendli_team
        verify_ssl = not get_disable_ssl_verify()

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=(self._connect_timeout, self._read_timeout),
                    verify=verify_ssl,
                    stream=True,
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    time.sleep((2**attempt) + random.uniform(0, 0.5 * (2**attempt)))
                    continue
                yield from ExaoneClient.chat_stream(self, messages, options=opts)
                return

            if resp.status_code >= 500 and attempt < max_retries:
                resp.close()
                time.sleep((2**attempt) + random.uniform(0, 0.5 * (2**attempt)))
                continue

            if 400 <= resp.status_code < 500:
                self._log_client_error_warning(
                    resp,
                    context="streaming rejected, falling back to chat()",
                    base_url=self.base_url,
                )
                resp.close()
                yield from ExaoneClient.chat_stream(self, messages, options=opts)
                return

            try:
                resp.raise_for_status()
            except Exception:
                resp.close()
                yield from ExaoneClient.chat_stream(self, messages, options=opts)
                return

            saw_done = False
            try:
                def _lines():
                    # (en) decode_unicode=True uses ISO-8859-1 and mojibakes UTF-8 Korean in SSE JSON.
                    # (kr) decode_unicode=True 는 ISO-8859-1 로 디코딩해 SSE JSON 의 UTF-8 한글이 깨진다.
                    for raw in resp.iter_lines(decode_unicode=False):
                        if raw:
                            yield raw.decode("utf-8", errors="replace")

                for chunk in iter_openai_compatible_sse(_lines()):
                    yield chunk
                    if chunk.kind == "done":
                        saw_done = True
                if not saw_done:
                    yield LlmStreamChunk(kind="done")
            finally:
                resp.close()
            return

        yield from ExaoneClient.chat_stream(self, messages, options=opts)
