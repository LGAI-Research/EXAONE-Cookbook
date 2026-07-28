"""exaone.integrations.llm_env — env validation."""
from __future__ import annotations

import pytest

from exaone.integrations.exit_codes import EXIT_CONFIG
from exaone.integrations.llm_env import build_llm_from_env
from exaone.llm import ExaoneAPIClient


def test_build_llm_from_env_requires_base_url(monkeypatch):
    monkeypatch.setenv("EXAONE_API_KEY", "test-key")
    monkeypatch.setenv("EXAONE_BASE_URL", "")
    with pytest.raises(SystemExit) as exc:
        build_llm_from_env()
    assert exc.value.code == EXIT_CONFIG


def test_build_llm_from_env_requires_api_key(monkeypatch):
    monkeypatch.setenv("EXAONE_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("EXAONE_API_KEY", "")
    with pytest.raises(SystemExit) as exc:
        build_llm_from_env()
    assert exc.value.code == EXIT_CONFIG


def test_build_llm_from_env_ok(monkeypatch):
    monkeypatch.setenv("EXAONE_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("EXAONE_API_KEY", "secret")
    monkeypatch.setenv("EXAONE_MODEL", "demo-model")
    client = build_llm_from_env()
    assert isinstance(client, ExaoneAPIClient)
    assert client.base_url == "https://example.com/v1"
    assert client.model == "demo-model"
