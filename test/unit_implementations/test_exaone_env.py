"""implementations/common/exaone_env 단위 테스트."""
from __future__ import annotations

import os

import pytest


def test_load_exaone_env_uses_impl_dir(exaone_env_module, impl_env_dir) -> None:
    # (en) EXAONE_IMPL_DIR + impl .env is the source of truth.
    # (kr) EXAONE_IMPL_DIR + impl .env 가 정본이다.
    env_mod = exaone_env_module
    impl = impl_env_dir("smolagents")

    loaded = env_mod.load_exaone_env()
    assert loaded == impl
    kw = env_mod.openai_compat_kwargs()
    assert kw["api_key"] == "test-key"
    assert kw["base_url"] == "https://example.com/v1"
    assert kw["model"] == "test-model"
    assert os.environ.get("EXAONE_API_KEY") == "test-key"


def test_impl_env_overrides_root_pollution(
    exaone_env_module,
    impl_env_dir,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # (en) Pre-set root-like EXAONE_* must not win over implementations/<repo>/.env.
    # (kr) 미리 박힌 루트 EXAONE_* 가 implementations/<repo>/.env 보다 우선하면 안 된다.
    env_mod = exaone_env_module
    impl_env_dir("browser-use", api_key="from-impl-env", model="impl-model")

    monkeypatch.setenv("EXAONE_API_KEY", "from-root-pollution")
    monkeypatch.setenv("EXAONE_MODEL", "root-model")

    kw = env_mod.openai_compat_kwargs()
    assert kw["api_key"] == "from-impl-env"
    assert kw["model"] == "impl-model"


def test_openai_compat_kwargs_missing_key_raises(exaone_env_module, impl_env_dir) -> None:
    # (en) Empty EXAONE_API_KEY in impl .env surfaces a clear error.
    # (kr) impl .env 의 EXAONE_API_KEY 가 비어 있으면 명확한 오류를 낸다.
    env_mod = exaone_env_module
    impl_env_dir("crewai", api_key="")

    with pytest.raises(RuntimeError, match=r"EXAONE_API_KEY is missing.*\.env"):
        env_mod.openai_compat_kwargs()
