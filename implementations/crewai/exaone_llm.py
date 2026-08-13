"""
(en) Build CrewAI LLM instances backed by EXAONE (OpenAI-compatible API).

(kr) EXAONE(OpenAI 호환 API)을 백본으로 하는 CrewAI LLM 빌더이다.
"""
from __future__ import annotations

from typing import Any

from crewai import LLM

from common.exaone_env import get_disable_ssl_verify, load_exaone_env, openai_compat_kwargs


def _patch_openai_ssl_clients(llm: LLM) -> None:
    if not get_disable_ssl_verify():
        return
    import httpx
    from openai import AsyncOpenAI, OpenAI

    if not hasattr(llm, "_get_client_params"):
        return
    sync_params = llm._get_client_params()
    sync_params["http_client"] = httpx.Client(verify=False)
    llm._client = OpenAI(**sync_params)
    async_params = llm._get_client_params()
    async_params["http_client"] = httpx.AsyncClient(verify=False)
    llm._async_client = AsyncOpenAI(**async_params)


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
    llm = LLM(**params)
    _patch_openai_ssl_clients(llm)
    return llm


__all__ = ["build_exaone_llm", "configure_litellm_for_exaone"]
