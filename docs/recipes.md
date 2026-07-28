# `recipes/` — Track 00–10 노트북 튜토리얼

**여기는 어떤 곳인가요?**  
Jupyter **노트북**으로 EXAONE 에이전트를 **처음부터 캡스톤까지** 따라 할 수 있게 정리한 폴더입니다.  
학습 경로·체크포인트·산출물 규칙의 **정본**은 [`recipes/README.md`](../recipes/README.md)입니다.

---

## Track 한눈에

| Track | 디렉터리 | 필요 조건 | 요약 |
|-------|----------|-----------|------|
| **00** | `track00_bootstrap/` | API 키 | env, 첫 호출, “에이전트가 필요한가?” |
| **01** | `track01_exaone_foundation/` | API 키 | 대화·한국어·JSON·툴·thinking |
| **02** | `track02_minimum_agent_loop/` | API 키 | `ToolAgent` 최소 루프 |
| **03** | `track03_tools_and_mcp/` | API 키, 네트워크(MCP) | 도구 등록, MCP |
| **04** | `track04_rag_and_knowledge/` | **Postgres + embedding** | pgvector, GraphRAG |
| **05** | `track05_memory_and_long_context/` | API 키 | Ledger, Artifact |
| **06** | `track06_orchestration_multi_agent/` | API 키 | Workflow, LangGraph |
| **07** | `track07_safety_hitl_observability/` | 없음(LLM 선택) | HITL, injection 방어, trace, SLO |
| **08** | `track08_evaluation_m1_m10/` | 없음(합성)·키는 `eval.run`만 | M1–M10, `eval.run`, τ-bench |
| **09** | `track09_framework_bridges/` | 프레임워크별(키는 일부) | LangChain, LlamaIndex, LangGraph, Gradio |
| **10** | `track10_ax_capstones/` | 없음(라이브만 키) | AX 캡스톤 7종 (clone-and-run) |

---

## 이렇게 시작하면 부담이 적어요

1. 루트 [`README.md`](../README.md): venv + `pip install -r requirements.txt` + `pip install -e .` + `cp .env.example .env`  
2. **처음이면** [`track00_bootstrap/00_bootstrap_lab.ipynb`](../recipes/track00_bootstrap/00_bootstrap_lab.ipynb)  
3. **기초 모델 사용** → Track 01 ([`01_exaone_foundation_lab.ipynb`](../recipes/track01_exaone_foundation/01_exaone_foundation_lab.ipynb))  
4. **RAG** → [infrastructure.md](./infrastructure.md) 셋업 후 Track 04  
5. **평가** → Track 08 + `python -m eval.run` ([eval.md](./eval.md))

실습 가이드: [`PLAYBOOK.md`](../PLAYBOOK.md)

---

## 노트북 공통 규칙

- **코드 시작:** `import exaone` → `load_project_env()` → `ROOT = exaone.project_root()` ([`recipes/README.md`](../recipes/README.md))  
- **실행:** 셀을 **위에서 아래로** — 중간 건너뛰면 `NameError`가 납니다  
- **산출물:** 각 트랙 디렉터리 아래 `_out/<MM>/` (예: `track08_…/_out/01/metric_map.json`). `recipes/**/_out/` 은 gitignore — 로컬 경로가 섞일 수 있음  
- **커널:** Jupyter가 프로젝트 `.venv`를 가리키는지 Track 00에서 확인  

---

## 자주 있는 일

| 증상 | 조치 |
|------|------|
| `ModuleNotFoundError` | venv + `requirements.txt` + `pip install -e .`, 커널 = `.venv` |
| MCP/외부 HTTP | Track 03 · [`PLAYBOOK.md` Part 8](../PLAYBOOK.md#part-8) |
| Postgres refused | Track 04 전 [infrastructure.md](./infrastructure.md) step2~4 |

---

## 막히면

- 한 단계 **아래** 트랙으로 내려가 “동작하는 최소 예제”부터 통과 (예: Track 04 막히면 Track 01 재확인)  
- **오늘은 한 노트북만** 목표로 잡아도 됩니다  

각 트랙 `README.md`에 학습 목표·체크리스트·다음 트랙 링크가 있습니다.
