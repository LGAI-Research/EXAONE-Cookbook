# hermes-agent + EXAONE

Hermes upstream + **EXAONE** custom provider. Upstream: `submodules/hermes-agent` (직접 clone).

## 3-step quick start

Cookbook **루트**에서:

```bash
# upstream (최초 1회) — 전체 가이드: implementations/README.md
git clone https://github.com/NousResearch/hermes-agent.git submodules/hermes-agent

cp implementations/hermes-agent/.env.example implementations/hermes-agent/.env
# .env 에 EXAONE_BASE_URL, EXAONE_API_KEY, EXAONE_MODEL 설정

./implementations/hermes-agent/run_cli_demo.sh          # 스모크
source implementations/hermes-agent/scripts/env.sh       # 셸 env
implementations/hermes-agent/scripts/run_hermes.sh       # 대화형 Hermes
```

세션: `/model custom:exaone/<EXAONE_MODEL>`

## 파일 구조

| 경로 | 역할 |
|------|------|
| `.env` | **정본** — EXAONE 키·URL·모델·SSL |
| `.hermes/` | `HERMES_HOME` (config·세션, gitignore) |
| `scripts/hermes_glue.py` | 접착 **단일 CLI** — `check` `render` `ping` `export-shell` `run` |
| `scripts/env.sh` | `source` → `HERMES_HOME` + `EXAONE_*` export |
| `scripts/run_hermes.sh` | Hermes 실행 (SSL 패치 포함); **CWD=`implementations/hermes-agent`** |
| `run_cli_demo.sh` | 비대화형 스모크 |
| `skills/` | 선택 cookbook 스킬 |

## `hermes_glue.py` 명령

```bash
./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py check
./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py render
./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py ping
eval "$(./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py export-shell)"
```

## 문제 해결

| 증상 | 조치 |
|------|------|
| `APIConnectionError` / SSL | `.env` 에 `DISABLE_SSL_VERIFY=1` — **`run_hermes.sh`만** 사용 (직접 `hermes` X) |
| `Auxiliary title generation failed` | 부가 LLM(제목) — 대화는 OK, `/title` 수동 또는 `run_hermes.sh` 재시작 |
| ping OK · Hermes 실패 | `source scripts/env.sh` 후 `run_hermes.sh` |
| `unknown` 상태바 | `env.sh` source → `/model custom:exaone/...` |
| doctor ⚠ 많음 | EXAONE-only 데모면 OAuth/web/discord **무시** |
| 빈 assistant content | reasoning-only — [`PLAYBOOK.md`](../../PLAYBOOK.md) §6.3.1 |
| 401/403 | `.env` 키·URL·크레딧 확인 |

**키:** `implementations/hermes-agent/.env` → `hermes_glue.py render` 가 `.hermes/.env` 브릿지.

**upstream:** `submodules/hermes-agent` 는 **읽기 전용**. 에이전트·파일 도구 산출물은 `implementations/hermes-agent/` 에만 생깁니다. `hermes_glue.py check` 가 upstream dirty 를 감지합니다.

## Expert (기본 off)

Gateway·terminal·cron 은 데모에서 켜지 않습니다. upstream Hermes 문서 참고.
