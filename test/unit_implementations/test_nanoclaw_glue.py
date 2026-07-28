"""NanoClaw glue — env sync, turn artifact validation (no live API by default)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NANOCLAW_IMPL = REPO_ROOT / "implementations" / "nanoclaw"
DEMO_QUESTION = (
    "EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘."
)


def test_sync_nanoclaw_env_dry_run(impl_env_dir) -> None:
    # (en) sync script renders OpenCode env vars from impl EXAONE_* without writing _out/.
    # (kr) sync 스크립트가 impl EXAONE_* 로부터 OpenCode env 블록을 렌더한다.
    impl_dir = impl_env_dir("nanoclaw")
    env = {k: v for k, v in os.environ.items() if not k.startswith("EXAONE_")}
    env["PYTHONPATH"] = str(REPO_ROOT / "implementations")
    env["EXAONE_IMPL_DIR"] = str(impl_dir)
    env["DRY_RUN"] = "1"

    proc = subprocess.run(
        ["bash", str(NANOCLAW_IMPL / "scripts" / "sync_nanoclaw_env.sh")],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OPENCODE_PROVIDER=exaone" in proc.stdout
    assert "OPENCODE_MODEL=exaone/test-model" in proc.stdout
    assert "ANTHROPIC_BASE_URL=https://example.com/v1" in proc.stdout


def test_eval_smoke_validates_turn_fixture(impl_env_dir) -> None:
    impl_dir = impl_env_dir("nanoclaw")
    out = impl_dir / "_out"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "question": DEMO_QUESTION,
        "answer": "네, 이 에이전트의 LLM 백본은 EXAONE입니다.",
        "provider": "opencode",
        "opencode_provider": "exaone",
        "channel": "cli",
        "success": True,
    }
    (out / "nanoclaw_turn.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(NANOCLAW_IMPL / "eval_smoke.py")],
        cwd=str(REPO_ROOT),
        env={
            **{k: v for k, v in os.environ.items() if not k.startswith("EXAONE_")},
            "PYTHONPATH": str(REPO_ROOT / "implementations"),
            "EXAONE_IMPL_DIR": str(impl_dir),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(proc.stdout)
    assert report["ok"] is True


def test_run_exaone_turn_mocked(impl_env_dir) -> None:
    impl_dir = impl_env_dir("nanoclaw")
    for path in (str(REPO_ROOT), str(REPO_ROOT / "implementations")):
        if path not in sys.path:
            sys.path.insert(0, path)

    mock_response = MagicMock()
    mock_response.content = "EXAONE이 이 NanoClaw 에이전트의 LLM 백본입니다."

    with patch("exaone.llm.ExaoneAPIClient") as client_cls:
        client_cls.return_value.chat.return_value = mock_response

        spec = importlib.util.spec_from_file_location(
            "nanoclaw_run_exaone_turn",
            NANOCLAW_IMPL / "run_exaone_turn.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.main() == 0

    turn_path = impl_dir / "_out" / "nanoclaw_turn.json"
    assert turn_path.is_file()
    data = json.loads(turn_path.read_text(encoding="utf-8"))
    assert data["success"] is True
    assert data["provider"] == "opencode"
