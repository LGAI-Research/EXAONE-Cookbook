"""Proof Gallery repo layout smoke — pyproject.toml and .env.example per repo."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import PROOF_GALLERY_REPOS


@pytest.mark.parametrize("repo_name", PROOF_GALLERY_REPOS)
def test_repo_has_pyproject_and_env_example(implementations_dir: Path, repo_name: str) -> None:
    # (en) Each gallery repo ships uv project + env template for isolated demos.
    # (kr) 각 gallery repo 는 격리 데모용 uv project 와 env 템플릿을 갖는다.
    repo = implementations_dir / repo_name
    assert (repo / "pyproject.toml").is_file(), f"missing {repo}/pyproject.toml"
    assert (repo / ".env.example").is_file(), f"missing {repo}/.env.example"


def test_uv_run_script_exists_and_executable(implementations_dir: Path) -> None:
    # (en) Shared entrypoint for all implementation demos.
    # (kr) 모든 implementation 데모의 공통 진입점이다.
    uv_run = implementations_dir / "uv_run.sh"
    assert uv_run.is_file()
    assert os.access(uv_run, os.X_OK)
