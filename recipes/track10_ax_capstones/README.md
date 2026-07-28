# Track 10 — AX Capstones

> **Stage 8 (출시)** — 클론한 사람이 한 줄로 재현할 수 있고, 골든셋·SLO·트레이스·HITL을 갖춘 작은 에이전트로 마감합니다.

---

## 공통 통과 기준

모든 `10_0x_*.ipynb` 캡스톤은 아래 산출물을 갖춥니다.

- **문서:** README와 노트북 상단 시나리오로 제공합니다.
- **패키지:** 골든셋·메트릭·라이브 결과·트레이스·SLO는 `_out/0x/capstone_package.json`에 저장합니다.
- **범위:** README/시나리오는 JSON 필드가 아니라 문서 산출물로 봅니다.

| 항목 | 설명 |
|------|------|
| **README**(문서) | 본 파일 + 노트북 상단 시나리오. 패키지 JSON이 아니라 문서 산출물입니다. |
| **골든셋** | `data/capstone_golden.jsonl` — 공통 `capstone:"all"` 사례(정적 메트릭 데모용) + 캡스톤별 `capstone:"0x"` 사례(라이브 평가/도메인 채점용). 현재 공통 22건 + `01` 전용 2건 + `02` 전용 3건이며, 캡스톤별 고유 사례는 계속 보강하는 것을 권장합니다. |
| **정적 메트릭 데모 (M1 · M6 · M9)** | `08b_my_golden_set` 패턴으로 고정 fixture를 채점하는 **메트릭 동작 예시**입니다. 에이전트 성능이 아니며, `M9`(`LengthRatioJudge`)는 테스트 전용 스텁입니다. |
| **라이브 평가** | 캡스톤별 `capstone:"0x"` 사례를 **실제 에이전트 경로**로 실행해 채점합니다(예: `10_01`은 인용·근거 통과율). API 키가 필요합니다. |
| **트레이스 1세션** | JSONL 또는 `session_trace` 필드 |
| **HITL** | 위험 도구(03·05) — `auto_approve` / mock stdin |
| **SLOSpec** | `exaone.observability.SLOSpec` 1개 이상 |

> **선수 준비 (`eval/`):** 정적 메트릭 데모(M1·M6·M9)는 Track 08과 공유하는 `eval/` 지표 패키지(`from eval.metrics …`)를 사용합니다. 저장소 루트에서 Jupyter/커널을 실행하고 `pip install -e .`를 마치면 `eval/`이 import 경로에 잡힙니다. `eval/metrics/`가 없는 구버전 체크아웃에서는 `ModuleNotFoundError`가 발생하므로 최신 `eval/` 포함 여부를 확인하세요.

---

## 코드 시작 패턴

```python
import exaone

exaone.load_project_env()
# eval 회귀
# python recipes/track10_ax_capstones/capstone_runner.py --capstone 02
```

에이전트 본체는 `exaone.agents.*`, `exaone.tools.*` facade를 사용합니다. [`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade)

---

## 캡스톤 노트북

| 파일 | 시나리오 | 선수 트랙 |
|------|----------|-----------|
| [`10_01_capstone_internal_kb_qa.ipynb`](./10_01_capstone_internal_kb_qa.ipynb) | 조직 정책 매뉴얼(샘플) RAG QA + 인용 | 04, 07, 08 |
| [`10_02_capstone_meeting_minutes_to_actions.ipynb`](./10_02_capstone_meeting_minutes_to_actions.ipynb) | 회의록 → 액션아이템 JSON | 01, 06, 08 |
| [`10_03_capstone_code_review_assistant.ipynb`](./10_03_capstone_code_review_assistant.ipynb) | PR diff 리뷰 + HITL merge 차단 | 03, 07, 08 |
| [`10_04_capstone_data_analyst.ipynb`](./10_04_capstone_data_analyst.ipynb) | CSV 질의 (샌드박스 vs 허용목록) | 03, 07, 08 |
| [`10_05_capstone_customer_support_router.ipynb`](./10_05_capstone_customer_support_router.ipynb) | 티켓 라우팅 + HITL 발송 | 06, 07, 08 |
| [`10_06_capstone_personal_agent_hermes_minimal.ipynb`](./10_06_capstone_personal_agent_hermes_minimal.ipynb) | ledger + skill 2개 | 05, [`implementations/hermes-agent`](../../implementations/hermes-agent) |
| [`10_07_capstone_production_harness.ipynb`](./10_07_capstone_production_harness.ipynb) | eval·CI·`capstone_runner` 통합 | 07, 08 |

**권장 순서:** 팀 시나리오에 맞는 `10_01`~`10_06` 중 **하나**를 끝낸 뒤 `10_07`로 운영화합니다.

---

## 회귀 실행 (선택)

```bash
python recipes/track10_ax_capstones/capstone_runner.py
python recipes/track10_ax_capstones/capstone_runner.py --capstone 02 --write-report
```

---

## AX 시나리오 빠른 선택

| 업무 | 캡스톤 |
|------|--------|
| 조직 KB / 정책 QA | `10_01` |
| 회의록·문서 가공 | `10_02` |
| 코드 리뷰 | `10_03` |
| CSV·데이터 질의 | `10_04` |
| 고객 응대 | `10_05` |
| 개인 비서 | `10_06` |
| 운영·CI | `10_07` |

전체 매핑: [`recipes/README.md` Section#6](../README.md#6-ax-시나리오--노트북-조합-매핑)
