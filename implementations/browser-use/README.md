# browser-use + EXAONE

| | |
|--|--|
| **Upstream** | `submodules/browser-use` (직접 clone) → [browser-use/browser-use](https://github.com/browser-use/browser-use) |
| **상태** | 🟢 E2E — `run_task.py` + `tasks/example_kr.yaml` |
| **담당 작업** | [`docs/implementations.md`](../docs/implementations.md) §7.2 |

## Wow 목표

Playwright 기반 **실웹** 작업(폼·SPA·표 추출)을 **EXAONE**이 reasoning 하도록 한 스크립트 재현.

## 한 줄 실행

Cookbook **루트**에서 (`implementations/browser-use/.env` 필요):

```bash
./implementations/uv_run.sh browser-use python run_task.py
```

결과는 `implementations/browser-use/_out/run.json` 에 저장됩니다 (gitignore).

## EXAONE 연동 (정본)

```python
from browser_use import Agent, Browser, ChatOpenAI
from common.exaone_env import openai_compat_kwargs  # PYTHONPATH=.:implementations

kw = openai_compat_kwargs()
llm = ChatOpenAI(
    model=kw["model"],
    base_url=kw["base_url"],
    api_key=kw["api_key"],
    remove_min_items_from_schema=True,
)
browser = Browser(allowed_domains=["https://example.com"])
agent = Agent(task="...", llm=llm, browser=browser, use_thinking=False)
```

- 문서: [ChatOpenAI](https://docs.browser-use.com/open-source/supported-models)
- EXAONE 빈 응답/thinking 이슈: [`PLAYBOOK.md`](../PLAYBOOK.md) §6.3.1 — 기본 `use_thinking=False`

## 태스크 YAML

`tasks/example_kr.yaml` — allowlist + 한국어 태스크. 다른 파일:

```bash
./implementations/uv_run.sh browser-use python run_task.py \
  --task-file tasks/example_kr.yaml
```

| 필드 | 설명 |
|------|------|
| `allowed_domains` | `Browser` URL allowlist (필수 권장) |
| `task` | 자연어 브라우저 과업 |
| `use_vision` | 스크린샷 vision (기본 `false`) |
| `use_thinking` | EXAONE thinking 채널 (기본 `false`) |
| `headless` | 헤드리스 Chromium (기본 `true`) |

## 보안

- **allowlist origin** — YAML `allowed_domains` 로만 허용. allowlist 없이 민감 페이지 데모 금지.
- **자격증명·로그인 페이지** 데모에 사용하지 않음.
- API 키는 `implementations/browser-use/.env` 만 사용.

## 산출물 체크리스트

- [x] `run_task.py` + `tasks/example_kr.yaml` (allowlist URL)
- [x] `playwright install` 절차를 README에 명시
- [x] PostHog/클라우드 SDK **off** 가이드 (로컬 EXAONE only)
- [x] `_out/run.json` (로컬 실행 시 생성)

## 사전 준비

Cookbook **루트**에서 가상환경을 활성화한 뒤:

```bash
# upstream (최초 1회) — 전체 가이드: implementations/README.md
git clone https://github.com/browser-use/browser-use.git submodules/browser-use

cp implementations/browser-use/.env.example implementations/browser-use/.env
uv sync --project implementations/browser-use
playwright install chromium
```

| 항목 | 설명 |
|------|------|
| **Python** | ≥3.11 (browser-use upstream 요구) |
| **browser-use** | `0.13.7` — `pyproject.toml` pin |
| **Playwright** | 최초 1회 `playwright install chromium` 필수 |
| **EXAONE** | `implementations/browser-use/.env` 의 `EXAONE_*` |

### Telemetry / 클라우드 off (로컬 EXAONE only)

`run_task.py` 가 기본으로 아래를 설정합니다.

```bash
export ANONYMIZED_TELEMETRY=false
export BROWSER_USE_CLOUD_SYNC=false
```

PostHog·Browser Use Cloud 는 **선택** 기능입니다. 데모는 로컬 LLM + 로컬 브라우저만 사용합니다.

## 검증 (Phase 4)

```bash
./implementations/uv_run.sh browser-use python scripts/check_env.py
./implementations/uv_run.sh browser-use python run_task.py
```

## 의존성

- `uv sync --project implementations/browser-use`
- Playwright Chromium (`playwright install chromium`)
- `implementations/browser-use/.env` EXAONE_*

## recipes와의 차이

- Track 09: LangChain/LlamaIndex 브릿지
- 여기: **browser-use** Playwright 에이전트 + EXAONE OpenAI-compatible API
