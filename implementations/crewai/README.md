# crewai + EXAONE

| | |
|--|--|
| **Upstream** | `submodules/crewai` (직접 clone) → [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) |
| **권장 pin** | `2148c7e` (2026-05-28) |
| **Pip (verified)** | `crewai` 0.203.x — see `requirements-crewai.txt` |
| **상태** | ✅ E2E — `run_crew.py` |

## Wow 목표

Researcher / Writer / Reviewer **역할 분리** 크루가 전부 **EXAONE** 백본으로 한 번에 돌아가는 최소 예제.

## EXAONE 연동 (정본)

CrewAI `LLM`은 LiteLLM 경로로 OpenAI 호환 API를 호출한다. Cookbook glue는 `exaone_llm.build_exaone_llm()` 에서 다음을 고정한다.

| 항목 | 값 |
|------|-----|
| 모델 문자열 | `openai/<EXAONE_MODEL>` |
| 엔드포인트 | `openai_compat_kwargs()` → `base_url`, `api_key` |
| Thinking | `extra_body.chat_template_kwargs.enable_thinking = False` (빈 `content` / reasoning-only 방지) |
| TLS | `DISABLE_SSL_VERIFY=1` 시 LiteLLM `ssl_verify=False` (`exaone.config`와 동일) |

자세한 복구 순서: [`PLAYBOOK.md`](../../PLAYBOOK.md) §6.3.1.

## recipes와의 차이

| | Track 06 (`recipes/`) | 여기 (`implementations/crewai/`) |
|--|----------------------|----------------------------------|
| 프레임워크 | `exaone.agents` / (선택) LangGraph | **CrewAI** |
| 멀티에이전트 | WorkflowAgent | Role-based Crew |

## 빠른 시작

```bash
cd <cookbook-root>
cp implementations/crewai/.env.example implementations/crewai/.env
uv sync --project implementations/crewai

# Phase 0 — LLM 1턴 스파이크
./implementations/uv_run.sh crewai python spike_llm.py

# Phase 1 — 3-agent crew (Researcher → Writer → Reviewer)
./implementations/uv_run.sh crewai python run_crew.py

# API 없이 구성만 검증
./implementations/uv_run.sh crewai python run_crew.py --dry-run
```

## 산출물

| 경로 | 설명 |
|------|------|
| `_out/spike_llm.json` | Phase 0 단일 턴 결과 |
| `_out/crew_trace.json` | Phase 1 크루 최종 출력·태스크별 preview |

`_out/` 은 gitignore — 로컬에서만 생성된다.

## 산출물 체크리스트

- [x] `exaone_llm.py` — EXAONE → `crewai.LLM` 빌더
- [x] `spike_llm.py` — 1턴 스파이크
- [x] `run_crew.py` — 3 agents, 3 sequential tasks
- [x] `tasks/research_brief_ko.md` 샘플 입력
- [x] `_out/crew_trace.json` (실행 시)

## 의존성

- `implementations/crewai/.env`: `EXAONE_API_KEY`, `EXAONE_BASE_URL`, `EXAONE_MODEL`
- `uv sync --project implementations/crewai`
- Upstream clone (참고용): `git clone https://github.com/crewAIInc/crewAI.git submodules/crewai` — 가이드: [`../README.md`](../README.md)

## 트러블슈팅

| 증상 | 조치 |
|------|------|
| `Connection error` / SSL | `implementations/crewai/.env`에 `DISABLE_SSL_VERIFY=1` 또는 `REQUESTS_CA_BUNDLE` |
| `NoneType` … `choices` | thinking 채널만 반환 — `exaone_llm.py`의 `enable_thinking: False` 확인 |
| 실행 후 traces 프롬프트 | `run_crew.py`가 `CREWAI_TRACING_ENABLED=false` 설정 — 여전히 뜨면 `CREWAI_TESTING=true` 확인 |
| `ModuleNotFoundError: crewai` | `uv sync --project implementations/crewai` |

## 인수인계

전체 Proof Gallery 설계: [`docs/implementations.md`](../../docs/implementations.md) §7.4.
