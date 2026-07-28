# implementations/ — EXAONE Proof Gallery

**대상:** AI·에이전트에 익숙한 독자 (recipes Track 00–10 **이후** 또는 병행).

**역할:** 외부 **선진 OSS 하니스**를 로컬에 clone하고, **EXAONE**을 백본 LLM으로 붙인 **재현 가능한 데모**를 둡니다.

| 항목 | 위치 |
|------|------|
| **인수인계·전체 설계** | [`docs/implementations.md`](../docs/implementations.md) |
| **Upstream 소스 (수정 금지)** | `submodules/<repo-name>/` — **직접 clone** (레포에 미포함) |
| **Cookbook 접착 코드만** | `implementations/<repo-name>/` |
| **공통 env 헬퍼** | `implementations/common/exaone_env.py` |
| **격리 실행 래퍼** | [`uv_run.sh`](./uv_run.sh) |

## Upstream clone (필수 — git submodule 아님)

`submodules/` 아래 5개 프로젝트는 **git submodule이 아닙니다.**  
Cookbook을 clone한 뒤, 사용할 데모만 골라 upstream을 **직접** clone 하세요.

```bash
cd <cookbook-root>
mkdir -p submodules

git clone https://github.com/NousResearch/hermes-agent.git submodules/hermes-agent
git clone https://github.com/browser-use/browser-use.git    submodules/browser-use
git clone https://github.com/nanocoai/nanoclaw.git         submodules/nanoclaw
git clone https://github.com/crewAIInc/crewAI.git          submodules/crewai
git clone https://github.com/huggingface/smolagents.git    submodules/smolagents
```

필요하면 권장 커밋으로 checkout (호환이 검증된 pin):

```bash
git -C submodules/hermes-agent  checkout 8208fc527
git -C submodules/browser-use   checkout 8342696
git -C submodules/nanoclaw      checkout 2492259
git -C submodules/crewai        checkout 2148c7e
git -C submodules/smolagents    checkout 13724b5
```

| Repo | Clone URL | 권장 pin | Implementation | Upstream 라이선스 |
|------|-----------|----------|----------------|-------------------|
| Hermes Agent | https://github.com/NousResearch/hermes-agent.git | `8208fc527` | `implementations/hermes-agent/` | MIT |
| browser-use | https://github.com/browser-use/browser-use.git | `8342696` (tag `0.12.9`) | `implementations/browser-use/` | MIT |
| NanoClaw | https://github.com/nanocoai/nanoclaw.git | `2492259` | `implementations/nanoclaw/` | MIT |
| CrewAI | https://github.com/crewAIInc/crewAI.git | `2148c7e` | `implementations/crewai/` | MIT |
| smolagents | https://github.com/huggingface/smolagents.git | `13724b5` | `implementations/smolagents/` | Apache-2.0 |

Cookbook 본문·`implementations/` 접착 코드: [`LICENSE.md`](../LICENSE.md) (BSD-3-Clause-LG AI Research). OSS Notice 정본: [`NOTICE.md`](../NOTICE.md).

**정책**

- `submodules/<name>/` 는 **읽기 전용** 참고용 — 기능 패치는 upstream PR.
- Cookbook에 커밋되는 것은 `implementations/<name>/` 접착 코드만.
- `submodules/*` 는 `.gitignore` — clone한 내용이 실수로 push되지 않습니다.

## 환경 분리 (cookbook vs implementations)

| | Cookbook (`recipes/`, `exaone/`, `eval/`) | Proof Gallery (`implementations/*`) |
|--|-------------------------------------------|-----------------------------------|
| **`.env`** | 레포 **루트** `.env` | 각 폴더 `implementations/<repo>/.env` |
| **Python venv** | 루트 `.venv` + `pip install -r requirements.txt` | 각 폴더 `implementations/<repo>/.venv` (**uv**) |
| **`exaone/` 패키지** | 루트 editable (`pip install -e ./exaone`) | 각 impl `pyproject.toml` → `exaone` **editable** (`uv sync --project implementations/<repo>`) |
| **실행** | `python -m eval.run` 등 | `./implementations/uv_run.sh <repo> python ...` |

```bash
# 예: smolagents 데모 (upstream clone 후)
cp implementations/smolagents/.env.example implementations/smolagents/.env   # EXAONE_* 채우기
uv sync --project implementations/smolagents   # 최초 1회 — exaone/ editable 포함
./implementations/uv_run.sh smolagents python scripts/check_env.py
./implementations/uv_run.sh smolagents python run_agent.py

# 예: hermes-agent (upstream clone + glue)
cp implementations/hermes-agent/.env.example implementations/hermes-agent/.env
./implementations/hermes-agent/run_cli_demo.sh
implementations/hermes-agent/scripts/run_hermes.sh
```

`uv` 미설치: https://docs.astral.sh/uv/getting-started/installation/

## 네이밍 규칙 (고정)

- 폴더명 = GitHub **repository 이름**: `hermes-agent`, `browser-use`, `nanoclaw`, `crewai`, `smolagents`
- `submodules/<name>` ↔ `implementations/<name>` **1:1**
- `S1_`, `A1_` 같은 티어 접두사 **사용 안 함**
- 새 레포 추가: upstream을 `submodules/<name>/`에 clone → 동일 이름으로 `implementations/<name>/` 생성 → 이 README 표에 행 추가

## recipes와의 경계

다음은 **recipes에서 이미 다룸** → implementations에 **중복으로 두지 않음**:

- LangGraph, LlamaIndex, LangChain, Gradio → `recipes/track09_framework_bridges/`
- MCP 프로토콜·stdio 클라이언트 → `recipes/track03_tools_and_mcp/`
- RAG 인프라·pgvector → `recipes/track04_*`, `infrastructure/`

## 클론 후 초기화

```bash
git clone <cookbook-url>
cd <cookbook-root>

# cookbook 본체 (recipes/eval 용 — implementations 와 별도)
cp .env.example .env

# Proof Gallery를 쓸 때만 — 위에서 upstream clone
# (예: smolagents만)
git clone https://github.com/huggingface/smolagents.git submodules/smolagents
cp implementations/smolagents/.env.example implementations/smolagents/.env
uv sync --project implementations/smolagents
```

각 `implementations/<repo>/README.md` 에 데모 실행 방법이 있습니다.

## 라이브 스모크 (일괄·개별)

```bash
# 환경만 (API 호출 없음 — hermes/nanoclaw 일부 단계 제외)
implementations/run_live_smoke.sh

# EXAONE API 라이브 proof (repo마다 RUN_LIVE_TURN=1)
RUN_LIVE_TURN=1 implementations/run_live_smoke.sh

# 하나만
RUN_LIVE_TURN=1 implementations/run_live_smoke.sh --repo smolagents

# CrewAI 3-agent crew까지 (느림)
RUN_LIVE_TURN=1 RUN_LIVE_CREW=1 implementations/run_live_smoke.sh --repo crewai
```

| Repo | 오케스트레이터 | 검증 스크립트 | 라이브 산출물 |
|------|----------------|---------------|---------------|
| hermes-agent | `run_cli_demo.sh` | `eval_smoke.py` | `_out/cli_smoke.json` |
| smolagents | `run_cli_demo.sh` | `eval_smoke.py --run` | `_out/run.json` |
| crewai | `run_cli_demo.sh` | `eval_smoke.py --run` (`--full`) | `_out/spike_llm.json` (+ `crew_trace.json`) |
| browser-use | `run_cli_demo.sh` | `eval_smoke.py --run` | `_out/run.json` |
| nanoclaw | `run_cli_demo.sh` | `eval_smoke.py --run` | `_out/nanoclaw_turn.json` |
