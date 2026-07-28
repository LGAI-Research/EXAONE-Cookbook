# `implementations/` — 인수인계서 (EXAONE Proof Gallery)

> **독자:** 이 문서를 받은 에이전트·엔지니어.  
> **목적:** `recipes/`(입문)와 분리된 **선진 OSS 하니스 + EXAONE** 쇼케이스를 upstream 직접 clone + 접착 코드로 구축한다.  
> **상태:** 2026-07 — git submodule 제거. `submodules/` 는 유저가 직접 clone (레포 미포함).

---

## 1. 배경·포지셔닝

### 1.1 Cookbook 안에서의 위치

| 레이어 | 경로 | 독자 | 목표 |
|--------|------|------|------|
| **입문·학습** | `recipes/track00_*` … `track10_*` | EXAONE·에이전트 처음 | 단계별 노트북, Track 08 eval |
| **공식 라이브러리** | `exaone/` | 서비스·노트북 개발자 | ToolAgent, RAG, memory, observability |
| **인프라** | `infrastructure/` | RAG 운영 | Postgres, embedding, setup |
| **벤치마크** | `eval/` | 모델·하네스 비교 | M1–M10 naive vs harness |
| **Proof Gallery** | `implementations/` + `submodules/` | **AI 고수** | “와, EXAONE으로 **이것도** 되네?” |

`reference_implementations/` 는 **제거**되었다. 튜토리얼 데모는 `recipes/trackNN_*` 노트북·동반 폴더에 두고, 외부 OSS 쇼케이스는 `implementations/<repo-name>/` 에만 추가한다.

### 1.2 설계 원칙 (합의됨)

1. **Build first, wow second** — 30초~2분 안에 재현 가능한 데모·스크립트·`_out/` 산출물.
2. **EXAONE 중심** — 모든 데모의 LLM 백본은 `implementations/<repo>/.env` 의 `EXAONE_*` (OpenAI-compatible). cookbook 루트 `.env` 와 **분리**.
3. **Upstream은 직접 clone** — `submodules/<repo-name>/` 는 유저가 clone한 upstream (`.gitignore`, 레포 미포함). 기능 PR은 upstream으로.
4. **접착만 cookbook** — `implementations/<repo-name>/` 에만 YAML·스크립트·README·skill.
5. **recipes와 중복 금지** — LangGraph, LlamaIndex, MCP 등은 recipes에 있음 → implementations에 중복으로 두지 않음.

### 1.3 네이밍 규칙 (변경 금지)

- 폴더명 = GitHub **repository 이름** (소문자·하이픈 유지).
- `submodules/hermes-agent` ↔ `implementations/hermes-agent` **1:1**.
- `S1_`, `A1_`, 티어 접두사 **사용 안 함**.
- 새 레포 추가 절차:

```bash
mkdir -p submodules
git clone https://github.com/<org>/<repo>.git submodules/<repo>
mkdir -p implementations/<repo>
# implementations/<repo>/README.md + glue
# implementations/README.md · docs/implementations.md 표에 1행 추가
```

공통 코드: `implementations/common/` (예: `exaone_env.py`).  
Clone 가이드 정본: [`implementations/README.md`](../implementations/README.md).

---

## 2. 초안 5종 — 권장 pin (유저 clone)

| Repo | Path | Upstream | 권장 pin | Upstream license |
|------|------|----------|----------|------------------|
| hermes-agent | `submodules/hermes-agent` | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | `8208fc527` | MIT |
| browser-use | `submodules/browser-use` | [browser-use/browser-use](https://github.com/browser-use/browser-use) | `8342696` (tag `0.12.9`) | MIT |
| nanoclaw | `submodules/nanoclaw` | [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) | `2492259` | MIT |
| crewai | `submodules/crewai` | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | `2148c7e` | MIT |
| smolagents | `submodules/smolagents` | [huggingface/smolagents](https://github.com/huggingface/smolagents) | `13724b5` | Apache-2.0 |

**클론 (git submodule 아님):**

```bash
mkdir -p submodules
git clone https://github.com/NousResearch/hermes-agent.git submodules/hermes-agent
git clone https://github.com/browser-use/browser-use.git    submodules/browser-use
git clone https://github.com/nanocoai/nanoclaw.git         submodules/nanoclaw
git clone https://github.com/crewAIInc/crewAI.git          submodules/crewai
git clone https://github.com/huggingface/smolagents.git    submodules/smolagents

# 선택: 권장 pin
git -C submodules/hermes-agent checkout 8208fc527
git -C submodules/browser-use  checkout 8342696
git -C submodules/nanoclaw     checkout 2492259
git -C submodules/crewai       checkout 2148c7e
git -C submodules/smolagents   checkout 13724b5
```

### 2.1 버전 정책 (upstream `main` 자동 추적 안 함)

**핵심:** Cookbook 문서가 권장하는 것은 브랜치가 아니라 **커밋 SHA(또는 tag)** 이다. 유저가 `git pull` 로 최신을 당기면 접착층과 어긋날 수 있다.

**운영 규칙 (고정):**

| 규칙 | 설명 |
|------|------|
| **릴리스 tag 우선** | 가능하면 `v0.12.9` 등 **tag**에 pin. |
| **bump는 문서 + 스모크** | 권장 SHA 변경 시 `implementations/README.md` · 이 표 · 해당 `implementations/<repo>/` 스모크를 같이 갱신. |
| **패치는 접착층만** | upstream API 변경 → `implementations/<repo>/` 만 수정. `submodules/` 안 fork·대량 패치 최소화. |
| **레포에 upstream 소스 커밋 금지** | `submodules/*` 는 `.gitignore`. |

**한 줄 요약:** Upstream은 유저가 직접 clone하고, **권장 tag/SHA는 README에만** 기록한다. bump는 **문서 갱신 + `implementations/` 스모크**로만 한다.

---

## 3. recipes와의 경계 (다시 읽을 것)

| 주제 | recipes | implementations |
|------|---------|-----------------|
| LangGraph, LangChain, LlamaIndex, Gradio | `recipes/track09_framework_bridges/` | ❌ |
| MCP stdio·discovery | `recipes/track03_tools_and_mcp/` | ❌ |
| pgvector RAG·GraphRAG | `recipes/track04_*`, `infrastructure/` | ❌ |
| `exaone.agents.ToolAgent` | `recipes/track02_*` | ❌ (smolagents는 **외부** 최소 루프 비교) |
| Workflow / planner-executor | `recipes/track06_*` | crewai는 **CrewAI API** 로 별도 wow |

`implementations/README.md` 에도 동일 안내가 있다.

---

## 4. 공통 EXAONE 환경

### 4.0 구현별 `.env` (필수)

각 Proof Gallery 데모는 **cookbook 루트 `.env` 가 아닌** 자기 폴더의 `.env` 를 씁니다.

```bash
cp implementations/<repo>/.env.example implementations/<repo>/.env
# EXAONE_API_KEY=
# EXAONE_BASE_URL=https://.../v1
# EXAONE_MODEL=...
```

템플릿 정본: [`implementations/common/.env.example`](../implementations/common/.env.example)

### 4.1 격리 실행 (uv)

| 항목 | 설명 |
|------|------|
| **venv** | `implementations/<repo>/.venv` (uv 가 관리, cookbook `.venv` 와 분리) |
| **의존성** | `implementations/<repo>/pyproject.toml` |
| **동기화** | `uv sync --project implementations/<repo>` |
| **실행** | `./implementations/uv_run.sh <repo> python <script>` |

```bash
uv sync --project implementations/smolagents
./implementations/uv_run.sh smolagents python run_agent.py
```

`uv_run.sh` 가 `PYTHONPATH=implementations` 와 `EXAONE_IMPL_DIR` 를 설정해 `common.exaone_env` 가 올바른 `.env` 를 읽게 한다.

### 4.2 `implementations/common/exaone_env.py`

| 함수 | 용도 |
|------|------|
| `repo_root()` | `exaone/` + `implementations/` 가 있는 cookbook 루트 |
| `impl_dir()` | 호출 스크립트의 `implementations/<repo>/` |
| `load_exaone_env()` | `implementations/<repo>/.env` 로드 |
| `openai_compat_kwargs()` | `base_url`, `api_key`, `model` dict |
| `get_disable_ssl_verify()` | implementation `.env` 의 TLS 플래그 |

**실행 패턴:**

```bash
./implementations/uv_run.sh <repo> python run_*.py
```

```python
import sys
from pathlib import Path
_IMPL = Path(__file__).resolve().parent.parent  # implementations/
sys.path.insert(0, str(_IMPL))
from common.exaone_env import openai_compat_kwargs
```

### 4.3 빈 응답 / thinking 채널

EXAONE API 특성: [`PLAYBOOK.md`](../PLAYBOOK.md) §6.3.1, `exaone.llm.ExaoneAPIClient` empty-content 복구.  
서드파티 SDK에서 파싱 실패 시 **우선 cookbook 클라이언트 패턴 링크** 후, 필요 시 thin wrapper.

---

## 5. 라이선스·컴플라이언스

| 항목 | 내용 |
|------|------|
| Cookbook 본문·접착 코드 | [`LICENSE.md`](../LICENSE.md) — BSD-3-Clause-LG AI Research |
| Upstream 5종 (직접 clone) | MIT 또는 Apache-2.0 (각 upstream 원본) |
| **EXAONE 모델/API** | cookbook / upstream 라이선스와 **별개** — LG AI Research 배포·API ToS 준수 |
| browser-use | 라이브러리 MIT; PostHog·`browser-use-sdk`·클라우드는 **선택** — 데모는 로컬 EXAONE only 권장 |
| Hermes / NanoClaw | 메신저·터미널·Docker → **운영 보안** 문서화 (라이선스와 별개) |
| Notices (정본) | [`NOTICE.md`](../NOTICE.md); 요약 [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) |

---

## 6. 디렉터리 구조

```
<cookbook-root>/
├── .gitmodules
├── submodules/
│   ├── hermes-agent/
│   ├── browser-use/
│   ├── nanoclaw/
│   ├── crewai/
│   └── smolagents/
├── implementations/
│   ├── README.md
│   ├── common/
│   │   └── exaone_env.py
│   ├── hermes-agent/
│   │   ├── README.md
│   │   ├── .env.example
│   │   ├── run_cli_demo.sh
│   │   ├── skills/
│   │   └── scripts/          # hermes_glue.py, env.sh, run_hermes.sh
│   ├── browser-use/
│   ├── nanoclaw/
│   ├── crewai/
│   └── smolagents/
└── docs/
    └── implementations.md   # 본 문서
```

**gitignore:** `implementations/**/_out/` (로컬 데모 산출물); `implementations/hermes-agent/.hermes/` (render·secrets).

---

## 7. 레포별 작업 분할 (에이전트 지시용)

각 구현 폴더의 `README.md` 와 아래 표를 **단일 소스**로 삼는다. PR은 `implementations/<repo>/` + 문서만; 권장 pin SHA 변경은 README·이 문서와 함께.

### 7.1 `hermes-agent` — 담당 에이전트 A

| 항목 | 내용 |
|------|------|
| **경로** | `implementations/hermes-agent/` |
| **Wow** | Skills + (선택) CLI 한 턴; Gateway는 Expert opt-in |
| **EXAONE 정본** | `custom_providers` → `custom:exaone/<model>` |
| **시작 파일** | `run_cli_demo.sh` · `scripts/hermes_glue.py` · `scripts/run_hermes.sh` |
| **glue** | `hermes_glue.py` (`check`/`render`/`ping`/`run`); `HERMES_HOME=./.hermes` |
| **상태** | ✅ glue 단순화 — [`README`](../../implementations/hermes-agent/README.md) |
| **의존성** | Hermes `uv`/venv — upstream `submodules/hermes-agent/README` |
| **완료 기준** | `run_cli_demo.sh` exit 0; `run_hermes.sh` REPL; `/model custom:exaone/<EXAONE_MODEL>`; `_out/` trace |

### 7.2 `browser-use` — 담당 에이전트 B

| 항목 | 내용 |
|------|------|
| **경로** | `implementations/browser-use/` |
| **Wow** | 실웹 1태스크 (한국어 결과), allowlist URL |
| **EXAONE 정본** | `ChatOpenAI(base_url=..., api_key=..., model=...)` |
| **시작 파일** | `run_task.py` (스캐폴드 있음) |
| **상태** | ✅ `tasks/example_kr.yaml`; `playwright install` 문서; telemetry off — [`README`](../../implementations/browser-use/README.md) |
| **완료 기준** | `./implementations/uv_run.sh browser-use python run_task.py` 성공 |

### 7.3 `nanoclaw` — 담당 에이전트 C

| 항목 | 내용 |
|------|------|
| **경로** | `implementations/nanoclaw/` |
| **Wow** | Docker 격리 + CLI(또는 Telegram) + EXAONE 한국어 1턴 |
| **EXAONE** | **팀이 하나만 선택:** `/add-opencode` **또** cookbook `proxy/` — README에 정본 1개 |
| **시작 파일** | `config.exaone.example.env` |
| **상태** | ✅ Docker/Node/pnpm — [`README`](../../implementations/nanoclaw/README.md); ✅ `install_prerequisites.sh`; ✅ `run_exaone_turn.py` |
| **완료 기준** | `./implementations/uv_run.sh nanoclaw python run_exaone_turn.py` + fork Docker 경로 문서화 |

### 7.4 `crewai` — 담당 에이전트 D

| 항목 | 내용 |
|------|------|
| **경로** | `implementations/crewai/` |
| **Wow** | 3 role agents (research / write / review) 전부 EXAONE |
| **EXAONE 정본** | `crewai.LLM` + `openai_compat_kwargs()` |
| **상태** | ✅ `run_crew.py`; `tasks/research_brief_ko.md`; `_out/crew_trace.json` — [`README`](../../implementations/crewai/README.md) |
| **완료 기준** | `./implementations/uv_run.sh crewai python run_crew.py` |

### 7.5 `smolagents` — 담당 에이전트 E

| 항목 | 내용 |
|------|------|
| **경로** | `implementations/smolagents/` |
| **Wow** | 짧은 tool loop + calculator 정확도 |
| **EXAONE 정본** | `OpenAIModel(api_base=...)` |
| **시작 파일** | `run_agent.py` (스캐폴드 있음) |
| **상태** | ✅ `eval_smoke.py` (3249×87); requirements 핀 문서 — [`README`](../../implementations/smolagents/README.md) |
| **완료 기준** | `run_agent.py` + `_out/run.json` |

### 7.6 공통·메타 — 담당 에이전트 F (선택)

| 작업 |
|------|
| `LICENSE.md` · `NOTICE.md` · `THIRD_PARTY_NOTICES.md` |
| `docs/README.md` · 루트 `README.md` 에 implementations 링크 |
| CI: cookbook unit tests (upstream clone 불필요). Proof Gallery는 로컬 clone 후 스모크 |
| `implementations/composites.md` — 3종 cross-demo **문서만** (폴더 추가 없음) |

---

## 8. 우선순위·마일스톤

| 단계 | 목표 | 권장 순서 |
|------|------|-----------|
| M0 | upstream clone 가이드 + 본 문서 + `common/exaone_env.py` | ✅ 완료 |
| M1 | **smolagents**, **browser-use** Python E2E | E → B | ✅ |
| M2 | **crewai** 멀티에이전트 | D | ✅ |
| M3 | **hermes-agent** custom provider + skill | A | ✅ glue |
| M4 | **nanoclaw** Docker + EXAONE 경로 확정 | C | ✅ cookbook E2E; fork Docker는 opt-in |
| M5 | 공지·license·CI | F | ✅ CI + `LICENSE.md` / `NOTICE.md` |

---

## 9. 보안·Expert Track (README 필수 문구)

- Submodule upstream 코드를 cookbook에서 **포크 수정하지 않음**.
- Hermes: terminal·gateway·delegation — 기본 데모는 **제한 toolset**; URL allowlist.
- browser-use: **allowlist origin**; 자격증명 페이지 데모 금지.
- NanoClaw: Docker 필수; 실메신저 연동은 Maintainer 문서 + opt-in.
- API 키: `implementations/<repo>/.env` 만; Hermes는 `HERMES_HOME=implementations/hermes-agent/.hermes`(render 시 `.env` 브릿지).

---

## 10. 참고 링크

| 자료 | URL |
|------|-----|
| Hermes providers | https://hermes-agent.nousresearch.com/docs/integrations/providers |
| browser-use models | https://docs.browser-use.com/open-source/supported-models |
| NanoClaw README | `submodules/nanoclaw/README.md` |
| Agent Learning Hub (recipes 참고) | `recipes/README.md` |
| PLAYBOOK | [`PLAYBOOK.md`](../PLAYBOOK.md) |
| llm_ax 노트북 계획 (내부) | `llm_ax_notebook_plan.md` — NB-01~07 ↔ implementations 주제 매핑 참고 |

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-28 | 초안: 5 submodule, 네이밍 규칙, 분할 표, 스캐폴드 (`smolagents/run_agent.py`, `browser-use/run_task.py`) |
| 2026-05-29 | §7 데모 완료 상태 반영 (smolagents, browser-use, crewai, hermes); M1–M3 ✅ |
| 2026-05-28 | §2.1 Submodule 버전 정책 (pin·bump·팀원 주의사항) |

---

**다음 액션 (maintainer):** `implementations/` 접착·문서 유지. Upstream은 유저 clone. 에이전트는 §7 표에서 자신의 repo만 집어 `implementations/<repo>/README.md` 체크리스트를 완료한다.
