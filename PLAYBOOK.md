# EXAONE Playbook — 노트북 중심 실무·학습 가이드

이 문서는 **레시피(`recipes/`) 안의 Jupyter 노트북을 처음부터 끝까지** 따라갈 수 있도록 쓴 안내서입니다.  
코드·아키텍처 용어는 최소로 두고, “**지금 이 노트북에서 무엇을 하면 되는지**”, “**막혔을 때 어디를 보면 되는지**”를 먼저 설명합니다.

**학습 경로의 정본:** [`recipes/README.md`](recipes/README.md) (Track 00–10).  
**평가·벤치마크:** [`docs/eval.md`](docs/eval.md) · `python -m eval.run`

- **빨리 실행만 해보고 싶다** → [Part 1](#part-1) → [Track 00–01](#part-2)  
- **RAG·도커·DB까지** → [Track 04](#part-4-rag) + [Part 5](#part-5)  
- **평가(M1–M10)** → [Track 08](#part-4-eval) · `eval.run`  
- **운영·SLO·로그** → [Part 7](#part-7)  
- **보안·컴플라이언스** → [Part 8](#part-8)

---

<a id="part-1"></a>

## Part 1 — 첫 실행 전 체크리스트

한 번만 순서대로 점검해 보세요.

1. **저장소를 받았다**  
   `git clone` 후 프로젝트 **루트**에서 작업합니다. 노트북은 루트의 `.env`를 찾습니다.

2. **Python 가상환경(권장)**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **`.env` 파일**  
   ```bash
   cp .env.example .env
   ```  
   **반드시** 채울 항목:
   - `EXAONE_API_KEY`
   - `EXAONE_BASE_URL` (OpenAI 호환, `/v1`로 끝남)
   - `EXAONE_MODEL` (배포 모델 ID)

4. **Jupyter**  
   ```bash
   pip install jupyter ipykernel
   jupyter notebook
   ```  
   VS Code / Cursor에서는 **위 venv를 커널**로 선택하세요. `ModuleNotFoundError`는 대부분 **다른 Python** 커널 때문입니다.

5. **노트북 실행 순서**  
   셀은 **위에서 아래로** 실행합니다. Track 00 [`00_bootstrap_lab.ipynb`](recipes/track00_bootstrap/00_bootstrap_lab.ipynb) Session 1 에서 env·커널을 먼저 확인하는 것을 권장합니다.

이제 [Part 2](#part-2)로 가면 됩니다.

---

## 추천 학습 경로 (한눈에)

```
[준비]  Track 00 Bootstrap          →  Part 2
           ↓
[기초]  Track 01 EXAONE Foundation  →  Part 2
           ↓
[에이전트] Track 02 Minimum Agent Loop
           Track 03 Tools & MCP
           Track 04 RAG & Knowledge    →  Part 5 (인프라)
           Track 05 Memory & Long Context
           ↓
[운영]  Track 06 Orchestration
        Track 07 Safety / HITL / Observability
        Track 08 Evaluation (M1–M10)  →  Part 4 (eval)
           ↓
[출구]  Track 09 Framework Bridges (선택)
        Track 10 AX Capstones
```

**느리게 가도 괜찮습니다.** 한 트랙을 여러 날에 나눠도 되고, 표는 “다음에 뭘 열지” 정할 때만 쓰면 됩니다.

---

<a id="part-2"></a>

## Part 2 — Track 00 & 01 (입문)

**위치:** `recipes/track00_bootstrap/`, `recipes/track01_exaone_foundation/`  
**필요한 것:** 유효한 `EXAONE_*`와 `.env`. DB·도커 없음.  
**목표:** 환경 확인 → 첫 API 호출 → 대화·JSON·툴·한국어·thinking 라우터 기본기.

| 트랙 | 노트북 | 하는 일 |
|------|--------|---------|
| 00 | [`00_bootstrap_lab`](recipes/track00_bootstrap/00_bootstrap_lab.ipynb) | **Session 1** 환경 점검(venv·`.env`·커널·SSL) · **Session 2** 첫 API(기준/thinking/streaming) |
| 01 | [`01_exaone_foundation_lab`](recipes/track01_exaone_foundation/01_exaone_foundation_lab.ipynb) | **Session 1** 대화·스트리밍 · **2** 한국어 · **3** 구조화 출력 · **4** 함수 호출 · **5** ThinkingRouter |

각 노트북은 `Session N` → `Session N-M` (가이드) → 코드 → **출력 해석** 순으로 구성됩니다.

**막혔을 때:** 401/403 → 키·URL·모델. SSL → [Part 6.2](#part-6-2) · [Part 8](#part-8).

---

<a id="part-3"></a>

## Part 3 — Track 02–07 (에이전트·운영)

**위치:** `recipes/track02_*` … `track07_*`  
**목표:** `ToolAgent` 루프, MCP, RAG, 메모리, 오케스트레이션, HITL·관측성.

| 트랙 | 노트북 | 핵심 |
|------|--------|------|
| 02 | [`02a_minimum_agent_loop_lab`](recipes/track02_minimum_agent_loop/02a_minimum_agent_loop_lab.ipynb) (+ 심화 [`02b_harness_anatomy`](recipes/track02_minimum_agent_loop/02b_harness_anatomy.ipynb)) | 손코딩 루프 · `ToolAgent` · SSE 스트리밍 · harness 해부 |
| 03 | [`03_tools_and_mcp_lab`](recipes/track03_tools_and_mcp/03_tools_and_mcp_lab.ipynb) | `ToolRegistry` · 안전 도구 · MCP |
| 04 | [`04a_rag_and_knowledge_lab`](recipes/track04_rag_and_knowledge/04a_rag_and_knowledge_lab.ipynb) (+ 심화 [`04b_pgvector_and_strategies`](recipes/track04_rag_and_knowledge/04b_pgvector_and_strategies.ipynb)) | 임베딩 · RAG · 실패 모드 (**Postgres·임베딩** → [Part 5](#part-5)) |
| 05 | [`05_memory_and_long_context_lab`](recipes/track05_memory_and_long_context/05_memory_and_long_context_lab.ipynb) | Ledger · Artifact · 컨텍스트 압축 |
| 06 | [`06_orchestration_lab`](recipes/track06_orchestration_multi_agent/06_orchestration_lab.ipynb) | planner·executor·critic · 라우터 핸드오프 |
| 07 | [`07a_safety_and_observability_lab`](recipes/track07_safety_hitl_observability/07a_safety_and_observability_lab.ipynb) (+ 심화 [`07b_slo_production_defaults`](recipes/track07_safety_hitl_observability/07b_slo_production_defaults.ipynb)) | HITL · prompt injection · 관측 trace · SLO |
| 08 | [`08a_evaluation_lab`](recipes/track08_evaluation_m1_m10/08a_evaluation_lab.ipynb) (+ 심화 [`08b_my_golden_set`](recipes/track08_evaluation_m1_m10/08b_my_golden_set.ipynb)) | M1–M10 지표 · 골든셋 회귀 |
| 09 | [`09_framework_bridges_lab`](recipes/track09_framework_bridges/09_framework_bridges_lab.ipynb) (선택) | LangChain · LlamaIndex · LangGraph · Gradio |
| 10 | [`10_01` … `10_07`](recipes/track10_ax_capstones/) | AX 캡스톤 (트랙별 `10_0x_capstone_*.ipynb`) |

각 트랙 `README.md`에 선수·체크포인트·산출물(`_out/…`, 트랙 디렉터리 기준)이 있습니다.

---

<a id="part-4-rag"></a>

### Part 4 — RAG 쪽만 먼저 (Track 04)

`track04_rag_and_knowledge/`를 열기 전에 [Part 5](#part-5)를 읽지 않으면 “connection refused”, “테이블 없음”으로 막히기 쉽습니다.

---

<a id="part-4-eval"></a>

### Part 4 — 평가 (Track 08)

**위치:** `recipes/track08_evaluation_m1_m10/`  
**CLI:** `python -m eval.run` (기본 dataset = BFCL 4종)

```bash
python -m eval.run --limit 25 --pass-k-trials 2 --sleep 3
```

- 지표 정의: [`eval/README.md`](eval/README.md), [`docs/eval.md`](docs/eval.md)  
- [`08a_evaluation_lab`](recipes/track08_evaluation_m1_m10/08a_evaluation_lab.ipynb) 은 **API 없이** 합성 trial로 대부분 통과 가능. `eval.run`/τ-bench E2E 셀만 `EXAONE_API_KEY` 필요.

---

<a id="part-5"></a>

## Part 5 — 노트북 밖: RAG 인프라

RAG·Track 04는 **Postgres(pgvector) + 임베딩 서버**가 필요합니다.

1. 상위 [`README.md`](README.md) “인프라 셋업” 절  
2. `infrastructure/setup`: `step1` → `step2`(Docker) → `step3` / `step4`  
3. `.env`의 `POSTGRES_*`, `EMBEDDING_*`가 로컬과 일치하는지 확인

**자주 겪는 일:** 노트북만 열었는데 안 된다 → DB/임베딩 미기동 또는 `PGVECTOR_TABLE_NAME` 불일치. [부록: 트러블슈팅](#appendix-troubleshoot).

---

<a id="part-6"></a>

## Part 6 — 설계·환경 (노트북 후반에 읽어도 됨)

<a id="part-6-1"></a>

### 6.1 아키텍처를 고를 때

- **문서/DB 검색 + 근거** → `ToolAgent` (rag)  
- **API·함수만** → `ToolAgent` + `ToolRegistry`  
- **여러 단계 워크플로** → `WorkflowAgent` 또는 LangGraph(Track 06)  
- **MCP·웹 검색** → Track 03 레퍼런스. 운영에서는 allowlist·레이트리밋 정책 필요 ([Part 8](#part-8))

<a id="part-6-2"></a>

### 6.2 환경 변수 한눈에 (자세한 건 `.env.example`)

| 변수 | 대략 이런 때 |
|------|----------------|
| `EXAONE_API_KEY` | 항상 (노트북·eval·reference) |
| `EXAONE_BASE_URL` / `EXAONE_MODEL` | 발급처와 쌍이 맞아야 함 |
| `EXAONE_API_EXTRA_HEADERS` | 벤더별 추가 HTTP 헤더(JSON) |
| `FRIENDLI_TEAM_ID` | Friendli Serverless 팀 헤더 (legacy; eval naive) |
| `DISABLE_SSL_VERIFY` | 회사망 SSL만 꼬일 때 (보안 trade-off) |
| `CORE_CONTEXT_LENGTH_*` | 긴 대화·툴 결과 컨텍스트 |
| `POSTGRES_*` / `EMBEDDING_*` | RAG, setup 스크립트 |

<a id="part-6-3"></a>

### 6.3 실패 시나리오 요약

| 증상 | 가능 원인 | 할 일(요약) |
|------|-----------|-------------|
| 화면이 완전히 비음 | 빈 200, 토큰/정책 | `ExaoneAPIClient` thinking off → nudge 복구 |
| thinking만 보임 | reasoning-only 응답 | reasoning을 content에 합치지 않음 → [6.3.1](#part-6-3-1) |
| JSON 파싱 실패 | 마크다운만 반환 | `StructuredOutputPipeline` · finalize |
| 컨텍스트 초과 | 토큰 상한 | 압축, `CORE_*` env |
| RAG 빈 근거 | 인덱스·질의 불일치 | preflight, 테이블명, step3 |
| DB/embedding refused | 서비스 미기동 | Docker, `.env` host/port |
| 5xx / timeout | 장애·부하 | 전송 계층 재시도 ([Part 7.3](#part-7-3)) |

<a id="part-6-3-1"></a>

#### 6.3.1 빈 `content` / `reasoning` 채널

`enable_thinking=True`일 때 API는 **reasoning**과 **content** 채널을 분리합니다. 레포 복구 순서:

```
1차 호출 → content 비었거나 reasoning-only?
2차: enable_thinking=False 재호출
3차: EMPTY_CONTENT_NUDGE 추가 후 재호출
→ ToolAgent finalize (thinking off + response_format)
```

| 계층 | 역할 |
|------|------|
| `exaone.llm.response_quality` | empty / reasoning-only 판별 |
| `ExaoneAPIClient.chat` | empty-200 복구 |
| `BaseAgent.request_final_turn` | 루프 종료 후 JSON·빈 content 보정 |

로그 키: `llm.empty_content`, `llm.reasoning_only`, `llm.empty_retry_success`.

### 6.4 관련 코드

- `exaone.observability.fields` — 로그 키  
- `exaone.observability.production_defaults` — 동시성·토큰 권장  
- `exaone.observability.SLOSpec` — SLO를 코드로  
- `.env.example` — `CORE_*`, `MCP_*`, setup 키

---

<a id="part-7"></a>

## Part 7 — 운영 (SLO·로그·비용)

**언제:** 로컬 노트북이 아니라 **서비스/스테이징**에 올릴 때.

### 7.1 SLO 표 — 팀이 숫자를 채움

| 측정 | 설명 | 예시(참고) |
|------|------|------------|
| 가용성 | API/서비스 | 99.9% / 월 |
| 오류율 | 5xx + 정의한 클라이언트 오류 | < 0.1% / 일 |
| p95 지연 | E2E 또는 LLM만 | 팀 정의 |
| 구조화 출력 성공률 | golden / 샘플 | > 95% |
| RAG 0-hit 비율 | 검색 0건 | 허용치 정의 |

### 7.2 로그·트레이싱

- **request_id**로 LLM·도구·검색 로그 연결  
- 에이전트: 종류, 턴 수, 지연, thinking 여부  
- LLM 품질: `llm.empty_content`, `llm.reasoning_only`, `llm.empty_retry_success`  
- PII: 원문 전체 대신 길이·해시·ID ([Part 8](#part-8))

<a id="part-7-3"></a>

### 7.3 비용·쿼터

- **토큰**: `production_defaults`의 `max_new_tokens` 참고  
- **동시 요청**: 워커당 in-flight 상한  
- **eval 배치**: `--sleep`으로 serverless 429 완화  
- **재시도**: 5xx·연결 vs 빈 200은 별개 ([6.3.1](#part-6-3-1))

---

<a id="part-8"></a>

## Part 8 — 보안·컴플라이언스 (요약)

법률·내부 규정의 완전한 설명은 이 문서 범위가 아닙니다. 팀·법무와 합의 후 플레이스홀더를 채우세요.

### 8.1 시크릿

- **하지 말 것:** API 키, `.env` 전체를 Git·슬랙·스크린샷에 노출  
- **권장:** 비밀 저장소·환경 변수만. 예시는 `EXAONE_API_KEY=REDACTED`  
- 노출 시 **즉시 키 회전**

### 8.2 로그·PII

- 사용자 원문·툴 인자 전체를 로그에 넣지 말 것  
- 운영 로그 vs 디버그 덤프 분리

### 8.3 MCP·외부 HTTP

Track 03 `mcp_demo`: allowlist, 레이트리밋, ToS를 팀 정책으로 정의. 레시피는 **학습용** — 프로덕션 트래픽 전에 정책 표를 채우세요.

---

<a id="appendix-env"></a>

## 부록: 환경 변수

- **필수(대부분):** `EXAONE_API_KEY`, `EXAONE_BASE_URL`, `EXAONE_MODEL` — [`.env.example`](.env.example)  
- **RAG:** `POSTGRES_*`, `EMBEDDING_*` — 인프라 기동 후  
- **SSL:** `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` 우선, 최후 `DISABLE_SSL_VERIFY`  
- **exaone core:** `CORE_*` — `exaone.config` getter  
- **eval:** `python -m eval.run` — [`docs/eval.md`](docs/eval.md)

---

<a id="appendix-troubleshoot"></a>

## 부록: 자주 나는 오류

1. **`ModuleNotFoundError`** → venv + `pip install -r requirements.txt` + `pip install -e .` + Jupyter 커널 (`.venv` 와 동일 Python)  
2. **401 / 403** → `.env` 키·URL·모델  
3. **SSL** → [Part 6.2](#part-6-2), 기업 CA 번들  
4. **Postgres/embedding refused** → `infrastructure/setup`, `docker ps`  
5. **RAG 빈 검색** → step3 인덱싱, `PGVECTOR_TABLE_NAME`  
6. **빈 화면 / thinking만 / JSON 실패** → [6.3](#part-6-3) · [6.3.1](#part-6-3-1)  
7. **`eval.run_all` not found** → `python -m eval.run` 사용 (`run_all` 제거됨)

---

**마지막으로:** 고정 순서는 없습니다. **첫날: Part 1 + Track 00–01**만 해도 충분히 잘 따라온 것입니다. 막힌 셀·에러 메시지를 이슈에 남기면 다음 기여자에게 도움이 됩니다.
