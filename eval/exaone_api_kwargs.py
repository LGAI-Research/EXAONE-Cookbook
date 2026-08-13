"""
(en) Shared EXAONE / OpenAI-compat request kwargs for eval runners that bypass
``exaone.llm.ExaoneAPIClient`` (τ-bench, Harbor upstream, Claw-Eval, …).

``enable_thinking`` and ``preserve_thinking`` are set explicitly via function
arguments or ``EXAONE_ENABLE_THINKING`` / ``EXAONE_PRESERVE_THINKING``. Both keys
are always included in ``chat_template_kwargs``. The *effect* of
``preserve_thinking`` is defined for K-EXAONE 2.0+; on 1.0 deployments the
server typically ignores the flag (see ``docs/k_exaone_2.md``).

(kr) eval 전용 runner용 EXAONE API kwargs.
``enable_thinking``·``preserve_thinking`` 은 인자 또는 환경 변수로 **명시**하며,
payload에는 항상 둘 다 실립니다. ``preserve_thinking`` 의 **효과**는 K-EXAONE 2.0+
에서만 정의되고, 1.0에서는 보통 무시됩니다.
"""
from __future__ import annotations

import os
from typing import Any

from exaone.llm.exaone_client import TEMPERATURE_MIN, TOP_P_DEFAULT


def _env_truthy(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def eval_enable_thinking() -> bool:
    """(en) Reasoning for agentic eval (default on). (kr) agentic eval reasoning (기본 on)."""
    return _env_truthy("EXAONE_ENABLE_THINKING", default=True)


def eval_preserve_thinking() -> bool:
    """
    (en) Keep reasoning across multi-turn agent loops (default on).

    Sent in every payload; only **effective** on K-EXAONE 2.0+ (1.0 ignores).

    (kr) 멀티턴 agentic reasoning 유지(기본 on). payload에는 항상 실리며,
    **효과**는 K-EXAONE 2.0+ 에서만 적용(1.0은 무시).
    """
    return _env_truthy("EXAONE_PRESERVE_THINKING", default=True)


def eval_agent_temperature() -> float:
    """(en) Tool-agent temperature for benches (default 0.7). (kr) agent temperature (기본 0.7)."""
    raw = (
        (os.environ.get("EXAONE_EVAL_AGENT_TEMPERATURE") or "").strip()
        or (os.environ.get("EXAONE_TEMPERATURE") or "").strip()
        or "0.7"
    )
    try:
        temp = float(raw)
    except ValueError:
        temp = 0.7
    return max(temp, TEMPERATURE_MIN)


def eval_top_p() -> float:
    raw = (os.environ.get("EXAONE_TOP_P") or "").strip() or str(TOP_P_DEFAULT)
    try:
        return float(raw)
    except ValueError:
        return TOP_P_DEFAULT


def build_chat_template_kwargs(
    *,
    enable_thinking: bool | None = None,
    preserve_thinking: bool | None = None,
) -> dict[str, Any]:
    """
    (en) ``chat_template_kwargs`` for EXAONE OpenAI-compat APIs.

    Agentic: ``enable_thinking=True``, ``preserve_thinking=True``.
    Chitchat / single-turn QA: both ``False``.

    ``preserve_thinking`` is always emitted; on K-EXAONE 1.0 it has no effect.

    (kr) EXAONE API용 kwargs. agentic은 둘 다 True, chitchat은 둘 다 False.
    ``preserve_thinking`` 은 항상 payload에 포함(1.0에서는 효과 없음).
    """
    thinking = enable_thinking if enable_thinking is not None else eval_enable_thinking()
    preserve = preserve_thinking if preserve_thinking is not None else eval_preserve_thinking()
    return {
        "enable_thinking": thinking,
        "preserve_thinking": preserve,
    }


def build_extra_body(
    *,
    enable_thinking: bool | None = None,
    preserve_thinking: bool | None = None,
) -> dict[str, Any]:
    """(en) Vendor ``extra_body`` wrapping ``chat_template_kwargs``. (kr) vendor extra_body."""
    return {
        "chat_template_kwargs": build_chat_template_kwargs(
            enable_thinking=enable_thinking,
            preserve_thinking=preserve_thinking,
        )
    }


def litellm_completion_extensions(
    *,
    enable_thinking: bool | None = None,
    preserve_thinking: bool | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    """(en) Extra kwargs for ``litellm.completion``. (kr) LiteLLM completion 추가 kwargs."""
    return {
        "extra_body": build_extra_body(
            enable_thinking=enable_thinking,
            preserve_thinking=preserve_thinking,
        ),
        "temperature": temperature if temperature is not None else eval_agent_temperature(),
        "top_p": eval_top_p(),
    }


def deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """(en) Recursive dict merge for nested ``extra_body``. (kr) nested extra_body 병합."""
    merged = dict(base)
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = deep_merge_dict(merged[key], val)
        else:
            merged[key] = val
    return merged


def merge_litellm_completion_kwargs(
    defaults: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """(en) Merge litellm kwargs; deep-merge ``extra_body``. (kr) litellm kwargs 병합."""
    merged = {**defaults, **overrides}
    if "extra_body" in defaults and "extra_body" in overrides:
        merged["extra_body"] = deep_merge_dict(
            defaults["extra_body"],
            overrides["extra_body"],
        )
    return merged


def ensure_eval_exaone_api_env() -> dict[str, str]:
    """(en) Documented defaults for subprocesses (setdefault only). (kr) subprocess env 기본값."""
    overlay = {
        "EXAONE_ENABLE_THINKING": "1" if eval_enable_thinking() else "0",
        "EXAONE_PRESERVE_THINKING": "1" if eval_preserve_thinking() else "0",
        "EXAONE_EVAL_AGENT_TEMPERATURE": str(eval_agent_temperature()),
    }
    for key, val in overlay.items():
        if not (os.environ.get(key) or "").strip():
            os.environ[key] = val
    return overlay


__all__ = [
    "build_chat_template_kwargs",
    "build_extra_body",
    "deep_merge_dict",
    "ensure_eval_exaone_api_env",
    "eval_agent_temperature",
    "eval_enable_thinking",
    "eval_preserve_thinking",
    "eval_top_p",
    "litellm_completion_extensions",
    "merge_litellm_completion_kwargs",
]
