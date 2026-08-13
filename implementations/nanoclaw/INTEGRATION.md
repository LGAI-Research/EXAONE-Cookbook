# NanoClaw + EXAONE — 연동 정본 (Phase 0)

> **상태:** 2026-05-28 — Path B 채택. 상세 실행은 `README.md` 및 단계별 스크립트 참고.

## 정본 경로: Path B — `/add-opencode` + EXAONE custom provider

NanoClaw trunk는 **Claude Agent SDK**(`AGENT_PROVIDER=claude`)가 기본이다. EXAONE은 **OpenAI-compatible** API이므로 Claude SDK에 `ANTHROPIC_BASE_URL`만 바꿔 끼우는 방식은 **동작하지 않는다**.

| 경로 | 설명 | Cookbook |
|------|------|----------|
| **B — OpenCode** | upstream `providers` 브랜치 `/add-opencode` skill → `AGENT_PROVIDER=opencode` + custom OpenAI-compatible provider | **정본** |
| A — Anthropic proxy | `implementations/nanoclaw/proxy/` (미구현) — Claude API ↔ OpenAI 변환 | OpenCode tool loop 실패 시만 검토 |
| C — `.env` 실험 | `ANTHROPIC_BASE_URL` = EXAONE | ❌ API 형식 불일치 |

### 왜 Path B인가

1. upstream NanoClaw가 공식 대안 provider로 **OpenCode**를 skill(`providers` 브랜치)로 제공한다.
2. OpenCode는 `@ai-sdk/openai-compatible` + `options.baseURL`로 **임의 OpenAI-compatible 엔드포인트**를 지원한다.
3. EXAONE은 `implementations/nanoclaw/.env`의 `EXAONE_BASE_URL` / `EXAONE_MODEL`과 직접 매핑 가능하다.
4. submodule **포크·패치 없이** skill 파일을 `implementations/nanoclaw/vendor/`에 vendoring; **submodules/nanoclaw working tree는 수정하지 않음**.

### Upstream pin

| 항목 | 값 |
|------|-----|
| NanoClaw submodule (main) | `62bd444` (tag `v2.1.54`) |
| OpenCode skill 소스 | `origin/providers` @ `9cfea509` (2026-08-12 fetch 기준) |
| OpenCode SDK + CLI pin | `1.18.16` (1.14.x 와 **비호환**; 1.4.x 대비 major bump — vendor 재적용 시 pin 확인) |

### EXAONE env 매핑

Cookbook `implementations/nanoclaw/.env` → NanoClaw host `.env` ( `scripts/sync_nanoclaw_env.sh` ):

| Cookbook | NanoClaw (OpenCode) |
|----------|---------------------|
| `EXAONE_BASE_URL` | `ANTHROPIC_BASE_URL` (OpenCode upstream baseURL 슬롯) |
| `EXAONE_MODEL` | `OPENCODE_MODEL=exaone/<model>` |
| `EXAONE_MODEL` | `OPENCODE_SMALL_MODEL=exaone/<model>` |
| (고정) | `OPENCODE_PROVIDER=exaone` |

**자격증명:** NanoClaw 운영 관례는 OneCLI Agent Vault (`HTTPS_PROXY` + host-pattern 주입). cookbook 데모 README의 OneCLI 절 참고. API 키를 컨테이너 `.env`에 넣지 않는다.

### Hermes vs NanoClaw (차별화)

| | Hermes Agent | NanoClaw |
|--|--------------|----------|
| 격리 | Gateway / terminal (앱 레벨) | **Docker 컨테이너** (OS-level) |
| EXAONE 연동 | `custom_providers` YAML | OpenCode provider + container poll loop |
| 데모 입구 | `hermes` CLI 한 턴 | **CLI scratch agent** (`pnpm run chat`) |
| Wow | Skills + delegation | **감사 가능한 작은 코드베이스** + container sandbox |

### Phase 로드맵 (implementations/nanoclaw/)

| Phase | 산출물 | 커밋 |
|-------|--------|------|
| 0 | 본 문서 + `scripts/check_env.py` | ✅ |
| 1 | `vendor/opencode-from-providers/`, `opencode.exaone.fragment.json`, `config.exaone.example.env` | ✅ |
| 2 | `scripts/sync_nanoclaw_env.sh`, `scripts/print_onecli_exaone.sh` | ✅ |
| 3 | `run_cli_demo.sh`, `samples/turn.example.json` | ✅ |
| 4 | `README.md` 완성 (요구사항·E2E·Expert opt-in) | ✅ |
| 5 | `run_exaone_turn.py` + `eval_smoke.py` (cookbook EXAONE 1턴) | ✅ |
