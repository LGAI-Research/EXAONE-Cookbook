# Track 08 — Evaluation (M1–M10)

> "eval 없이 에이전트를 늘리지 마라." 고정 테스트셋과 표준 지표가 없으면, 더 화려한 데모는 그저 더 화려한 추측일 뿐입니다.
> Agent Learning Hub 매핑: **Stage 7**(평가) · Project Ladder **L11** · 원칙 4(eval 먼저)·5(trace·근거).

이 트랙의 지표는 **M1–M10** 입니다. (디렉토리명만 `m1_m10`; M10 = Empty-response Recovery.)

---

## 학습 목표

- [ ] 10개 표준 지표(M1–M10)가 *무엇을·왜* 재는지 합성 trial 로 직접 계산한다.
- [ ] pass^k(≠ pass@k), strict/loose 스키마, abstention, faithfulness, recovery 의 채점 방식을 구분한다.
- [ ] 내 팀의 **골든셋**(고정 테스트셋)을 만들고 회귀 임계값을 건다.
- [ ] `eval.run` 매트릭스 + τ-bench E2E 로 실제 데이터셋에 연결한다.

---

## 노트북

이 트랙은 **Master 1개 + deep-dive 1개**입니다.

| 파일 | 다루는 내용 | 산출물 |
|---|---|---|
| [`08a_evaluation_lab.ipynb`](./08a_evaluation_lab.ipynb) | 메트릭 지도(M1–M10) → **M1/M2** → **M3/M4** → **M5/M6** → **M7/M8/M9** → **M10** → 합성 smoke + `eval.run` | `_out/metric_map.json`, `_out/eval_table.md` |
| [`08b_my_golden_set.ipynb`](./08b_my_golden_set.ipynb) | **deep-dive** 골든셋 회귀(M1/M5/M6/M9/M3) + BFCL·IFEval·τ-bench 연결 | `_out/my_golden.jsonl`, `_out/regression_report.json` |

**거의 전부 키 없이 실행됩니다.** 모든 지표를 합성 `TrialResult` 로 계산하므로 LLM 이 필요 없습니다. `EXAONE_API_KEY` 가 있으면 `eval.run`/τ-bench E2E 까지 (`HAS_API` 가드).

### 08b 심화에서 직접 확인할 것

- 골든셋 행은 `category` 로 설명되지만, 실제 지표 분모는 `expected_answer`·`required_keys`·`grounding_context`·`expected_no_tools`·`gold_tools` 같은 **라벨 필드**가 정한다.
- `cases≥20` 같은 수량 체크가 아니라 `metric_coverage` 와 `all_rows_scored` 로 **죽은 패딩 행이 없는지** 확인한다.
- M1·M6·M5 는 값 임계값으로, M9 는 교육용 스텁 judge 이므로 **건수 임계값**으로만 게이트한다.
- 08b 는 실제 에이전트 E2E 평가가 아니라 **골든셋 설계·채점·회귀 게이트 메커니즘**을 가르친다. 실제 에이전트 출력에 이 게이트를 연결하는 흐름은 Track 10 캡스톤에서 다룬다.

### 10개 지표

| 지표 | 이름 | 모듈 |
|---|---|---|
| M1 | Task Success Rate | `eval.metrics.m1_task_success` |
| M2 | pass^k Reliability | `eval.metrics.m2_pass_k` |
| M3 | Tool Selection Accuracy | `eval.metrics.m3_tool_selection` |
| M4 | Argument F1 | `eval.metrics.m4_argument_f1` |
| M5 | Abstention Score | `eval.metrics.m5_abstention` |
| M6 | Schema Adherence | `eval.metrics.m6_schema_adherence` |
| M7 | Token Efficiency Score | `eval.metrics.m7_efficiency` |
| M8 | Call Uniqueness Score | `eval.metrics.m8_redundancy` |
| M9 | Faithfulness Score | `eval.metrics.m9_faithfulness` |
| M10 | Empty-response Recovery Score | `eval.metrics.m10_empty_recovery` |

### 동반 데이터 (`data/`)

| 파일 | 용도 |
|---|---|
| `golden_seed.jsonl` | deep-dive 골든셋 22행 (정답·필수키·근거 컨텍스트·기대 도구; M1·M5·M6·M9·M3 채점) |

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()

# (en) The eval.metrics modules are the source of truth; here we feed them synthetic trials.
# (kr) eval.metrics 모듈이 채점 정본이며, 여기서는 합성 trial 을 먹인다.
from eval.metrics import m1_task_success, m10_empty_recovery
from eval.metrics.types import TrialResult, ToolCallRecord

m1 = m1_task_success.compute(trials, golds, mode="exact")
m10 = m10_empty_recovery.compute(trials)
```

전체 규칙은 [`recipes/README.md`](../README.md). eval 프레임워크 정본은 [`eval/README.md`](../../eval/README.md).

---

## 체크포인트

- [ ] Master Session 7 mini-check 6개 PASS (M1=1.0, M6=1.0, **M10=0.5**, M2 pass^2=1.0, datasets≥8, τ-bench 등록) — **키 없이**.
- [ ] `metric_map.json` 에 M1–M10 **10개** 지도가 기록.
- [ ] deep-dive Session 2 회귀 mini-check 5개 PASS (모든 행 채점, M1·M6·M5 평균≥0.8, M9 건수≥3) — **키 없이**. (M3 는 g22 의도적 오호출 때문에 정보용.)

---

## 다음 트랙

- **Track 09 — Framework Bridges:** LangChain/LlamaIndex/LangGraph/Gradio 어댑터.
- **Track 10 캡스톤:** 이 골든셋 회귀를 **릴리스 게이트**로 묶어, 지표가 팀 임계값 아래로 떨어지면 배포를 멈춘다.

---

## 문제 해결

- `eval.run` 이 `[SKIP]` → `EXAONE_API_KEY` 확인. 합성 smoke·골든셋 회귀는 키 없이 그대로 충족됩니다.
- `ModuleNotFoundError: eval` → Track 08/10 은 로컬 `eval/` 패키지에 의존합니다. 저장소 루트에서 커널을 열고, 이 워크스페이스에 `eval/` 디렉터리가 있는지 확인하세요.
- 데이터셋 미리보기가 skip → 로컬에 벤치마크 캐시가 없거나 사내망 TLS 문제입니다(`REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`). 합성 경로는 영향 없습니다.
- `_out/` 위치가 헷갈림 → 08b 산출물은 Jupyter 실행 위치와 무관하게 `recipes/track08_evaluation_m1_m10/_out/` 아래에 저장됩니다.
- pass^k 가 헷갈림 → pass@k(k 중 1회 성공)가 아니라 pass^k(k회 *전부* 성공)입니다. τ-bench 신뢰도 컨벤션.
