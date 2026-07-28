# Track 04 — RAG & Knowledge

> **근거 있는 답**을 만드는 데이터 파이프라인 한 바퀴: 임베딩 → pgvector 인덱싱 → 검색 전략 → RAG ToolAgent.
> Agent Learning Hub 매핑: **Stage 2** (RAG 축).

---

## 학습 목표

- [ ] `exaone.integrations.embedding` 으로 임베딩 서버를 붙이고 코사인 유사도·클러스터링을 본다.
- [ ] `infrastructure/setup` step1~4 와 `exaone.integrations.postgres` 로 pgvector 인덱스 상태를 점검한다.
- [ ] `exaone.retrieval` 의 vector / graph / hybrid 전략을 같은 질의로 비교한다.
- [ ] `ToolAgent(retrieval_strategy=...)` + `DEFAULT_SYSTEM_PROMPT_RAG` 로 인용 포함 QA를 만든다.
- [ ] 빈 검색·과도한 컨텍스트·중복 청크 등 실패 모드와 `exaone.context_management` 복구 패턴을 본다.

---

## 코드 시작 패턴 (facade)

RAG 트랙도 Setup 셀은 동일하게 `import exaone` 한 줄입니다. 인프라·검색은 점 접근으로 이어집니다.

```python
import exaone

exaone.load_project_env()
# (en) Heavy integration submodules are not re-exported from exaone.integrations — import them once in Setup.
# (kr) 무거운 integration 서브모듈은 exaone.integrations 에서 re-export 되지 않으므로 Setup 에서 한 번 import 한다.
import exaone.integrations.embedding
import exaone.integrations.postgres

embedder = exaone.integrations.embedding.build_embedder_from_env()
strategy = exaone.retrieval.VectorRetrievalStrategy(embed_fn=..., search_fn=...)
registry = exaone.agents.build_rag_tool_registry(strategy)
agent = exaone.agents.ToolAgent(tool_registry=registry, ...)
```

모든 코드 셀은 `from exaone.* import ...` 없이 위 facade 규칙을 따릅니다. `exaone.integrations.*` 는 Setup 셀에서 `import exaone.integrations.<name>` 한 줄로 등록한 뒤 점 접근합니다. [`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade).

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`04a_rag_and_knowledge_lab.ipynb`](./04a_rag_and_knowledge_lab.ipynb) | Session 1~5 — 임베딩 · in-memory RAG · 실패 모드 복구 | `_out/cluster_report.json`, `_out/manual_qa.json`, `_out/failure_recovery.json` |
| [`04b_pgvector_and_strategies.ipynb`](./04b_pgvector_and_strategies.ipynb) | **심화** pgvector 인덱스 · vector/graph/hybrid 검색 비교 | `_out/index_stats.json`, `_out/strategy_compare.json` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `cluster_report.json` — 임베딩 서버 없이도 개념 셀 통과, 서버 있으면 FAQ 클러스터 저장.
- [ ] `manual_qa.json` — 조직 정책 매뉴얼(샘플) 5질의 QA + `sources` 필드.
- [ ] `failure_recovery.json` — 실패 케이스 5종 각각 pass.
- [ ] (심화) `index_stats.json`, `strategy_compare.json` — Postgres·검색 전략 비교.

---

## 선수

- **Track 01** — API 호출, 함수 호출 개념
- **Track 02~03** — `ToolAgent`, `ToolRegistry`

### 인프라 선수 조건 (심화 `04b_pgvector_and_strategies`)

| 항목 | 버전·용도 | 확인 |
|------|-----------|------|
| **Docker** | Postgres(pgvector) + embedding HTTP (`step2_docker.sh`) | `docker compose ps` |
| **Python deps** | `spacy`, `llama-index`, `psycopg` — 루트 `requirements.txt` | `pip install -r requirements.txt` |
| **spaCy 모델** | `en_core_web_sm` — step4 graph / NER (`infrastructure/ingestion/spacy_model.py`) | setup README |
| **디스크** | MS MARCO ingest — `.env` `STEP3_MAX_CONTEXTS` 로 데모 규모 조절 | 기본 5000 passages |
| **`.env`** | `POSTGRES_*`, `EMBEDDING_*`, `PGVECTOR_*` | [`infrastructure/setup/README.md`](../../infrastructure/setup/README.md) |

lab Session 1 은 임베딩 서버만 있으면 동작합니다. Postgres·Docker 없이도 **개념 셀**은 통과할 수 있습니다.

## 인프라 (심화 이후)

```bash
cd infrastructure/setup
./step1_downloads.sh
./step2_docker.sh
./step3_build_rag.sh
./step4_build_graph.sh
```

`.env` 의 `POSTGRES_*`, `EMBEDDING_*`, `PGVECTOR_*` — [`infrastructure/setup/README.md`](../../infrastructure/setup/README.md) 참고.

## 다음 트랙

- **Track 05 — Memory**: RAG 컨텍스트와 대화 압축을 함께 다룸
- **Track 08 — Evaluation**: M9 faithfulness 로 RAG 인용 품질 측정
- **Track 10 — Capstone `10_01`**: lab RAG QA 가 조직 KB QA 베이스라인

---

## 문제 해결

- `postgres_available: False` / 호스트 포트 충돌(다른 Postgres 가 기본 포트 점유) → `.env` 의 `POSTGRES_HOST_PORT`·`POSTGRES_PORT` 를 빈 포트로(둘 같은 값) 맞춤. step 스크립트는 venv 활성화 필요. 상세: [`infrastructure/setup/README.md`](../../infrastructure/setup/README.md) 트러블슈팅.
- Embedding 연결 실패 → `step2_docker.sh`, `.env` 의 `EMBEDDING_BASE_URL` 확인.
- 클러스터링 → (선택) `pip install scikit-learn`.
- Vector 테이블 없음 → `step3_build_rag.sh`, `PGVECTOR_TABLE_NAME` / `data_embeddings` 후보 확인.
- Graph 테이블 없음 → `step4_build_graph.sh`.
- step3 graph 실패 (spaCy `E050`) → `python -m infrastructure.ingestion.spacy_model` (step3 shell preflight).
- RAG 답변 JSON 파싱 실패 → `exaone.output.StructuredOutputPipeline` / `DEFAULT_SYSTEM_PROMPT_RAG` 그대로 사용했는지 확인.
