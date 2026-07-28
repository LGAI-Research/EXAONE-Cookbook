#!/usr/bin/env bash
# (en) Run Proof Gallery live smokes (all implementations or one --repo).
# (kr) Proof Gallery 라이브 스모크를 실행한다(전체 또는 --repo 하나).
#
# Usage (cookbook root):
#   implementations/run_live_smoke.sh                  # env-only phases
#   RUN_LIVE_TURN=1 implementations/run_live_smoke.sh  # EXAONE API live proofs
#   RUN_LIVE_TURN=1 RUN_LIVE_CREW=1 implementations/run_live_smoke.sh  # + CrewAI crew
#   implementations/run_live_smoke.sh --repo smolagents
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REPOS=(hermes-agent smolagents crewai browser-use nanoclaw)
ONLY_REPO=""

usage() {
  sed -n '2,12p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --repo)
      shift
      ONLY_REPO="${1:-}"
      if [[ -z "$ONLY_REPO" ]]; then
        echo "error: --repo requires a name" >&2
        exit 2
      fi
      ;;
    *) echo "unknown arg: $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

log() { printf '[live-smoke] %s\n' "$*"; }

run_demo() {
  local repo="$1"
  local demo="$SCRIPT_DIR/$repo/run_cli_demo.sh"
  if [[ ! -f "$demo" ]]; then
    log "skip $repo — no run_cli_demo.sh"
    return 0
  fi
  log "===== $repo ====="
  RUN_LIVE_TURN="${RUN_LIVE_TURN:-0}" RUN_LIVE_CREW="${RUN_LIVE_CREW:-0}" bash "$demo"
}

main() {
  cd "$ROOT"
  export RUN_LIVE_TURN="${RUN_LIVE_TURN:-0}"
  export RUN_LIVE_CREW="${RUN_LIVE_CREW:-0}"

  if [[ -n "$ONLY_REPO" ]]; then
    run_demo "$ONLY_REPO"
    return 0
  fi

  local failed=0
  for repo in "${REPOS[@]}"; do
    if ! run_demo "$repo"; then
      failed=1
      log "FAILED: $repo"
    fi
  done
  if [[ "$failed" -ne 0 ]]; then
    exit 1
  fi
  log "all demos finished"
}

main "$@"
