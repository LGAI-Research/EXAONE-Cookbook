"""Implementation glue subprocess smoke — stdlib-only scripts, no live API."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_check_env(
    repo_root: Path,
    repo_name: str,
    script_relative: str,
    env: dict[str, str],
    *extra_args: str,
) -> subprocess.CompletedProcess[str]:
    # (en) Run a glue script with isolated EXAONE_IMPL_DIR.
    # (kr) 격리된 EXAONE_IMPL_DIR 로 glue 스크립트를 실행한다.
    script = repo_root / "implementations" / repo_name / script_relative
    return subprocess.run(
        [sys.executable, str(script), *extra_args],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_hermes_check_env_reads_impl_env(
    repo_root: Path,
    glue_subprocess_env: dict[str, str],
) -> None:
    # (en) Hermes hermes_glue check prints impl path and api_key_set without calling Hermes CLI.
    # (kr) Hermes hermes_glue check 는 Hermes CLI 없이 impl 경로와 api_key_set 을 출력한다.
    proc = _run_check_env(
        repo_root,
        "hermes-agent",
        "scripts/hermes_glue.py",
        glue_subprocess_env,
        "check",
    )
    assert proc.returncode in {0, 1}
    payload = json.loads(proc.stdout)
    assert payload["api_key_set"] is True
    assert payload["model"] == "test-model"
    assert "hermes-agent" in Path(payload["impl_env"]).name


def test_nanoclaw_check_env_reads_impl_env(
    repo_root: Path,
    impl_env_dir,
) -> None:
    # (en) NanoClaw check_env loads EXAONE from impl .env and emits JSON (docker may be absent).
    # (kr) NanoClaw check_env 는 impl .env 의 EXAONE 를 읽고 JSON 을 낸다(docker 없을 수 있음).
    impl_dir = impl_env_dir("nanoclaw")
    env = {
        key: value
        for key, value in __import__("os").environ.items()
        if not key.startswith("EXAONE_")
    }
    env["PYTHONPATH"] = str(repo_root / "implementations")
    env["EXAONE_IMPL_DIR"] = str(impl_dir)

    proc = _run_check_env(
        repo_root,
        "nanoclaw",
        "scripts/check_env.py",
        env,
    )
    assert proc.returncode in {0, 1}
    payload = json.loads(proc.stdout)
    assert payload["api_key_set"] is True
    assert payload["model"] == "test-model"
    assert str(payload["impl_env"]) == str(impl_dir)
