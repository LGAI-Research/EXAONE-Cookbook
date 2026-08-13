# `exaone/` — 핵심 라이브러리

**여기는 어떤 곳인가요?**  
이 저장소의 **“공식에 가깝게 다루는” Python 패키지**입니다. OpenAI 호환 **EXAONE API**로 대화·도구·RAG·메모리·구조화 출력을 묶는 코드가 여기에 모여 있습니다. `recipes/`와 `implementations/`는 이 위에서 **예제**를 쌓는 셈입니다.

---

## 이럴 때 `exaone`을 쓰면 좋아요

- 노트북·서비스 코드에서 **한 가지 스타일**으로 LLM을 부르고 싶을 때  
- **ToolAgent**로 “enrich(도구) → finalize(JSON)” 흐름을 만들 때 (RAG는 `rag.retrieve` tool)  
- 컨텍스트가 길어질 때 **잘라내기·압축** 정책을 코드로 맞추고 싶을 때  
- **Ledger·Artifact**로 대화/도구 흔적을 남기되, 민감한 기본은 팀 정책·`PLAYBOOK`과 함께 쓰고 싶을 때

---

## 모듈을 이렇게 떠올리면 이해가 쉬워요

| 경로 (대략) | 역할 |
|-------------|------|
| `exaone.config` | 루트 `.env` / **`.env.example`** 로드, 모델·컨텍스트·운영 기본값 |
| `exaone.llm` / `exaone.llm.exaone_client` | 채팅 **API 클라이언트** |
| `exaone.agents` | `ToolAgent`, `ToolAgentCatalog`, `ThinkingRouter`, `NextStepPlanner`, rag tools |
| `exaone.context_management` | 토큰 **실행/압축** 파이프라인, 비신뢰 텍스트 sanitize (`input + reserved_new_tokens ≤ max`) |
| `exaone.retrieval` | 벡터/그래프/하이브리드 **검색 전략** |
| `exaone.output` | JSON 추출, 스키마 검증, **구조화 응답** 파이프 |
| `exaone.memory` | Ledger, Artifact 등 **대화/도구 기록** (설정: `CORE_MEMORY_*` 등). 조회 API는 스냅샷 반환, 내부 변경은 `append`/`put`만 |
| `exaone.tools` | 툴 레지스트리, `ToolResult`/`ToolOutcome`, 실패 payload |
| `exaone.integrations` | 참조 구현·CLI용 env 팩토리, Postgres/embedding 연동, exit code |

에이전트 쪽 **시스템 프롬프트는 기본적으로 영어**로 두는 것이 권장됩니다(일관성·토큰·구조화 파싱). 자세한 이유는 `exaone/agents/README.md`에 적혀 있습니다.

---

## 처음 읽을 파일 추천

1. 루트 **`.env.example`** / `exaone/config.py` — 환경 변수와 기본 한도  
2. `exaone/llm/exaone_client.py` — 실제로 어떻게 `chat` 하는지  
3. `exaone/agents/tool_agent.py` — ToolAgent (rag/tool) registry 등록 후 `run()`  

---

## K-EXAONE 2.0 · `preserve_thinking`

K-EXAONE **2.0**은 1.0과 달리 OpenAI 호환 API에 **`preserve_thinking`** 이 추가됩니다. 이전 턴의 `reasoning_content`를 멀티턴 컨텍스트에 **남길지** 결정합니다.

| 워크플로 | `enable_thinking` | `preserve_thinking` |
|----------|-------------------|---------------------|
| 잡담 · 단발 Q&A | `False` | `False` — **지연·토큰 절약** |
| **Agentic** (ToolAgent · 도구 루프) | `True` | **`True` (필수)** — 효과는 **K-EXAONE 2.0+** |

- **`exaone.llm.ExaoneAPIClient`**: `ExaoneGenerateOptions.enable_thinking`만 노출합니다. `preserve_thinking`은 **eval glue**(`eval/exaone_api_kwargs.py`) 또는 `extra_body`로 **명시**합니다.
- **K-EXAONE 1.0**에 `preserve_thinking`을 payload에 넣어도 보통 **무시**되며, Cookbook은 모델 id 추측 없이 설정값을 그대로 보냅니다.

자세한 API 표·환경 변수·eval 연동은 [`k_exaone_2.md`](./k_exaone_2.md)를 참고하세요.

---

## 막히면

- **import 오류** → 루트에서 `pip install -r requirements.txt && pip install -e .` 후 Jupyter 커널이 같은 `.venv` 인지 확인 ([`recipes/README.md`](../recipes/README.md))  
- **404/401** → `EXAONE_BASE_URL` 끝에 `/v1`이 맞는지, 키가 맞는지  
- **긴 맥락·메모리** → `exaone.config`의 컨텍스트·`CORE_MEMORY_*`와 [PLAYBOOK.md](../PLAYBOOK.md) Part 6~8  

`exaone`은 **재사용 가능한 부품 상자**로 생각하시면 됩니다. 레시피 한 편씩 뜯어보며 필요한 모듈만 가져다 써도 충분합니다.
