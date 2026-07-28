"""
(en) Fixtures for implementations/ glue tests — isolated per-repo .env, not cookbook root .env.

(kr) implementations/ glue 테스트용 fixture — cookbook 루트 .env 와 분리된 repo별 .env.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATIONS_DIR = REPO_ROOT / "implementations"
EXAONE_ENV_KEYS = ("EXAONE_API_KEY", "EXAONE_BASE_URL", "EXAONE_MODEL")

PROOF_GALLERY_REPOS = (
    "smolagents",
    "browser-use",
    "crewai",
    "hermes-agent",
    "nanoclaw",
)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """
    (en) Cookbook repository root.

    (kr) Cookbook 레포지토리 루트이다.
    """
    return REPO_ROOT


@pytest.fixture(scope="session")
def implementations_dir() -> Path:
    """
    (en) `implementations/` directory (contains `common/` glue).

    (kr) `common/` glue 가 있는 `implementations/` 디렉터리이다.
    """
    return IMPLEMENTATIONS_DIR


@pytest.fixture
def exaone_env_module():
    """
    (en) Import `common.exaone_env` with implementations/ on sys.path.

    (kr) implementations/ 가 sys.path 에 있도록 `common.exaone_env` 를 import 한다.
    """
    impl_root = str(IMPLEMENTATIONS_DIR)
    if impl_root not in sys.path:
        sys.path.insert(0, impl_root)
    import common.exaone_env as env_mod

    yield env_mod
    env_mod._loaded_impl_dirs.clear()
    env_mod._active_impl = None


@pytest.fixture(autouse=True)
def _clear_root_exaone_from_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    (en) Drop cookbook root EXAONE_* so unit_implementations never inherits test/conftest .env.

    (kr) test/conftest 의 루트 .env 가 주입한 EXAONE_* 를 제거해 unit_implementations 가 물려받지 않게 한다.
    """
    for key in EXAONE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def impl_env_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    (en) Factory: temp `implementations/<repo>/.env` + `EXAONE_IMPL_DIR`.

    (kr) 임시 `implementations/<repo>/.env` 와 `EXAONE_IMPL_DIR` 를 만드는 factory 이다.
    """

    def _factory(
        repo_name: str = "smolagents",
        *,
        api_key: str = "test-key",
        base_url: str = "https://example.com/v1",
        model: str = "test-model",
    ) -> Path:
        env_dir = tmp_path / repo_name
        env_dir.mkdir(parents=True, exist_ok=True)
        (env_dir / ".env").write_text(
            f"EXAONE_API_KEY={api_key}\n"
            f"EXAONE_BASE_URL={base_url}\n"
            f"EXAONE_MODEL={model}\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("EXAONE_IMPL_DIR", str(env_dir))
        return env_dir

    return _factory


@pytest.fixture
def glue_subprocess_env(
    impl_env_dir,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, str]]:
    """
    (en) Env dict for running glue scripts: PYTHONPATH + EXAONE_IMPL_DIR, no root EXAONE_*.

    (kr) glue 스크립트 subprocess 용 env — PYTHONPATH + EXAONE_IMPL_DIR, 루트 EXAONE_* 없음.
    """
    impl_dir = impl_env_dir("hermes-agent")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in EXAONE_ENV_KEYS
    }
    env["PYTHONPATH"] = str(IMPLEMENTATIONS_DIR)
    env["EXAONE_IMPL_DIR"] = str(impl_dir)
    yield env
