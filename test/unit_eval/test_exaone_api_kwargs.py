"""Unit tests for eval.exaone_api_kwargs."""
from __future__ import annotations

from eval.exaone_api_kwargs import (
    build_chat_template_kwargs,
    build_extra_body,
    litellm_completion_extensions,
    merge_litellm_completion_kwargs,
)


def test_build_extra_body_agentic_defaults(monkeypatch):
    monkeypatch.delenv("EXAONE_ENABLE_THINKING", raising=False)
    monkeypatch.delenv("EXAONE_PRESERVE_THINKING", raising=False)
    kwargs = build_extra_body()["chat_template_kwargs"]
    assert kwargs == {"enable_thinking": True, "preserve_thinking": True}


def test_build_extra_body_chitchat_explicit(monkeypatch):
    monkeypatch.setenv("EXAONE_ENABLE_THINKING", "0")
    monkeypatch.setenv("EXAONE_PRESERVE_THINKING", "0")
    kwargs = build_chat_template_kwargs()
    assert kwargs == {"enable_thinking": False, "preserve_thinking": False}


def test_preserve_in_payload_for_v1_when_env_on(monkeypatch):
    """v1 deployments ignore the flag; Cookbook still sends it explicitly."""
    monkeypatch.setenv("EXAONE_PRESERVE_THINKING", "1")
    kwargs = build_chat_template_kwargs(enable_thinking=True, preserve_thinking=True)
    assert kwargs["preserve_thinking"] is True


def test_litellm_extensions_agent_temperature(monkeypatch):
    monkeypatch.setenv("EXAONE_EVAL_AGENT_TEMPERATURE", "0.65")
    ext = litellm_completion_extensions()
    assert ext["temperature"] == 0.65
    assert ext["extra_body"]["chat_template_kwargs"]["preserve_thinking"] is True


def test_merge_litellm_deep_merges_extra_body():
    defaults = {
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": True,
                "preserve_thinking": True,
            }
        },
        "temperature": 0.7,
    }
    overrides = {
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
        "max_tokens": 512,
    }
    merged = merge_litellm_completion_kwargs(defaults, overrides)
    assert merged["max_tokens"] == 512
    ctk = merged["extra_body"]["chat_template_kwargs"]
    assert ctk["enable_thinking"] is False
    assert ctk["preserve_thinking"] is True
