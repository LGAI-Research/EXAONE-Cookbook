#!/usr/bin/env bash
# (en) Non-interactive CrewAI + EXAONE demo orchestrator.
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\crewai\run_cli_demo.cmd).
# (kr) 비대화형 CrewAI + EXAONE 데모 오케스트레이터.
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\crewai\run_cli_demo.cmd).
#
# Usage (cookbook root):
#   implementations/crewai/run_cli_demo.sh [--live] [--crew]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" demo crewai "$@"
