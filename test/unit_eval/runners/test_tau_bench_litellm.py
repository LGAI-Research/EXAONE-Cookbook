"""
(en) Unit tests for τ-bench LiteLLM / EXAONE env bridging.

(kr) τ-bench LiteLLM / EXAONE 환경변수 브리지 단위 테스트.
"""
from __future__ import annotations

import pytest

from eval.runners.tau_bench_litellm import patch_litellm_completion_exaone, sync_openai_env_from_exaone


def test_sync_openai_env_from_exaone_maps_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.setenv("EXAONE_API_KEY", "sk-test-exaone")
    monkeypatch.setenv("EXAONE_BASE_URL", "https://api.example.com/v1/chat/completions")

    sync_openai_env_from_exaone()

    import os

    assert os.environ["OPENAI_API_KEY"] == "sk-test-exaone"
    assert os.environ["OPENAI_API_BASE"] == "https://api.example.com/v1"


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("tau_bench"),
    reason="tau-bench optional package not installed",
)
def test_patch_rebinds_tau_bench_user_completion(monkeypatch):
    monkeypatch.setenv("EXAONE_API_KEY", "sk-test-exaone")
    monkeypatch.setenv("EXAONE_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("EXAONE_MODEL", "test-model")

    import litellm
    import tau_bench.envs.user as user_mod

    before = user_mod.completion
    patch_litellm_completion_exaone()
    assert user_mod.completion is litellm.completion
    assert user_mod.completion is not before
