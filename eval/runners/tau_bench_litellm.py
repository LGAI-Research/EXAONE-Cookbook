"""
(en) Configure LiteLLM (τ-bench user simulator) to call the same Friendli / EXAONE
OpenAI-compatible endpoint as ``eval.runners.naive_runner``.

(kr) LiteLLM(τ-bench user simulator)이 ``eval.runners.naive_runner``와 동일한
Friendli / EXAONE OpenAI 호환 엔드포인트를 쓰도록 설정한다.
"""
from __future__ import annotations

import os
import sys
from typing import Any


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def exaone_api_key() -> str:
    """
    (en) Resolve API key for EXAONE / Friendli (same precedence as naive runner).

    (kr) EXAONE / Friendli API 키를 해석한다(naive runner와 동일 우선순위).
    """
    return (
        os.environ.get("EXAONE_API_KEY")
        or os.environ.get("FRIENDLI_API_KEY")
        or ""
    ).strip()


def exaone_openai_base_url() -> str:
    """
    (en) Strip ``/chat/completions`` from ``EXAONE_BASE_URL`` for LiteLLM ``api_base``.

    (kr) LiteLLM ``api_base``용으로 ``EXAONE_BASE_URL``에서 ``/chat/completions``를 제거한다.
    """
    base = (os.environ.get("EXAONE_BASE_URL") or "").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if not base:
        raise ValueError("EXAONE_BASE_URL is required for τ-bench user simulation")
    return base


def exaone_model_name() -> str:
    """
    (en) Model id for both agent and user simulator (override with ``TAU_BENCH_USER_MODEL``).

    (kr) agent·user simulator 공통 모델 id(``TAU_BENCH_USER_MODEL``로 user만 override 가능).
    """
    return (
        os.environ.get("TAU_BENCH_USER_MODEL")
        or os.environ.get("EXAONE_MODEL")
        or ""
    ).strip() or "gpt-4o"


def sync_openai_env_from_exaone() -> None:
    """
    (en) Map ``EXAONE_*`` credentials to ``OPENAI_*`` names LiteLLM reads when
    τ-bench calls ``completion(model=..., custom_llm_provider='openai')`` without
    explicit ``api_key`` / ``api_base``.

    (kr) τ-bench가 ``api_key``/``api_base`` 없이 ``completion(..., custom_llm_provider='openai')``
    를 호출할 때 LiteLLM이 읽는 ``OPENAI_*`` 환경변수에 ``EXAONE_*`` 자격증명을 맞춘다.
    """
    key = exaone_api_key()
    if key:
        os.environ["OPENAI_API_KEY"] = key
    try:
        base = exaone_openai_base_url()
    except ValueError:
        base = ""
    if base:
        os.environ["OPENAI_API_BASE"] = base


def litellm_completion_kwargs() -> dict[str, Any]:
    """
    (en) Keyword args for ``litellm.completion`` targeting Friendli serverless.

    (kr) Friendli serverless를 향한 ``litellm.completion`` 키워드 인자.
    """
    api_key = exaone_api_key()
    if not api_key:
        raise ValueError("EXAONE_API_KEY (or FRIENDLI_API_KEY) is required for τ-bench")
    kwargs: dict[str, Any] = {
        "model": exaone_model_name(),
        "custom_llm_provider": "openai",
        "api_base": exaone_openai_base_url(),
        "api_key": api_key,
    }
    team = os.environ.get("FRIENDLI_TEAM_ID", "").strip()
    if team:
        kwargs["extra_headers"] = {"X-Friendli-Team": team}
    return kwargs


def apply_litellm_exaone_defaults() -> None:
    """
    (en) Set module-level LiteLLM defaults (SSL, optional debug). Idempotent.

    (kr) LiteLLM 모듈 기본값(SSL, debug)을 설정한다. 멱등.
    """
    import litellm

    if _truthy("DISABLE_SSL_VERIFY"):
        litellm.ssl_verify = False
    if _truthy("TAU_BENCH_LITELLM_DEBUG"):
        litellm.set_verbose = True


def _rebind_tau_bench_user_completion() -> None:
    """
    (en) ``tau_bench.envs.user`` binds ``from litellm import completion`` at import
    time; re-point it after we patch ``litellm.completion``.

    (kr) ``tau_bench.envs.user``는 import 시 ``from litellm import completion``으로
    고정되므로 ``litellm.completion`` 패치 후 다시 연결한다.
    """
    import litellm

    mod = sys.modules.get("tau_bench.envs.user")
    if mod is not None and hasattr(mod, "completion"):
        mod.completion = litellm.completion


def patch_litellm_completion_exaone() -> None:
    """
    (en) Route τ-bench user simulator ``litellm.completion`` calls through EXAONE/Friendli.
    Safe to call multiple times (re-syncs env + rebinds ``tau_bench.envs.user``).

    (kr) τ-bench user simulator의 ``litellm.completion``을 EXAONE/Friendli로 보낸다.
    여러 번 호출해도 안전(env 재동기화·``tau_bench.envs.user`` 재바인딩).
    """
    import litellm

    sync_openai_env_from_exaone()
    apply_litellm_exaone_defaults()

    if not getattr(litellm, "_cookbook_exaone_patched", False):
        original = litellm.completion
        defaults = litellm_completion_kwargs()

        def _completion(*args: Any, **kwargs: Any) -> Any:
            merged = {**defaults, **kwargs}
            return original(*args, **merged)

        litellm.completion = _completion
        litellm._cookbook_exaone_patched = True

    _rebind_tau_bench_user_completion()


__all__ = [
    "apply_litellm_exaone_defaults",
    "exaone_api_key",
    "exaone_model_name",
    "exaone_openai_base_url",
    "litellm_completion_kwargs",
    "patch_litellm_completion_exaone",
    "sync_openai_env_from_exaone",
]
