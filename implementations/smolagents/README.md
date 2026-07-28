# smolagents + EXAONE

| | |
|--|--|
| **Upstream** | `submodules/smolagents` (직접 clone) → [huggingface/smolagents](https://github.com/huggingface/smolagents) |
| **상태** | 🟢 E2E — `run_agent.py` + `eval_smoke.py` |
| **담당 작업** | [`docs/implementations.md`](../docs/implementations.md) §7.5 |

## Wow 목표

HF **smolagents** tool-calling 루프가 **EXAONE** `OpenAIModel`로 돌아가며, `calculator` 도구로 **3249×87 = 282663** 을 맞추는 **짧은** 스크립트 (~110줄).

## 한 줄 실행

Cookbook **루트**에서 (`implementations/smolagents/.env` 필요):

```bash
./implementations/uv_run.sh smolagents python run_agent.py
```

결과는 `implementations/smolagents/_out/run.json` 에 저장됩니다 (gitignore).

## EXAONE 연동 (정본)

```python
from smolagents import OpenAIModel, ToolCallingAgent, tool
from common.exaone_env import openai_compat_kwargs  # PYTHONPATH=.:implementations

kw = openai_compat_kwargs()
model = OpenAIModel(
    model_id=kw["model"],
    api_base=kw["base_url"],
    api_key=kw["api_key"],
    temperature=0,
)
agent = ToolCallingAgent(tools=[calculator], model=model, max_steps=5)
run_result = agent.run("3249 * 87은? calculator 도구를 사용해 계산해줘.", return_full_result=True)
```

- upstream: [smolagents OpenAIModel](https://github.com/huggingface/smolagents)
- EXAONE 빈 응답/thinking 이슈: [`PLAYBOOK.md`](../PLAYBOOK.md) §6.3.1

## 산출물 체크리스트

- [x] `run_agent.py` + `calculator` @tool
- [x] `eval_smoke.py` — 3249×87 calculator 호출·정답 검증
- [x] `_out/run.json` (로컬 실행 시 생성)

## 사전 준비

Cookbook **루트**에서:

```bash
# upstream (최초 1회) — 전체 가이드: implementations/README.md
git clone https://github.com/huggingface/smolagents.git submodules/smolagents

cp implementations/smolagents/.env.example implementations/smolagents/.env
# EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL
uv sync --project implementations/smolagents
```

| 항목 | 설명 |
|------|------|
| **Python** | ≥3.10 (smolagents upstream 요구) |
| **uv** | 각 implementation 전용 `.venv` (cookbook `.venv` 와 분리) |
| **smolagents** | `1.25.0` — `pyproject.toml` pin |
| **EXAONE** | `implementations/smolagents/.env` 의 `EXAONE_*` |

회사망 TLS 이슈는 **implementation `.env`** 의 `DISABLE_SSL_VERIFY` / `REQUESTS_CA_BUNDLE` — [`PLAYBOOK.md`](../../PLAYBOOK.md) Part 8.

## 검증

```bash
# import + EXAONE env (LLM 호출 없음)
./implementations/uv_run.sh smolagents python scripts/check_env.py

# E2E (EXAONE API 필요)
./implementations/uv_run.sh smolagents python run_agent.py

# 3249×87 스모크 (기존 _out/run.json 검증)
./implementations/uv_run.sh smolagents python eval_smoke.py

# E2E 실행 후 검증 한 번에
./implementations/uv_run.sh smolagents python eval_smoke.py --run
```

`run.json` 성공 조건: `calculator_used=true`, `answer_ok=true`, `success=true`, `expected=282663`.

## 의존성

- `uv sync --project implementations/smolagents`
- `implementations/smolagents/.env` EXAONE_*

## recipes와의 차이

- Track 02: `exaone.agents.ToolAgent` 네이티브 (ledger, JSON repair, empty-content 복구)
- 여기: **외부 최소 tool-calling 라이브러리** + EXAONE — “HF smolagents도 EXAONE으로 된다” wow
