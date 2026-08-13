# eval/ — K-EXAONE Agentic Harness Benchmark

`exaone/` 하네스가 **naive OpenAI-compatible API 호출** 대비 얼마나 더 신뢰성 있고 효율적인 에이전트 동작을 제공하는지를
**정량적으로** 비교·검증하기 위한 평가 스위트입니다.

공개 reference 숫자: [`reference/`](reference/) · 해석 가이드: [`docs/eval.md`](../docs/eval.md)

> 본 평가 스위트는 설계된 9가지 지표와 비교 프레임워크를 사용합니다.
> 업계에서 검증된 벤치마크(BFCL v3, τ‑bench, AgencyBench, IFEval, Toolscore, RAGAS) 메트릭을 차용·통합했습니다.

---

## 0. 목적 & 비교 대상

비교의 본질은 *"동일 모델·동일 입력에서, 호출 레이어(=하네스)가 얼마나 실패 모드를 줄이는가"* 입니다.

| 영역 | Naive (baseline) | Harness (`exaone/`) |
|------|------------------|---------------------|
| 빈 200·reasoning-only 응답 복구 | 없음 | thinking off → nudge 2-stage retry (`exaone/llm/exaone_client.py::ExaoneAPIClient.chat`) |
| 도구 루프 | 호출부에서 직접 작성 | enrich → progress gate → finalize (`exaone/agents/tool_agent.py`) |
| 중복 도구 호출 차단 | 없음 | `ToolInvocationLedger` (canonical JSON args) |
| 구조화 출력 | `response_format`만 의존 | `JsonExtractor → AutoRepair → SchemaValidator` (`exaone/output/`) |
| 토큰 버짓 | 호출부 책임 | `prepare_messages_for_llm_chat` (input + reserved ≤ 256k) |
| 라우팅 / 사고 제어 | 없음 | `ThinkingRouter`로 turn별 thinking·temperature·답변 포맷 결정 |

따라서 지표는 단순 정답률만이 아니라, **"하네스가 막아주는 실패 모드"를 모두 가시화**할 수 있도록 9개 축으로 설계했습니다.

---

## 1. 정량 지표 (9선)

### M1. Task Success Rate — TSR (E2E 과업 성공률)

- **정의**: 최종 응답이 ground truth 기준을 만족하는 비율.
- **공식**: `TSR = (1/N) · Σ 1[ŷᵢ ⊨ yᵢ]`
- **채점**:
  - 스칼라/엔티티: exact-match (정규화 후 비교).
  - 자유응답: rubric 기반 `LLM-as-a-Judge` (judge 모델은 평가 대상 모델과 분리).
- **출처**: AgentBench *Success Rate*, AgencyBench *Average Score*, τ‑bench reward `r ∈ {0,1}`.

### M2. pass^k Reliability (재현 신뢰도)

- **정의**: 동일 태스크를 *k*번 독립 실행했을 때 **k번 모두 성공**할 확률.
- **공식**: `pass^k = (1/N) · Σᵢ Πⱼ 1[rᵢ,ⱼ = 1]` (j = 1..k)
- **권장 *k***: 1, 2, 4, 8 모두 보고 → 지수감쇠(stochasticity 영향) 시각화.
- **출처**: τ‑bench (Sierra/Princeton, Yao et al. 2024). 일반 `pass@k`(적어도 한 번 성공)와 달리 production-grade 신뢰성 지표.
- **기대**: 하네스의 ledger + thinking-off retry가 분산을 줄여 `pass^4 / pass^1` 비율이 baseline보다 높게 유지되어야 정상.

### M3. Tool Selection Accuracy — TSA (도구 선택 정확도)

- **정의**: 호출된 도구 집합이 정답 도구 집합과 일치한 비율.
- **공식**:
  - strict: `1[tools_pred == tools_gold]`
  - soft: set-level F1 또는 Jaccard
- **출처**: BFCL v3 AST matching, Toolscore *Selection Accuracy* (40% 가중치).
- **주의**: 하네스는 `tool_agent_key__tool_name`(예: `rag__retrieve`) 네이밍을 사용하므로,
  비교 시 dispatch 후 logical name(`rag.retrieve` 등)으로 정규화하여 매칭합니다.

### M4. Argument F1 / Parameter Validity (인자 정확도)

- **정의**: 도구 호출 시 (1) 인자 이름이 스키마와 일치, (2) 타입 일치, (3) 값 일치의 token-level F1.
- **공식**: `F1 = 2·|args_pred ∩ args_gold| / (|args_pred| + |args_gold|)`
- **값 비교**: case-insensitive, whitespace/punctuation 정규화 (BFCL 규칙).
- **출처**: BFCL v3 sub-tree matching, Toolscore *Argument F1* (30% 가중치).
- **기대**: 하네스의 `input_model`(typed callable) 강제로 인자 누락·타입 오류 감소.

### M5. Irrelevance / Abstention Rate (불필요한 도구 호출 억제율)

- **정의**: "도구를 부르면 안 되는" 케이스에서 모델이 빈 `tool_calls`를 반환한 비율 = **환각 호출 억제력**.
- **공식**: `Abstain = #{tool_calls = ∅ | gold = ∅} / #{gold = ∅}`
- **출처**: BFCL v3 *Irrelevance Detection* (875건) — 정답은 "함수 호출 없음".
- **기대**: `NextStepPlanner.evaluate_progress`가 finalize 결정을 LLM JSON으로 게이팅하므로 무한 enrich 방지.

### M6. Schema Adherence — Strict / Loose (구조화 출력 성공률)

- **정의**: 응답이 사전에 약속한 JSON 스키마(또는 verifiable instruction)를 만족하는 비율.
- **공식**:
  - strict: `JsonExtractor` 단독 통과율
  - loose: `JsonExtractor → AutoRepair` 통과율
  - **repair gain = loose − strict** ⇒ 하네스 repair 단계의 순 기여분
- **출처**: IFEval(Google, Zhou et al. 2023) prompt-level / instruction-level × strict / loose 4축, PLAYBOOK Part 7.1의 *structured output success ≥ 95%*.
- **기대**: naive는 `response.choices[0].message.content` raw 파싱 성공률로 잡고, 하네스는 `StructuredOutputPipeline` 통과율을 그대로 사용.

### M7. Trajectory Efficiency — Step / Token Efficiency

- **정의**: 성공한 태스크에 들어간 **턴 수·토큰 수** 분포.
- **공식 (요약 단일값)**:
  - `StepEff = TSR / mean(turns)`
  - `TokenEff = TSR / (mean(total_tokens) / 1000)`
- **출처**: AgencyBench *Attempt Efficiency* / *Token Efficiency* (Fig. 4), Toolscore *Sequence Accuracy* (20% 가중치).
- **데이터 소스**:
  - 하네스: `AgentResult.metadata["llm_calls"]` (phase, latency_ms) + `usage.input_tokens/output_tokens` 자동 기록.
  - naive: 동일 키를 직접 로깅해야 공정 비교 가능.

### M8. Redundancy Rate (중복 / 스톨 호출 비율)

- **정의**: 동일 `(tool, canonical_args)` 또는 의미적 동의어 호출이 한 trajectory 내에서 반복된 비율.
- **공식**: `Redundancy = #duplicate_calls / #total_calls` (낮을수록 좋음)
- **canonical_args**: 키 정렬 + whitespace 제거 + 숫자 정규화 (하네스 ledger와 동일 규칙).
- **출처**: Toolscore *Redundancy* (10% inverted weight), `sentinel`의 `LoopDetectionGuard` (hard loop vs semantic loop 구분).
- **기대**: 하네스는 `ToolInvocationLedger`로 deterministic 차단 ⇒ 0에 수렴. naive ReAct 루프 직접 구현 시 통상 5~20% 발생.

### M9. Groundedness / Faithfulness (출처 정합성)

- **정의**: 최종 답안의 사실 주장(claims)이 도구/검색 결과 컨텍스트로 entailment 되는 비율. **환각 억제 지표**.
- **공식**: `Faith = #{claims entailed by context} / #total_claims`
- **채점**: claims 추출·entailment 모두 judge LLM 사용 (RAGAS / HaluBench 방식).
- **출처**: RAGAS *faithfulness*, HaluBench / Lynx (reference-free), PLAYBOOK Part 7.1 *RAG 0-hit ratio*.
- **기대**: ToolAgent(rag) finalize에서 `sources` 필드를 강제 ⇒ 인용 가능한 응답만 통과.

### M10. Empty-response Recovery (빈 응답 복구율)

- **정의**: 빈 content(또는 reasoning-only) 응답이 발생한 trial 중, 하네스 재시도로 **복구에 성공한 비율**.
- **공식**: trial별 `recovery_successes / empty_triggers` ([0, 1] clamp) → trigger가 있는 trial들의 평균. trigger가 0인 trial은 제외.
- **채점**: runner가 `metadata["recovery"]`에 `empty_triggers`·`recovery_successes`를 채움 (완전 자동).
- **출처**: `exaone.llm.response_quality` + `ExaoneAPIClient.chat` 재시도 경로.
- **기대**: 하네스는 HTTP-layer 재시도로 복구 ⇒ 높음. naive runner는 복구 경로가 없어 0.

---

## 2. 한눈에 보는 지표 행렬

| ID | 지표 | 출처 | 단위 | 기대 격차 (naive → harness) | 자동 산출 |
|----|------|------|------|------------------------------|-----------|
| M1 | Task Success Rate | AgentBench, τ‑bench, AgencyBench | % | 중~대 | 부분 (LLM judge) |
| M2 | pass^k Reliability | τ‑bench | % @ k=4 | 대 | 완전 |
| M3 | Tool Selection Accuracy | BFCL v3, Toolscore | % | 소~중 | 완전 (AST) |
| M4 | Argument F1 | BFCL v3, Toolscore | F1 | 중 | 완전 (AST) |
| M5 | Irrelevance / Abstention | BFCL v3 | % | 중 | 완전 |
| M6 | Schema Adherence (strict / loose) | IFEval, PLAYBOOK 7.1 | % | 대 | 완전 |
| M7 | Step / Token Efficiency | AgencyBench Fig. 4 | TSR / (turns·1k토큰) | 중 (양방향) | 완전 |
| M8 | Redundancy Rate | Toolscore, sentinel | % (↓ 좋음) | 대 (ledger 효과) | 완전 |
| M9 | Faithfulness / Groundedness | RAGAS, HaluBench | % | 중 | 부분 (LLM judge) |
| M10 | Empty-response Recovery | `exaone.llm.response_quality` | % | 대 (naive = 0) | 완전 |

**그룹별 의미**

- **품질**: M1, M2, M6, M9 — *"정답 · 신뢰 · 환각"* 축
- **에이전트 코어 능력**: M3, M4, M5 — *"옳은 도구를 / 필요할 때만 / 정확한 인자로"* (BFCL 정통)
- **효율 · 안정성**: M7, M8, M10 — 하네스의 router · ledger · 재시도 복구 기여 가시화

---

## 3. 비교 실험 설계

### 3.1 변인 통제 (필수)

- **모델·엔드포인트 동일**: Friendli `K-EXAONE-236B-A23B` 한 가지로 고정.
- **샘플링 동일**: `temperature=1.0, top_p=0.95, do_sample=True` (HF 가이드, `exaone/llm/exaone_client.py:46-47`).
- **시스템 프롬프트 동일**, messages 직렬화 결과 동일.
- **시드 / 호출 순서 고정** (가능한 한도 내, k회 반복 시 trial id만 분리).

### 3.1.1 K-EXAONE 2.0 API kwargs (`preserve_thinking`)

`exaone.llm.ExaoneAPIClient`를 거치지 않는 runner(τ-bench, Harbor upstream, Claw-Eval 등)는 **`eval/exaone_api_kwargs.py`** 로 동일한 `chat_template_kwargs`를 맞춥니다.

| 벤치 유형 | `enable_thinking` | `preserve_thinking` |
|-----------|-------------------|---------------------|
| Agentic (τ-bench, Harbor, Claw-Eval) | `True` (기본) | **`True` (기본)** — 효과는 K-EXAONE 2.0+ |
| 단발 QA · user simulator | `False` | `False` |

```bash
# .env — agentic eval 기본값 (payload에 항상 실림; 1.0은 preserve 무시)
EXAONE_ENABLE_THINKING=1
EXAONE_PRESERVE_THINKING=1
EXAONE_EVAL_AGENT_TEMPERATURE=0.7
```

```python
from eval.exaone_api_kwargs import build_extra_body

extra_body = build_extra_body()  # agentic defaults: thinking + preserve
```

상세 가이드: [`docs/k_exaone_2.md`](../docs/k_exaone_2.md).

### 3.2 두 가지 호출 모드

1. **Naive baseline** — `runners/naive_runner.py` *(예정)*
   - `requests.post("{EXAONE_BASE_URL}/chat/completions", json=payload)` 직접 호출.
   - 빈 200·reasoning-only 복구 **없음**, JSON repair **없음**, 도구 중복 차단 **없음**.
   - 도구 루프는 단순 `while resp.tool_calls: exec_tools → 재호출`.

2. **Harness** — `runners/harness_runner.py` *(예정)*
   - `ToolAgent(...).run(AgentContext(query=...), llm=ExaoneAPIClient(...))` 그대로 사용.

### 3.3 데이터셋 (eval 폴더 외부에서 새로 도입)

| 영역 | 권장 데이터셋 | 측정 지표 |
|------|----------------|-----------|
| 도구 호출 정확도 | BFCL v3 `simple`, `multiple`, `parallel`, `irrelevance` | M3, M4, M5, M6 |
| 멀티턴 신뢰성 | τ‑bench `retail`, `airline` (LLM user simulator) | M1, M2, M7, M8 |
| 지시 준수 | IFEval 25종 verifiable instructions | M6 |
| RAG 환각 | HaluBench / RAGAS 평가셋 (혹은 사내 코퍼스 적용) | M9 |

> **한국어 특화**: BFCL / IFEval 일부 프롬프트는 K-EXAONE용 한국어 버전으로 번역·재구축(human-in-the-loop) 권장.

### 3.4 자동 계산 데이터 소스

- **하네스**: 이미 구조화 로그가 있음.
  - `AgentResult.metadata["llm_calls"]` (`exaone/agents/run_trace.py::LlmCallTrace`) — phase, latency_ms, schema_name
  - `exaone/observability/fields.py`의 키 그대로 사용:
    - `TOOL_INVOCATIONS`, `DUPLICATES_BLOCKED`, `ENRICH_STOP_REASON`
    - `LLM_EMPTY_CONTENT`, `LLM_REASONING_ONLY`, `LLM_EMPTY_RETRY_SUCCESS`
    - `STRUCTURED_SUCCESS`, `STRUCTURED_ERROR`
- **naive**: 동일 키 세트를 직접 로깅하도록 runner에 hook 추가 → 공정 비교 보장.

### 3.5 보고 형식

- **수치**: 평균 + bootstrap 95% CI (n_resample ≥ 1000).
- **pass^k** (M2): *k = 1, 2, 4, 8* 모두 보고. τ‑bench 컨벤션의 지수감쇠 가시화.
- **효율** (M7): Pareto 산점도 — x = mean tokens, y = TSR — AgencyBench·Alan 블로그 스타일.
- **실패 모드 breakdown**: M5/M8/M6의 strict↔loose gap을 stack-bar로 표시.

---

## 4. 권장 폴더 구조 (구현 시)

```
eval/
├── README.md                       # (this file)
├── metrics/                        # 지표 계산 모듈 (provider 비의존)
│   ├── __init__.py
│   ├── m1_task_success.py
│   ├── m2_pass_k.py
│   ├── m3_tool_selection.py        # BFCL AST matching
│   ├── m4_argument_f1.py
│   ├── m5_abstention.py
│   ├── m6_schema_adherence.py      # strict / loose
│   ├── m7_efficiency.py
│   ├── m8_redundancy.py            # canonical_args 정규화 포함
│   └── m9_faithfulness.py          # LLM judge
├── runners/
│   ├── naive_runner.py             # 순수 HTTP + 단순 ReAct 루프
│   ├── harness_runner.py           # ToolAgent.run() 래퍼
│   └── common.py                   # trace schema, 로깅 키
├── datasets/                       # 외부 벤치마크 변환 결과 (git-ignored 권장)
│   ├── bfcl_v3/
│   ├── tau_bench/
│   ├── ifeval/
│   └── halubench/
├── judges/                         # LLM-as-a-Judge 프롬프트 & 클라이언트
│   ├── rubric_judge.py
│   └── entailment_judge.py
├── reports/                        # JSON / Markdown / 산점도
│   └── .gitkeep
├── run.py                          # CLI (`python -m eval.run`)
├── pipeline.py                     # task 로드 → runner → M1–M10
├── report.py                       # JSON / Markdown (M8 = 1 − redundancy 표시)
```

---

## 5. 실행

```bash
# 데이터셋 목록
python -m eval.run --list-datasets

# BFCL tool-calling 비교 (naive + harness)
python -m eval.run --dataset bfcl_v3.simple --limit 5 --pass-k-trials 2

# harness만 스모크
python -m eval.run --dataset bfcl_v3.simple --limit 2 --pass-k-trials 1 --runners harness

# 결과
ls eval/reports/  # {timestamp}.json + {timestamp}.md
```

---

## 6. 참고문헌

| 항목 | 출처 |
|------|------|
| BFCL v3 (AST matching, irrelevance) | <https://gorilla.cs.berkeley.edu/leaderboard.html> |
| τ‑bench (`pass^k`) | Yao et al. 2024 — <https://arxiv.org/abs/2406.12045>, <https://github.com/sierra-research/tau-bench> |
| AgencyBench (효율 메트릭, long-horizon) | <https://github.com/GAIR-NLP/AgencyBench> |
| IFEval (strict / loose) | Zhou et al. 2023 — <https://arxiv.org/abs/2311.07911> |
| Toolscore (선택·인자·시퀀스·중복) | <https://github.com/yotambraun/toolscore> |
| RAGAS (faithfulness) | <https://github.com/explodinggradients/ragas> |
| HaluBench / Lynx (reference-free faithfulness) | <https://github.com/EdinburghNLP/awesome-hallucination-detection> |
| sentinel (loop detection patterns) | <https://github.com/darshjme/sentinel> |
| EXAONE 운영 SLO 축 | 본 레포 `PLAYBOOK.md` Part 7, `exaone/observability/slo.py` |
| EXAONE 로그 키 컨벤션 | `exaone/observability/fields.py` |

---

## 7. 비교 결과를 읽는 법 (요약)

| 관찰 | 해석 |
|------|------|
| M2 `pass^4 / pass^1` 이 하네스에서 더 높음 | ledger + thinking-off retry 가 분산을 줄여 production 신뢰성 ↑ |
| M6 `loose − strict` gap 이 하네스에서 큼 | `AutoRepair` 가 실제 JSON 실패를 복구하고 있다는 직접 증거 |
| M5(Abstention) 이 하네스에서 높음 | `NextStepPlanner` 가 불필요한 enrich 호출을 끊고 있음 |
| M8(Redundancy) 이 하네스에서 ≈ 0 | `ToolInvocationLedger` 가 정상 동작 (deterministic 차단) |
| M7 TokenEff 가 하네스에서 더 높음 | `ThinkingRouter` 가 turn별로 thinking 을 끄는 효과 |
| M9 Faithfulness 가 하네스(rag)에서 높음 | finalize 의 `sources` 인용 강제 효과 |

반대 패턴이 나오면 **하네스가 막아주려던 실패 모드 자체가 trigger 되지 않은 데이터셋**인지부터 점검합니다
(예: 모두 single-tool / single-turn 이면 M2·M8 격차는 의미가 작음).
