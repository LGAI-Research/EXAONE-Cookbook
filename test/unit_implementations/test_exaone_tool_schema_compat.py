"""EXAONE tool JSON Schema compatibility — vendor config + live API regression."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NANOCLAW_IMPL = REPO_ROOT / "implementations" / "nanoclaw"
VENDOR_CONTAINER_OPENCODE = (
    NANOCLAW_IMPL
    / "vendor"
    / "opencode-from-providers"
    / "container"
    / "agent-runner"
    / "src"
    / "providers"
    / "opencode.ts"
)

_IMPL_ROOT = str(REPO_ROOT / "implementations")
if _IMPL_ROOT not in sys.path:
    sys.path.insert(0, _IMPL_ROOT)

pytest.importorskip("requests")

from nanoclaw.exaone_tool_schema_compat import (  # noqa: E402
    ONEOF_REJECTED_MESSAGE,
    nested_anyof_parameters,
    nested_oneof_parameters,
    post_tool_schema_probe,
)


def test_vendor_opencode_pins_openai_compatible_for_any_proxy_url() -> None:
    """Path B uses OPENCODE_PROVIDER=exaone; npm pin must not be openai-only."""
    src = VENDOR_CONTAINER_OPENCODE.read_text(encoding="utf-8")
    assert VENDOR_CONTAINER_OPENCODE.is_file(), f"missing vendor file: {VENDOR_CONTAINER_OPENCODE}"
    assert "provider === 'openai' && proxyUrl" not in src
    assert re.search(
        r"proxyUrl\s*\?\s*\{\s*npm:\s*'@ai-sdk/openai-compatible'\s*\}",
        src,
    ), "expected proxyUrl-gated @ai-sdk/openai-compatible npm pin in buildOpenCodeConfig"


def test_vendor_opencode_pin_is_current() -> None:
    snippet = (
        NANOCLAW_IMPL
        / "vendor"
        / "opencode-from-providers"
        / "patches"
        / "agent-runner-package.json.snippet"
    )
    text = snippet.read_text(encoding="utf-8")
    assert '"@opencode-ai/sdk": "1.18.16"' in text


@pytest.fixture
def live_exaone_kw(exaone_env_module):
    if os.environ.get("RUN_LIVE_TURN", "").strip().lower() not in ("1", "true", "yes"):
        pytest.skip("set RUN_LIVE_TURN=1 for live EXAONE tool schema probes")
    exaone_env_module.load_exaone_env(caller_file=str(NANOCLAW_IMPL / "run_exaone_turn.py"))
    kw = exaone_env_module.openai_compat_kwargs()
    if not kw.get("api_key"):
        pytest.skip("EXAONE_API_KEY not set in implementations/nanoclaw/.env")
    return kw


@pytest.mark.live
def test_exaone_rejects_nested_oneof_tool_schema(live_exaone_kw) -> None:
  response = post_tool_schema_probe(
      base_url=live_exaone_kw["base_url"],
      api_key=live_exaone_kw["api_key"],
      model=live_exaone_kw["model"],
      parameters=nested_oneof_parameters(),
  )
  assert response.status_code == 422
  assert ONEOF_REJECTED_MESSAGE in response.text


@pytest.mark.live
def test_exaone_accepts_nested_anyof_tool_schema(live_exaone_kw) -> None:
  response = post_tool_schema_probe(
      base_url=live_exaone_kw["base_url"],
      api_key=live_exaone_kw["api_key"],
      model=live_exaone_kw["model"],
      parameters=nested_anyof_parameters(),
  )
  assert response.status_code == 200, response.text[:500]
  assert ONEOF_REJECTED_MESSAGE not in response.text
