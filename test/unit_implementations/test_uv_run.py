"""implementations/uv_run.sh router smoke (no API, no full uv sync required)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run_uv_run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # (en) Invoke uv_run.sh (Windows: uv_run.cmd) from cookbook root.
    # (kr) cookbook 루트에서 uv_run.sh(Windows: uv_run.cmd)를 호출한다.
    script = repo_root / "implementations" / ("uv_run.cmd" if os.name == "nt" else "uv_run.sh")
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


def test_gallery_uv_run_usage_without_bash(repo_root: Path) -> None:
    # (en) The shared logic in gallery.py must work without bash (Windows PowerShell/cmd path).
    # (kr) gallery.py 공통 로직은 bash 없이도 동작해야 한다(Windows PowerShell/cmd 경로).
    import sys

    gallery = repo_root / "implementations" / "gallery.py"
    proc = subprocess.run(
        [sys.executable, str(gallery), "uv-run", "not-a-real-repo", "python", "-c", "print(1)"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "unknown implementation repo" in proc.stderr.lower()


def test_every_sh_entrypoint_has_windows_cmd(repo_root: Path) -> None:
    # (en) Each gallery .sh entrypoint (except bash-only env.sh / brew helpers) has a .cmd twin.
    # (kr) gallery .sh 진입점마다(bash 전용 env.sh·brew 헬퍼 제외) .cmd 짝이 있어야 한다.
    impl = repo_root / "implementations"
    bash_only = {"env.sh", "add_feeds.sh", "install_dependencies.sh"}
    tracked = subprocess.run(
        ["git", "ls-files", "*.sh"], cwd=str(impl), capture_output=True, text=True, check=True
    ).stdout.split()
    assert tracked, "git ls-files found no .sh under implementations/"
    for rel in tracked:
        sh = impl / rel
        if sh.name in bash_only:
            continue
        twins = [sh.with_suffix(".cmd"), sh.parent.parent / sh.with_suffix(".cmd").name]
        assert any(t.is_file() for t in twins), f"missing .cmd twin for {sh.relative_to(repo_root)}"
        assert "gallery.py" in sh.read_text(encoding="utf-8"), f"{sh.name} should delegate to gallery.py"
