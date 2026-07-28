#!/usr/bin/env bash
#
# (en) Print OneCLI secret registration hints for EXAONE (host-pattern from impl .env).
# (kr) implementation .env 기준 EXAONE OneCLI secret 등록 힌트를 출력한다.
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/print_onecli_exaone.sh
#
# Does not call onecli — prints copy-paste commands only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKBOOK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
UV_RUN="$COOKBOOK_ROOT/implementations/uv_run.sh"

"$UV_RUN" nanoclaw python - <<'PY'
import json
import shutil
from urllib.parse import urlparse

from common.exaone_env import impl_dir, load_exaone_env, openai_compat_kwargs

load_exaone_env()
kw = openai_compat_kwargs()
host = urlparse(kw["base_url"]).hostname or "<host-from-EXAONE_BASE_URL>"
key_set = bool(kw["api_key"])
env_file = impl_dir() / ".env"

print("# (en) OneCLI — register EXAONE for NanoClaw container outbound proxy")
print("# (kr) OneCLI — NanoClaw 컨테이너 아웃바운드 프록시용 EXAONE 등록")
print()
if not key_set:
    print(f"# WARNING: EXAONE_API_KEY is not set in {env_file}")
    print()
print(f"# host-pattern derived from EXAONE_BASE_URL: {host}")
print()
print("onecli secrets create --name \"EXAONE\" --type generic \\")
print(f"  --value \"${{EXAONE_API_KEY:-<your-key>}}\" --host-pattern \"{host}\" \\")
print('  --header-name "Authorization" --value-format "Bearer {value}"')
print()
print("# (en) Grant the agent access (set-secrets replaces — include existing IDs):")
print("# (kr) 에이전트에 secret 부여 (set-secrets 는 교체 — 기존 ID 포함):")
print("# onecli agents list")
print("# onecli secrets list")
print("# onecli agents set-secrets --id <agent-id> --secret-ids <existing>,<exaone-secret-id>")
print()
print("# (en) After wiring, set groups/<folder>/container.json → \"provider\": \"opencode\"")
print("# (kr) wiring 후 groups/<folder>/container.json → \"provider\": \"opencode\"")
print()
report = {
    "host_pattern": host,
    "base_url": kw["base_url"],
    "model": kw["model"],
    "onecli_on_path": shutil.which("onecli"),
}
print("# check_env snapshot:")
print(json.dumps(report, ensure_ascii=False, indent=2))
PY
