# Apply OpenCode vendor bundle to **your** NanoClaw fork

Cookbook does **not** modify `submodules/nanoclaw`. Copy from this vendor tree into a
**separate NanoClaw checkout or your fork**, then build there.

Providers ref: `origin/providers` @ `9cfea50972870e85bbb80d48310d4fda8e814eb7`
OpenCode pin: `1.18.16`

## 1. Copy source files

```bash
VENDOR="implementations/nanoclaw/vendor/opencode-from-providers"
NANOCLAW=/path/to/your/nanoclaw

cp "$VENDOR/src/providers/opencode.ts" "$NANOCLAW/src/providers/"
cp "$VENDOR/container/agent-runner/src/providers/opencode.ts" "$NANOCLAW/container/agent-runner/src/providers/"
cp "$VENDOR/container/agent-runner/src/providers/mcp-to-opencode.ts" "$NANOCLAW/container/agent-runner/src/providers/"
cp "$VENDOR/container/agent-runner/src/providers/mcp-to-opencode.test.ts" "$NANOCLAW/container/agent-runner/src/providers/"
cp "$VENDOR/container/agent-runner/src/providers/opencode.factory.test.ts" "$NANOCLAW/container/agent-runner/src/providers/"
```

## 2. Barrel imports

Append to `src/providers/index.ts` and `container/agent-runner/src/providers/index.ts`:

```typescript
import './opencode.js';
```

## 3. agent-runner dependency

```bash
cd "$NANOCLAW/container/agent-runner"
bun add @opencode-ai/sdk@1.18.16
```

## 4. Dockerfile

See `patches/dockerfile-opencode.snippet`.

## 5. Build

```bash
cd "$NANOCLAW"
pnpm run build
pnpm exec tsc -p container/agent-runner/tsconfig.json --noEmit
./container/build.sh
```

## 6. EXAONE env

Merge `implementations/nanoclaw/_out/nanoclaw.exaone.env` (from sync_nanoclaw_env.sh) into **your** NanoClaw host `.env`.

Upstream skill: fetch `origin/providers` and see `.claude/skills/add-opencode/SKILL.md`.
