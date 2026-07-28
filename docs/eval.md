# `eval/` — Harness vs Naive 벤치마크

**여기는 어떤 곳인가요?**  
동일 모델·동일 입력에서 **`exaone/` 하네스**와 **naive OpenAI-compatible API 호출**을 나란히 돌려, 에이전트 동작을 **M1–M10 한 표**로 비교하는 오픈소스 평가 스위트입니다.

- 구현·수식: [`eval/README.md`](../eval/README.md)
- 본 문서: **지표 정의**, **pass^k 설명**, **실행·로드맵**

---

## 1. 비교의 본질

| | Naive baseline | Harness (`exaone/`) |
|---|----------------|---------------------|
| API 호출 | `chat/completions` 직접 + 단순 `while tool_calls` | `ToolAgent.run()` |
| 빈 응답 / reasoning-only 복구 | 없음 | thinking off → nudge retry |
| 중복 tool 호출 | 허용 | `ToolInvocationLedger` 차단 |
| JSON / schema | raw parse | `JsonExtractor → AutoRepair → SchemaValidator` |
| 라우팅 | 없음 | `ThinkingRouter`, `NextStepPlanner` |

---

## 2. M1–M10 — 같은 평면, **전부 ↑ 높을수록 좋음**

리포트·README·그래프에서 **10개 지표를 동등하게** 나란히 둡니다.  
**Δ = harness − naive** → **양수 = 하네스 우위** (M1–M10 공통).

| ID | 이름 | 무엇을 재는가 | 데이터셋 예 | 구현 |
|----|------|---------------|-------------|------|
| **M1** | Task Success Rate | 과업 정답 비율 | BFCL, τ-bench | ✅ |
| **M2** | pass^k Reliability | 같은 문제 **k번 연속** 성공 비율 | BFCL, τ-bench | ✅ |
| **M3** | Tool Selection Accuracy | 정답 도구 multiset 일치 | BFCL | ✅ |
| **M4** | Argument F1 | 도구 인자 정확도 | BFCL | ✅ |
| **M5** | Abstention Score | “도구 쓰지 마”일 때 실제로 안 씀 | BFCL irrelevance | ✅ |
| **M6** | Schema Adherence | JSON/schema 준수 (loose; repair_gain은 breakdown) | IFEval | ✅ |
| **M7** | Token Efficiency Score | `TSR / (mean_tokens/1000)` — 적은 토큰으로 성공 | 전체 | ✅ |
| **M8** | Call Uniqueness Score | `1 − redundancy_rate` — 중복 호출 없음 | BFCL, τ-bench | ✅ |
| **M9** | Faithfulness Score | 답변이 컨텍스트에 grounded | HaluBench | ✅ |
| **M10** | Empty-response Recovery Score | 빈/reasoning-only 응답 후 복구 성공률 | logged trials | ✅ |

**M8 표기:** 내부는 `redundancy_rate`(낮을수록 좋음). **공개 스코어는 `1 − redundancy`** 로 뒤집어 M1–M7과 방향을 맞춥니다.

---

## 3. pass^k / pass⁴ / pass⁸ — M2가 뭔지

**M2 = pass^k** (τ-bench, [Yao et al. 2024](https://arxiv.org/abs/2406.12045))

같은 task를 **서로 독립적으로 k번** 돌렸을 때, **k번 모두 성공**한 task 비율입니다.

```
pass^k = (성공한 trial이 k개인 task 수) / (전체 task 수)
```

| 기호 | 의미 | `--pass-k-trials` |
|------|------|-------------------|
| **pass¹** | 1번만 돌려도 성공한 task 비율 | `1` (M1과 비슷한 단일 시도 관점) |
| **pass²** | **2번 연속** 둘 다 성공 | `2` ← 이번 reference run |
| **pass⁴** | **4번 연속** 모두 성공 | `4` |
| **pass⁸** | **8번 연속** 모두 성공 | `8` |

**직관:** k가 커질수록 점수는 **떨어지기 마련**입니다. LLM은 확률적이라 “한 번은 운 좋게 맞춤”과 “매번 맞춤”은 다릅니다.

```
pass¹  0.87  ████████████████████
pass²  0.84  ██████████████████    ← 이번 run (harness)
pass⁴  0.78  ████████████████      ← 예시: k↑ 하면 보통 ↓
pass⁸  0.65  █████████████         ← 예시
```

**pass² / pass¹** 이 harness에서 더 **완만하게** 떨어지면 → “가끔 맞추기”가 아니라 **안정적으로 맞춘다**는 뜻입니다.

### pass@k 와 헷갈리지 말 것

| | pass^k (M2, **우리가 씀**) | pass@k (코딩 벤치 등) |
|---|---------------------------|----------------------|
| 정의 | k번 **전부** 성공 | k번 중 **하나라도** 성공 |
| k↑ 시 | 점수 **↓** (더 어려움) | 점수 **↑** (더 쉬움) |
| 용도 | production **재현성** | 탐색·샘플링 여지 |

pass⁴/pass⁸은 **별도 지표가 아니라 M2를 k=4, k=8로 돌린 값**입니다. 리포트 `breakdown`에 `pass_1`, `pass_2`, `pass_4`, `pass_8`로 함께 적습니다.

```bash
# pass⁴까지 보려면
python -m eval.run ... --pass-k-trials 4

# pass⁸까지
python -m eval.run ... --pass-k-trials 8
```

(`--pass-k-trials 8` → task당 8 API 호출 × 2 runner → 비용·시간 4배 이상)

---

## 4. Reference run (2026-05-28, BFCL 100 tasks, pass²) — subset baseline

```bash
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance \
  --limit 25 --pass-k-trials 2 --sleep 3
```

고정 스냅샷: [`eval/reference/bfcl_pass2_20260528.snapshot.json`](../eval/reference/bfcl_pass2_20260528.snapshot.json)  
로컬 전체 리포트 예: `eval/reports/20260528T163231Z.{md,json}` (gitignore)

**M1–M10 중 이번 run에서 산출된 것** (나머지는 `—`, 해당 데이터셋 미실행).

| ID | 이름 | Naive | Harness | Δ (h−n) |
|----|------|------:|--------:|--------:|
| M1 | Task Success Rate | 0.840 | 0.840 | +0.000 |
| M2 | pass² Reliability | 0.827 | 0.827 | +0.000 |
| M3 | Tool Selection Accuracy | 0.667 | 0.840 | +0.173 |
| M4 | Argument F1 | 0.687 | 0.784 | +0.097 |
| M5 | Abstention Score | 0.960 | 0.860 | −0.100 |
| M6 | Schema Adherence | — | — | — |
| M7 | Token Efficiency Score | 0.558 | 0.236 | −0.322 |
| M8 | Call Uniqueness Score | 0.785 | 1.000 | +0.215 |
| M9 | Faithfulness Score | — | — | — |
| M10 | Empty-response Recovery | — | — | — |

M2 breakdown (동일 run): naive pass¹=0.840, pass²=0.827 / harness pass¹=0.840, pass²=0.827.

**M7 해석:** harness는 router·JSON repair 등 **내부 LLM 호출 토큰**이 naive 대비 많아 M7이 낮게 나올 수 있습니다. M1이 비슷한데 M7↓이면 “품질은 유지, 비용↑” trade-off로 읽습니다 (Phase 1에서 집계 범위 통일 예정).

**Scope:** BFCL v3 subset 100건, tool-centric. IFEval·HaluBench·τ-bench 미포함.  
→ **M1–M10 종합 표 (Table A)** 는 [§4.1](#41-종합-표-cookbook-matrix) Cookbook matrix reference (2026-06-08).

---

## 4.1 종합 표 (Cookbook matrix)

**한 장의 M1–M10 표**에 BFCL + IFEval + HaluBench를 묶습니다. τ-bench는 **별도 표**([§4.2](#42-시뮬레이션-표-τ-bench)) — 측정 축·비용·pass^k 해석이 달라 cherry-pick 없이 역할을 분리합니다.

| 리포트 | 데이터셋 | 채우는 M (주력) |
|--------|----------|-----------------|
| **Cookbook matrix** | BFCL 4종 + `ifeval` + `halubench` | M1–M6, M7, M8, M9, M10* |
| **τ-bench simulation** | `tau_bench.retail` + `tau_bench.airline` | M1–M4, M7, M8, M2(pass^k) |

\* M10은 empty/reasoning-only trigger가 있는 trial만 집계(없으면 행 생략).

```bash
# Cookbook matrix — 한 run, 한 리포트 (권장 limit는 dataset별 조정 가능)
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \
  --limit 25 --pass-k-trials 2 --sleep 3
```

- BFCL 4종 × 25 = **100** tool tasks  
- IFEval × 25 → **M6**  
- HaluBench × 25 → **M9**  
- 합계 **150 tasks/runner** (×2 naive/harness, ×pass²) — 시간·비용 크므로 스모크는 `--limit 5`부터.

**OSS 규칙:** Cookbook matrix 표에서 **Δ > 0 / Δ < 0 모두** 같은 표에 둡니다 ([§9](#9-오픈소스--하지-말-것)). BFCL만·τ-bench만 골라 headline 내지 않습니다.

### Reference run (2026-06-08, Table A, pass²)

고정 스냅샷: [`eval/reference/cookbook_matrix_pass2_20260608.snapshot.json`](../eval/reference/cookbook_matrix_pass2_20260608.snapshot.json)  
로컬 전체 리포트: `eval/reports/20260608T132721Z.{md,json}` (gitignore)

| ID | 이름 | Naive | Harness | Δ (h − n) |
|----|------|------:|--------:|--------:|
| **M1** | Task Success Rate | 0.645 | 0.630 | −0.015 |
| **M2** | pass² Reliability | 0.853 | 0.787 | −0.067 |
| **M3** | Tool Selection Accuracy | 0.680 | 0.840 | +0.160 |
| **M4** | Argument F1 | 0.711 | 0.780 | +0.069 |
| **M5** | Abstention Score | 0.900 | 0.900 | +0.000 |
| **M6** | Schema Adherence | 0.020 | 0.520 | +0.500 |
| **M7** | Token Efficiency Score | 0.516 | 0.201 | −0.315 |
| **M8** | Call Uniqueness Score | 0.863 | 1.000 | +0.137 |
| **M9** | Faithfulness Score | 0.508 | 0.565 | +0.057 |
| **M10** | Empty-response Recovery Score | 0.000 | 1.000 | +1.000 |

M2 breakdown: naive pass¹=0.853, pass²=0.853 / harness pass¹=0.840, pass²=0.787.  
M5 breakdown (irrelevance only): harness hallucinated tool calls **6** vs naive **5**.

**표 읽는 법 (Table A):**

- **Harness 우위 (Δ > 0):** M3/M4 tool orchestration, M6 IFEval instructions, M8 duplicate-call blocking, M9 HaluBench faithfulness (fair answer-field judge), M10 empty-response recovery infrastructure.
- **동률 (Δ = 0):** M5 — abstention parity on this run.
- **Harness 열위 (Δ < 0):** M1/M2 (stochasticity on BFCL judge TSR·pass²), M7 (~2.5× mean tokens — router/planner/finalize internal LLM cost).
- **이전 reference (2026-05-31):** [`cookbook_matrix_pass2_20260531.snapshot.json`](../eval/reference/cookbook_matrix_pass2_20260531.snapshot.json) — M9 was unfair (JSON wrapper scored); fixed via `faithfulness_answer_text` nested unwrap.
- **Table B (τ-bench):** not included — run separately ([§4.2](#42-시뮬레이션-표-τ-bench)).

---

## 4.2 시뮬레이션 표 (τ-bench)

τ-bench는 LLM user simulator + 도메인 런타임이 필요합니다. **별도 CLI run → 별도 JSON/MD**로 둡니다 (Cookbook matrix와 파일 분리).

**설치:** `uv pip install '.[eval-taubench]'` (또는 `uv pip install git+https://github.com/sierra-research/tau-bench.git`).

```bash
# pass⁴ 이상 권장 (M2 pass^k 정본)
python -m eval.run \
  --dataset tau_bench.retail,tau_bench.airline \
  --limit 25 --pass-k-trials 4 --sleep 3 \
  --out-dir eval/reports/taubench
```

| | Cookbook matrix | τ-bench 표 |
|---|-----------------|------------|
| 질문 | 도구·지시·RAG 환각·복구를 **한 평면**에서? | **멀티턴 E2E·pass^k**만? |
| M5/M6/M9 | ✓ (BFCL/IFEval/Halu) | — (다른 벤치가 정본) |
| M2 해석 | BFCL pass² (보조) | **pass⁴/pass⁸가 정본** |
| 리포트 | `eval/reports/{ts}.md` | `eval/reports/taubench/{ts}.md` (권장) |

두 표를 README/블로그에 쓸 때: **“Table A: Cookbook matrix”**, **“Table B: τ-bench simulation”** 로 명시.

---

## 5. 데이터셋 ↔ M1–M10

한 run에 모든 지표가 나오지는 않습니다. **task 종류에 따라 해당 M만 계산**하고, 리포트에는 **같은 표에 `—`** 로 둡니다.

| 데이터셋 | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 |
|----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| BFCL simple/multiple/parallel | ✓ | ✓ | ✓ | ✓ | | | ✓ | ✓ | | |
| BFCL irrelevance | | | | | ✓ | | ✓ | | | |
| IFEval | ✓ | ✓ | | | | ✓ | ✓ | | | |
| τ-bench | ✓ | ✓ | ✓ | ✓ | | | ✓ | ✓ | | |
| HaluBench | ✓ | | | | | | ✓ | | ✓ | |
| (any, observability log) | | | | | | | | | | ✓ |

**풀 매트릭스 (M6/M9 포함):** [§4.1](#41-종합-표-cookbook-matrix) — BFCL + IFEval + HaluBench **한 run**.  
τ-bench는 [§4.2](#42-시뮬레이션-표-τ-bench). 여러 날에 나눠 돌린 JSON을 합칠 때는 merge CLI (로드맵 Phase 3).

---

## 6. 실행

`.env`: `EXAONE_API_KEY`, `EXAONE_BASE_URL`, `EXAONE_MODEL`

```bash
# (A) BFCL only — 빠른 스모크 / CI
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance \
  --limit 25 --pass-k-trials 2 --sleep 3

# (B) Cookbook matrix — BFCL + IFEval + HaluBench 종합 표
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \
  --limit 25 --pass-k-trials 2 --sleep 3

# (C) τ-bench simulation — 별도 표
python -m eval.run \
  --dataset tau_bench.retail,tau_bench.airline \
  --limit 25 --pass-k-trials 4 --sleep 3 \
  --out-dir eval/reports/taubench

# pass⁴·pass⁸ curve (M2 breakdown, BFCL subset)
python -m eval.run \
  --dataset bfcl_v3.simple \
  --limit 25 --pass-k-trials 8 --sleep 3
```

**결과:** `eval/reports/{timestamp}.md` (표), `{timestamp}.json` (breakdown + trials).  
τ-bench는 `--out-dir eval/reports/taubench` 등 **별도 디렉터리** 권장.

**데이터셋 캐시:** HuggingFace 다운로드는 레포 루트 `_dataset/` (gitignore). 상세는 [`eval/datasets/README.md`](../eval/datasets/README.md) §6.

**IFEval / HaluBench (Hugging Face):** 사내망 SSL 검사 시 `.env`에 `DISABLE_SSL_VERIFY=1` 또는 `HF_HUB_DISABLE_SSL_VERIFICATION=1` (또는 `REQUESTS_CA_BUNDLE`에 기업 CA). `eval.run`은 `load_dotenv` 후 Hub httpx 클라이언트를 맞춥니다 ([PLAYBOOK.md](../PLAYBOOK.md) Part 6.2).

**τ-bench:** optional `eval-taubench` extra. User simulator는 LiteLLM → `EXAONE_*` (`TAU_BENCH_USER_STRATEGY`, `TAU_BENCH_MAX_STEPS`).

---

## 7. 로드맵 (티어 없음 — 구현·측정 개선만)

| Phase | 내용 |
|-------|------|
| **0** | `docs/eval.md` M1–M10 평면 표; `eval/run.py` M8 Call Uniqueness display |
| **1** | M7 token 집계 범위 통일; naive baseline v2 (429/SSL); harness ablation flags |
| **2** | Cookbook matrix run (BFCL+IFEval+HaluBench); M10 recovery 집계 |
| **3** | τ-bench simulation reference run; `--pass-k-trials 8` reference; optional merge CLI |
| **4** | M5 irrelevance triage; irrelevance 프롬프트/router 튜닝 후 재run |

---

## 8. 리포트 읽는 법

1. **M1–M10 한 줄씩** 본다. Δ > 0이면 harness 우위.
2. **M2**는 pass¹·pass²(·pass⁴·pass⁸)를 breakdown에서 같이 본다 — k↑ 하며 얼마나 떨어지는지.
3. **M6** `repair_gain` = loose − strict (JSON AutoRepair 기여).
4. **M7**↓, **M5**↓도 숨기지 않는다 — 같은 표에서 trade-off로 읽는다.
5. `—`는 “이 run/data에 해당 없음”, 0점이 아님.

---

## 9. 오픈소스 — 하지 말 것

- 특정 M만 골라 headline 내기 (cherry-pick)
- M7에서 harness internal LLM call 제외
- pass@k로 M2 대체
- ad-hoc “Harness Score” 가중합

---

## 10. 폴더 · 참고

```
eval/
├── README.md      # M1–M10 수식 spec
├── run.py              # CLI (`python -m eval.run`)
├── pipeline.py         # load → run → metrics
├── report.py           # JSON / Markdown
├── metrics/       # m1 … m10
├── runners/
├── datasets/
├── judges/
└── reports/

test/unit_eval/    # eval 단위 테스트 (metrics, runners, datasets, datasets_smoke)
```

| 참고 | 링크 |
|------|------|
| 지표 spec | [`eval/README.md`](../eval/README.md) |
| pass^k | [τ-bench](https://arxiv.org/abs/2406.12045) |
| BFCL | [Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-08 | Cookbook matrix reference (`cookbook_matrix_pass2_20260608.snapshot.json`); M9 fair judge (`faithfulness_answer_text`); Table A refresh |
| 2026-05-31 | Cookbook matrix reference (`cookbook_matrix_pass2_20260531.snapshot.json`); Table A M1–M10 + trade-off notes in §4.1 |
| 2026-05-29 | Reference run 숫자를 `eval/reference/bfcl_pass2_20260528.snapshot.json` 과 동기화; M7 trade-off 해석 추가 |
| 2026-05-29 | Cookbook matrix vs τ-bench 별도 표 전략; M6/M9/M10 pipeline 반영 |
| 2026-05-28 | Tier 제거; M1–M10 평면 비교; pass^k/pass⁴/pass⁸ 설명 추가 |
