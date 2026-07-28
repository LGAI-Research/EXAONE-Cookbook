#!/usr/bin/env bash
#
# (en) Vendor upstream /add-opencode files from the providers branch into
#      implementations/nanoclaw/vendor/ only. Does NOT modify submodules/nanoclaw.
# (kr) upstream providers 브랜치 /add-opencode 파일을 implementations/nanoclaw/vendor/
#      에만 vendoring 한다. submodules/nanoclaw 는 수정하지 않는다.
#
# Usage (cookbook root):
#   implementations/nanoclaw/apply-opencode-from-providers.sh
#
# Env:
#   NANOCLAW_ROOT          default: <cookbook>/submodules/nanoclaw (read-only git source)
#   NANOCLAW_PROVIDERS_REF default: origin/providers
#   OPENCODE_VERSION       default: 1.4.17
#   VENDOR_ROOT            default: implementations/nanoclaw/vendor/opencode-from-providers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKBOOK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NANOCLAW_ROOT="${NANOCLAW_ROOT:-$COOKBOOK_ROOT/submodules/nanoclaw}"
PROVIDERS_REF="${NANOCLAW_PROVIDERS_REF:-origin/providers}"
OPENCODE_VERSION="${OPENCODE_VERSION:-1.4.17}"
VENDOR_ROOT="${VENDOR_ROOT:-$SCRIPT_DIR/vendor/opencode-from-providers}"

log() { printf '[apply-opencode] %s\n' "$*"; }
die() { printf '[apply-opencode] ERROR: %s\n' "$*" >&2; exit 1; }

git_show() {
  git -C "$NANOCLAW_ROOT" show "${PROVIDERS_REF}:$1"
}

copy_vendor_file() {
  local rel="$1"
  local dest="$VENDOR_ROOT/$rel"
  mkdir -p "$(dirname "$dest")"
  git_show "$rel" > "$dest"
  log "vendored: $rel"
}

write_barrel_snippets() {
  mkdir -p "$VENDOR_ROOT/patches"
  printf '%s\n' "import './opencode.js';" > "$VENDOR_ROOT/patches/host-providers-index.snippet"
  printf '%s\n' "import './opencode.js';" > "$VENDOR_ROOT/patches/container-providers-index.snippet"
  cat > "$VENDOR_ROOT/patches/agent-runner-package.json.snippet" <<EOF
{
  "dependencies": {
    "@opencode-ai/sdk": "${OPENCODE_VERSION}"
  }
}
EOF
  cat > "$VENDOR_ROOT/patches/dockerfile-opencode.snippet" <<EOF
ARG OPENCODE_VERSION=${OPENCODE_VERSION}

# (en) Append after claude-code global install in container/Dockerfile:
# (kr) container/Dockerfile 의 claude-code global install 다음에 추가:
RUN --mount=type=cache,target=/root/.cache/pnpm \\
    pnpm install -g "opencode-ai@\${OPENCODE_VERSION}"
EOF
  log "wrote patch snippets under vendor/opencode-from-providers/patches/"
}

write_apply_instructions() {
  local providers_sha="$1"
  cat > "$VENDOR_ROOT/APPLY-TO-YOUR-NANOCLAW-FORK.md" <<EOF
# Apply OpenCode vendor bundle to **your** NanoClaw fork

Cookbook does **not** modify \`submodules/nanoclaw\`. Copy from this vendor tree into a
**separate NanoClaw checkout or your fork**, then build there.

Providers ref: \`${PROVIDERS_REF}\` @ \`${providers_sha}\`
OpenCode pin: \`${OPENCODE_VERSION}\`

## 1. Copy source files

\`\`\`bash
VENDOR="implementations/nanoclaw/vendor/opencode-from-providers"
NANOCLAW=/path/to/your/nanoclaw

cp "\$VENDOR/src/providers/opencode.ts" "\$NANOCLAW/src/providers/"
cp "\$VENDOR/container/agent-runner/src/providers/opencode.ts" "\$NANOCLAW/container/agent-runner/src/providers/"
cp "\$VENDOR/container/agent-runner/src/providers/mcp-to-opencode.ts" "\$NANOCLAW/container/agent-runner/src/providers/"
cp "\$VENDOR/container/agent-runner/src/providers/mcp-to-opencode.test.ts" "\$NANOCLAW/container/agent-runner/src/providers/"
cp "\$VENDOR/container/agent-runner/src/providers/opencode.factory.test.ts" "\$NANOCLAW/container/agent-runner/src/providers/"
\`\`\`

## 2. Barrel imports

Append to \`src/providers/index.ts\` and \`container/agent-runner/src/providers/index.ts\`:

\`\`\`typescript
import './opencode.js';
\`\`\`

## 3. agent-runner dependency

\`\`\`bash
cd "\$NANOCLAW/container/agent-runner"
bun add @opencode-ai/sdk@${OPENCODE_VERSION}
\`\`\`

## 4. Dockerfile

See \`patches/dockerfile-opencode.snippet\`.

## 5. Build

\`\`\`bash
cd "\$NANOCLAW"
pnpm run build
pnpm exec tsc -p container/agent-runner/tsconfig.json --noEmit
./container/build.sh
\`\`\`

## 6. EXAONE env

Merge \`implementations/nanoclaw/_out/nanoclaw.exaone.env\` (from sync_nanoclaw_env.sh) into **your** NanoClaw host \`.env\`.

Upstream skill: fetch \`origin/providers\` and see \`.claude/skills/add-opencode/SKILL.md\`.
EOF
  log "wrote: $VENDOR_ROOT/APPLY-TO-YOUR-NANOCLAW-FORK.md"
}

verify() {
  local ok=1
  [[ -f "$VENDOR_ROOT/src/providers/opencode.ts" ]] \
    && log "verify: host provider OK" || { log "verify FAIL: host provider"; ok=0; }
  [[ -f "$VENDOR_ROOT/container/agent-runner/src/providers/opencode.ts" ]] \
    && log "verify: container provider OK" || { log "verify FAIL: container provider"; ok=0; }
  [[ -f "$VENDOR_ROOT/patches/dockerfile-opencode.snippet" ]] \
    && log "verify: patches OK" || { log "verify FAIL: patches"; ok=0; }
  [[ "$ok" -eq 1 ]] || die "verification failed"
}

main() {
  git -C "$NANOCLAW_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "nanoclaw missing — git clone https://github.com/nanocoai/nanoclaw.git submodules/nanoclaw"

  log "read-only source: $NANOCLAW_ROOT"
  log "vendor dest:      $VENDOR_ROOT"
  log "providers ref:    $PROVIDERS_REF"
  log "opencode pin:     $OPENCODE_VERSION"

  log "fetching providers branch (git metadata only, no working tree writes in submodule)..."
  git -C "$NANOCLAW_ROOT" fetch origin providers

  git_show ".claude/skills/add-opencode/SKILL.md" >/dev/null \
    || die "add-opencode skill missing at $PROVIDERS_REF"

  copy_vendor_file "src/providers/opencode.ts"
  copy_vendor_file "container/agent-runner/src/providers/opencode.ts"
  copy_vendor_file "container/agent-runner/src/providers/mcp-to-opencode.ts"
  copy_vendor_file "container/agent-runner/src/providers/mcp-to-opencode.test.ts"
  copy_vendor_file "container/agent-runner/src/providers/opencode.factory.test.ts"
  copy_vendor_file ".claude/skills/add-opencode/SKILL.md"

  write_barrel_snippets
  local providers_sha
  providers_sha="$(git -C "$NANOCLAW_ROOT" rev-parse "$PROVIDERS_REF")"
  write_apply_instructions "$providers_sha"
  verify

  log "done — submodule untouched. Read: $VENDOR_ROOT/APPLY-TO-YOUR-NANOCLAW-FORK.md"
  log "Next: implementations/nanoclaw/scripts/sync_nanoclaw_env.sh"
}

main "$@"
