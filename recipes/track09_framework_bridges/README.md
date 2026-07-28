# Track 09 — Framework Bridges (선택)

> **EXAONE을 다른 생태계 안에서 쓰는 법** — LangChain, LlamaIndex, LangGraph, Gradio를 *선택적 통합 패턴*으로 다룹니다.
> Agent Learning Hub 매핑: **Stage 3** (다른 하니스가 같은 문제를 어떻게 푸는지).

캡스톤(Track 10)은 **EXAONE 라이브러리 단독** 구현을 권장합니다. 이 트랙은 “조직이 이미 쓰는 프레임워크에 EXAONE을 연결할 때”의 연결 패턴만 익힙니다.

---

## 학습 목표

- [ ] `ChatOpenAI(base_url=...)` 로 EXAONE을 LangChain LCEL·tool calling에 연결한다.
- [ ] `OpenAICompatLLM` 으로 OpenAI 호환 형 model id 를 LlamaIndex QueryEngine·ReAct에 붙인다.
- [ ] LangGraph `StateGraph` 로 Track 06 의 planner→executor→critic 흐름을 *그래프*로 표현하고 EXAONE-native 와 비교한다.
- [ ] `exaone.llm.ExaoneAPIClient.chat_stream` 을 Gradio UI 스크립트로 export 한다.

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()
# (en) Optional integration submodules — register once in Setup for dotted access.
# (kr) 선택 integration 서브모듈 — Setup 에서 한 번 import 하면 점 접근이 가능하다.
import exaone.integrations.llamaindex_openai_compat

client = exaone.llm.ExaoneAPIClient(base_url=..., model=..., api_key=...)
llm = exaone.integrations.llamaindex_openai_compat.OpenAICompatLLM(model=..., api_base=..., api_key=...)
```

LangChain·LlamaIndex·LangGraph·Gradio API 는 **외부 패키지**이므로 `from langchain_openai import ChatOpenAI` 등은 허용됩니다. `exaone.*` 만 facade 규칙(`import exaone` + 점 접근)을 따릅니다.

전체 규칙: [`recipes/README.md` — 모든 노트북 공통 첫 셀](../README.md#모든-노트북-공통-첫-셀).

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`09_framework_bridges_lab.ipynb`](./09_framework_bridges_lab.ipynb) | Session 1~4 — LangChain · LlamaIndex · LangGraph · Gradio | `_out/langchain_vs_exaone.json`, `_out/react_trace.json`, `_out/langgraph_vs_exaone.json`, `_out/chat_app.py`, `_out/app_spec.json` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `langchain_vs_exaone.json` — LCEL 번역·RAG 인용 출처·도구 호출 트레이스 (**키 필요**; 지연 ms 는 동일 엔드포인트라 noise).
- [ ] `react_trace.json` — QueryEngine 검색 노드(유사도 점수) + ReAct 1턴 (**키 필요**; QueryEngine·ReAct 모두 키가 있어야 실행, 임베딩 최초 1회 다운로드).
- [ ] `langgraph_vs_exaone.json` — planner/executor/critic 노드 trace + EXAONE-native 단계 방문수 비교 (**키 없이**, LangGraph 설치 시).
- [ ] `chat_app.py` + `app_spec.json` — AST 파싱 통과, 터미널에서 로컬 UI 실행 가능 (**키 없이**; 스트리밍 smoke 만 키 필요).

---

## 선수

- **Track 04** — RAG 시나리오·매뉴얼 스니펫 (`../track04_rag_and_knowledge/data/`)
- **Track 06** — planner→executor→critic (Session 3 비교용)
- **Track 02** — 스트리밍 개념 (Session 4)

## 추가 패키지

루트 `requirements.txt` 에 포함: `langchain*`, `llama-index*`, `langgraph`, `gradio`. 별도 `pip install` 없이 Track 00 venv 를 쓰세요. 단, **Session 2 는 최초 1회 한국어 임베딩 모델(`intfloat/multilingual-e5-small`, ~470MB)을 HuggingFace 에서 내려받습니다**(이후 캐시).

## 다음 트랙

- **Track 10 캡스톤** — EXAONE-native 하니스로 출시 (09 는 참고만)
- **Track 08** — 프레임워크 브리지 전에 평가 체계를 먼저 갖추는 것을 권장

---

## 문제 해결

- LangChain `ChatOpenAI` SSL 오류 → `.env` 의 `DISABLE_SSL_VERIFY=1` 또는 `SSL_CERT_FILE` (Track 00 참고).
- LlamaIndex `ValueError: model ... not found` → `OpenAICompatLLM` 사용 여부 확인 (Session 2 Setup).
- LangGraph import 실패 → venv 에 `langgraph>=0.2` 설치 후 커널 재시작.
- Gradio `launch()` 가 노트북 실행을 멈춤 → Deliverable 셀은 *스크립트 export* 만 하고, 터미널에서 `python _out/chat_app.py` 실행.
