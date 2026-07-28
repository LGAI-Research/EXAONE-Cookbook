"""
(en) Build CrewAI LLM instances backed by EXAONE (OpenAI-compatible API).

(kr) EXAONE(OpenAI 호환 API)을 백본으로 하는 CrewAI LLM 빌더이다.
"""
from __future__ import annotations

from typing import Any

from crewai import LLM

from common.exaone_env import get_disable_ssl_verify, load_exaone_env, openai_compat_kwargs


def configure_litellm_for_exaone() -> None:
    """
    (en) Align LiteLLM TLS with implementation `.env` (`DISABLE_SSL_VERIFY`, corporate CA).

    (kr) implementation `.env`(`DISABLE_SSL_VERIFY`, 회사 CA)에 맞춰 LiteLLM TLS를 설정한다.
    """
    load_exaone_env()
    if get_disable_ssl_verify():
        import litellm

        litellm.ssl_verify = False


def build_exaone_llm(**overrides: Any) -> LLM:
    """
    (en) CrewAI LLM for EXAONE: `openai/<model>` + thinking off + optional overrides.

    (kr) EXAONE용 CrewAI LLM이다(`openai/<model>` + thinking off + 선택적 override).
    """
    configure_litellm_for_exaone()
    kw = openai_compat_kwargs()
    params: dict[str, Any] = {
        "model": f"openai/{kw['model']}",
        "base_url": kw["base_url"],
        "api_key": kw["api_key"],
        "temperature": 0.3,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    }
    params.update(overrides)
    return LLM(**params)


__all__ = ["build_exaone_llm", "configure_litellm_for_exaone"]
