"""implementations/uv_run.sh router smoke (no API, no full uv sync required)."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run_uv_run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # (en) Invoke uv_run.sh from cookbook root.
    # (kr) cookbook 루트에서 uv_run.sh 를 호출한다.
    script = repo_root / "implementations" / "uv_run.sh"
    return subprocess.run(
        [str(script), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def test_uv_run_usage_without_args_exits_2(repo_root: Path) -> None:
    # (en) Missing repo/command should fail fast with usage hint.
    # (kr) repo/command 가 없으면 usage 힌트와 함께 바로 실패해야 한다.
    proc = _run_uv_run(repo_root)
    assert proc.returncode == 2
    assert "usage:" in proc.stderr.lower()


def test_uv_run_unknown_repo_exits_2(repo_root: Path) -> None:
    # (en) Unknown gallery repo name is rejected before uv runs.
    # (kr) 알 수 없는 gallery repo 이름은 uv 실행 전에 거절된다.
    proc = _run_uv_run(repo_root, "not-a-real-repo", "python", "-c", "print(1)")
    assert proc.returncode == 2
    assert "unknown implementation repo" in proc.stderr.lower()
