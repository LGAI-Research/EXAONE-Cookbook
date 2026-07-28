"""
(en) LlamaIndex OpenAI LLM with support for non-standard model ids (Friendli / HuggingFace style).

``llama_index.llms.openai.OpenAI`` resolves model names only against the public OpenAI
catalog when computing ``metadata``. Model ids on OpenAI-compatible endpoints (e.g. EXAONE)
may be absent from that list, causing ``ValueError`` before ``complete()`` / ``chat()``.

This subclass adjusts ``LLMMetadata`` and tiktoken fallback only; API requests still send
``self.model`` in the ``model`` field.

On TLS verification failure (e.g. corporate network), applies ``verify=False`` to ``httpx``
clients when root ``.env`` sets ``DISABLE_SSL_VERIFY=1`` (aligned with ``exaone.llm``).

(kr) LlamaIndex OpenAI LLM이다(Friendli / HuggingFace 형 비표준 model id 지원).

``llama_index.llms.openai.OpenAI``는 ``metadata`` 계산 시 모델명을 OpenAI 공개
목록에서만 조회한다. EXAONE 등 OpenAI 호환 엔드포인트의 model id는 목록에
없어 ``complete()`` / ``chat()`` 호출 전에 ``ValueError``가 날 수 있다.

이 서브클래스는 ``LLMMetadata``와 tiktoken 폴백만 보정하고, 실제 API 요청의
``model`` 필드는 그대로 ``self.model``을 사용한다.

회사망 등 TLS 검증 실패 시 루트 ``.env``의 ``DISABLE_SSL_VERIFY=1``과 동일하게
``httpx`` 클라이언트에 ``verify=False``를 적용한다(``exaone.llm``과 맞춤).
"""
from __future__ import annotations

from typing import Any, Optional

import httpx
import tiktoken
from llama_index.core.base.llms.types import LLMMetadata, MessageRole
from llama_index.core.bridge.pydantic import Field
from llama_index.llms.openai import OpenAI as OpenAILLM

from exaone.config import get_context_length_max_tokens, get_disable_ssl_verify


class OpenAICompatLLM(OpenAILLM):
    """
    (en) LlamaIndex LLM for OpenAI-compatible base_url and non-standard ``model`` ids.

    Default ``context_window`` comes from ``exaone.config.get_context_length_max_tokens()``
    (``.env`` key ``CORE_CONTEXT_LENGTH_MAX_TOKENS``, default 256000).

    (kr) OpenAI 호환 base_url과 비표준 ``model`` id용 LlamaIndex LLM이다.

    ``context_window`` 기본값은 ``exaone.config.get_context_length_max_tokens()``이다
    (``.env``의 ``CORE_CONTEXT_LENGTH_MAX_TOKENS``, 기본 256000).
    """

    context_window: int = Field(
        default_factory=get_context_length_max_tokens,
        description="LlamaIndex 메타데이터용 컨텍스트 상한(토큰). API payload 의 model 과 무관.",
    )

    def __init__(self, **kwargs: Any) -> None:
        http_client = kwargs.get("http_client")
        async_http_client = kwargs.get("async_http_client")
        if get_disable_ssl_verify():
            if http_client is None:
                kwargs["http_client"] = httpx.Client(verify=False)
            if async_http_client is None:
                kwargs["async_http_client"] = httpx.AsyncClient(verify=False)
        super().__init__(**kwargs)

    # (en) type: ignore[override] — LlamaIndex LLMMetadata property signature differs by version.
    # (kr) type: ignore[override] — LlamaIndex LLMMetadata 프로퍼티 시그니처가 버전마다 다르다.
    # type: ignore[override]
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.max_tokens or -1,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name=self.model,
            system_role=MessageRole.SYSTEM,
        )

    # (en) type: ignore[override] — optional tiktoken encoding; base class typing varies.
    # (kr) type: ignore[override] — tiktoken 인코딩 optional; 베이스 클래스 typing 이 다양하다.
    # type: ignore[override]
    @property
    def _tokenizer(self) -> Optional[tiktoken.Encoding]:
        try:
            return tiktoken.encoding_for_model(self._get_model_name())
        except (KeyError, ValueError):
            return tiktoken.get_encoding("cl100k_base")
