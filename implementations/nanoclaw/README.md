# nanoclaw + EXAONE

| | |
|--|--|
| **Upstream** | `submodules/nanoclaw` (직접 clone) → [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) |
| **상태** | 🟢 E2E — cookbook `run_exaone_turn.py` + fork `pnpm run chat` (Docker) |
| **담당 작업** | `docs/implementations.md` §7.3 |
| **연동 정본** | [`INTEGRATION.md`](./INTEGRATION.md) — **Path B: `/add-opencode` + EXAONE custom provider** |

## Wow 목표

**Docker 컨테이너 격리** + CLI(또는 메시징) 입구에서 에이전트가 돌아가고, LLM 백본이 **EXAONE**임을 보여준다.

## EXAONE 연동 (정본)

**Path B only** — upstream `providers` 브랜치 `/add-opencode` skill을 cookbook 접착 스크립트로 적용한 뒤, OpenCode custom OpenAI-compatible provider에 EXAONE을 연결한다. fallback 정책은 [`INTEGRATION.md`](./INTEGRATION.md).

| Cookbook `implementations/nanoclaw/.env` | NanoClaw host `.env` (OpenCode) |
|-----------------|----------------------------------|
| `EXAONE_BASE_URL` | `ANTHROPIC_BASE_URL` |
| `EXAONE_MODEL` | `OPENCODE_MODEL=exaone/<model>` |
| (고정) | `OPENCODE_PROVIDER=exaone` |

자격증명은 **OneCLI Agent Vault**로 주입한다. **`submodules/nanoclaw`는 read-only** — cookbook 스크립트가 upstream working tree를 수정하지 않는다.

## Upstream 정책 (중요)

| 경로 | 역할 |
|------|------|
| `submodules/nanoclaw/` | upstream **read-only** (직접 clone, **수정·커밋 금지**) |
| `implementations/nanoclaw/` | cookbook **접착 코드** — vendor·env·문서 |
| **본인 NanoClaw fork** | 실제 설치·빌드·`pnpm run chat` |

OpenCode provider 파일은 `implementations/nanoclaw/vendor/opencode-from-providers/`에 vendoring한 뒤, [`APPLY-TO-YOUR-NANOCLAW-FORK.md`](./vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md) 절차로 **fork에** 적용한다.

## 사전 준비

Cookbook **루트**에서:

```bash
# upstream (최초 1회) — 전체 가이드: implementations/README.md
git clone https://github.com/nanocoai/nanoclaw.git submodules/nanoclaw
cp implementations/nanoclaw/.env.example implementations/nanoclaw/.env
uv sync --project implementations/nanoclaw
```

| 항목 | 버전·설명 |
|------|-----------|
| **Docker** | Desktop(macOS/Windows) 또는 Engine(Linux) — **필수** |
| **Node.js** | 20+ |
| **pnpm** | 10+ (`submodules/nanoclaw/nanoclaw.sh` 가 bootstrap 가능) |
| **Bun** | agent-runner 의존성 설치 시 권장 (fork에서 `bun add`) |
| **OneCLI** | 전체 NanoClaw 운영 시 권장 — [`scripts/print_onecli_exaone.sh`](./scripts/print_onecli_exaone.sh) |
| **EXAONE** | `implementations/nanoclaw/.env` `EXAONE_*` (OpenAI-compatible) |

## 한 줄 데모 (오케스트레이터)

```bash
# cookbook 루트 — vendor + env 렌더 (submodule 미수정)
implementations/nanoclaw/run_cli_demo.sh

# EXAONE API 1턴 proof (Docker 불필요)
./implementations/uv_run.sh nanoclaw python run_exaone_turn.py
./implementations/uv_run.sh nanoclaw python eval_smoke.py

# 전체 오케스트레이터 + live turn
RUN_LIVE_TURN=1 implementations/nanoclaw/run_cli_demo.sh
```

선수 조건 체크:

```bash
implementations/nanoclaw/scripts/install_prerequisites.sh
```

스모크만:

```bash
./implementations/uv_run.sh nanoclaw python scripts/check_env.py
```

Tool schema regression (vendor static + optional live EXAONE API):

```bash
pytest test/unit_implementations/test_exaone_tool_schema_compat.py
RUN_LIVE_TURN=1 pytest test/unit_implementations/test_exaone_tool_schema_compat.py
```

## 단계별 실행

### 1. OpenCode vendor bundle (repo에 포함)

경로: `implementations/nanoclaw/vendor/opencode-from-providers/`

upstream `origin/providers` @ `9cfea509` 스냅샷이 **cookbook에 커밋**되어 있다. submodule은 **read-only**.

OpenCode SDK/CLI pin: **1.18.16**

fork 적용: `vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md`

### 2. EXAONE env 렌더

```bash
implementations/nanoclaw/scripts/sync_nanoclaw_env.sh
```

출력: `implementations/nanoclaw/_out/nanoclaw.exaone.env` → **본인 fork** `.env`에 병합.

### 3. OneCLI secret (운영 경로)

```bash
implementations/nanoclaw/scripts/print_onecli_exaone.sh
```

출력된 `onecli secrets create` / `agents set-secrets` 를 따라 EXAONE 키를 등록한다.

### 4. NanoClaw host + container (**본인 fork**)

```bash
cd /path/to/your/nanoclaw-fork
bash nanoclaw.sh          # 최초 1회
./container/build.sh      # vendor 적용 후 이미지 재빌드
```

`groups/<folder>/container.json`:

```json
{ "provider": "opencode" }
```

### 5. CLI 한 턴

**Cookbook (EXAONE LLM proof, Docker 없음):**

```bash
./implementations/uv_run.sh nanoclaw python run_exaone_turn.py
```

응답: `implementations/nanoclaw/_out/nanoclaw_turn.json` (gitignore)

**본인 fork (컨테이너 샌드박스 E2E):**

```bash
cd /path/to/your/nanoclaw-fork
pnpm install
pnpm exec tsx scripts/init-cli-agent.ts --display-name "Cookbook" --agent-name "ExaoneDemo"
pnpm run chat
```

질의 예:

```
EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘.
```

응답은 `implementations/nanoclaw/_out/nanoclaw_turn.json` 에 저장 (gitignore). 형식 샘플: [`samples/turn.example.json`](./samples/turn.example.json)

## Hermes vs NanoClaw

| | Hermes Agent | NanoClaw + EXAONE |
|--|--------------|-------------------|
| **격리** | Gateway / terminal (앱 레벨) | **Docker 컨테이너** |
| **EXAONE 연동** | `custom_providers` YAML | OpenCode + `OPENCODE_*` |
| **데모 입구** | `hermes` CLI | **`pnpm run chat`** (CLI scratch agent) |
| **Wow** | Skills + delegation | **작은 코드베이스** + container sandbox |

## EXAONE 특이사항

- EXAONE API: 빈 `content` / reasoning-only 응답 가능 → [`PLAYBOOK.md`](../../PLAYBOOK.md) §6.3.1
- OpenCode tool loop 실패 시 fallback 후보만 [`INTEGRATION.md`](./INTEGRATION.md) Path A (`proxy/` 미구현)
- OpenCode CLI **1.14.x** 는 SDK 1.4.x 와 **비호환** — pin 유지

## Expert track (opt-in)

WhatsApp · Telegram · Discord 등 **실메신저** 연동은 upstream `nanoclaw.sh` + `/add-<channel>` skill 로만 진행한다.

- 실계정·실연락처 사용 전 **Maintainer 승인** 및 allowlist 정책 준수
- cookbook 기본 데모는 **CLI 채널만** — 메신저는 Expert 문서로 분리
- API 키: `implementations/nanoclaw/.env` + OneCLI; 공개 채널 로그에 키 노출 금지

## 산출물 체크리스트

- [x] `README.md` — Docker / Node 20+ / pnpm 요구사항
- [x] `config.exaone.example.env` + `opencode.exaone.fragment.json`
- [x] `vendor/opencode-from-providers/` + env/OneCLI 스크립트
- [x] `run_cli_demo.sh` + `samples/turn.example.json`
- [x] `run_exaone_turn.py` + `eval_smoke.py` — cookbook EXAONE 1턴 E2E
- [x] `scripts/install_prerequisites.sh` — Docker/Node/pnpm 체크리스트
- [x] Expert: 실채널 opt-in 절 (본 README)
- [ ] fork Docker E2E: `pnpm run chat` (운영자 머신·OneCLI)

## 파일 맵

| 파일 | 역할 |
|------|------|
| [`INTEGRATION.md`](./INTEGRATION.md) | 정본 경로·Phase 로드맵 |
| [`vendor/opencode-from-providers/`](./vendor/opencode-from-providers/) | OpenCode provider 스냅샷 (submodule 미수정) |
| [`scripts/sync_nanoclaw_env.sh`](./scripts/sync_nanoclaw_env.sh) | `EXAONE_*` → `_out/nanoclaw.exaone.env` |
| [`scripts/print_onecli_exaone.sh`](./scripts/print_onecli_exaone.sh) | OneCLI 등록 명령 출력 |
| [`scripts/check_env.py`](./scripts/check_env.py) | Phase 0 스모크 |
| [`run_cli_demo.sh`](./run_cli_demo.sh) | env 오케스트레이터 (`RUN_LIVE_TURN=1`) |
| [`run_exaone_turn.py`](./run_exaone_turn.py) | Cookbook EXAONE 1턴 → `_out/nanoclaw_turn.json` |
| [`eval_smoke.py`](./eval_smoke.py) | 턴 산출물 검증 (`--run` 옵션) |
| [`scripts/install_prerequisites.sh`](./scripts/install_prerequisites.sh) | 선수 조건 체크리스트 |

## 의존성

- Docker Desktop 또는 Docker Engine
- Node.js 20+, pnpm 10+
- `implementations/nanoclaw/.env` `EXAONE_*`
- 상세: [`docs/implementations.md`](../../docs/implementations.md) §7.3
