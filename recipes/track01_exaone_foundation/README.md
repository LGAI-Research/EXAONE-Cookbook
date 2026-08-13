# Track 01 — EXAONE Foundation

> EXAONE 모델 기본기. Track 00 다음.

---

## 학습 목표

- [ ] 각 Session 단계 **출력 해석** 셀을 읽고 정상 여부를 판단한다.
- [ ] 멀티턴·스트리밍에서 `prompt_tokens` 증가를 본다.
- [ ] JSON 스키마·함수 호출·ThinkingRouter 를 각각 한 번씩 돌려본다.

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`01_exaone_foundation_lab.ipynb`](./01_exaone_foundation_lab.ipynb) | Session 1~5 — `### Session N-M` 로직 단계별 코드 셀 | `_out/*.json`, `korean_golden.jsonl` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

**`data/`:** `korean_golden_seed.jsonl`, `meeting_minutes_samples.json`, `minutes_prompt.json`, `action_item_schema.json`, `multi_turn_turns.json` (**Session 1 `turn_cfg`** — 파이썬 동시성 3턴 + 스트리밍 1질문), `structured_output_samples.json`, `exchange_rates.json`, `fc_demo.json`, `router_queries.json`

---

## 시작 패턴

```python
import exaone
exaone.load_project_env()
client = exaone.integrations.build_llm_from_env()
resp = client.chat([exaone.llm.ExaoneMessage(role="user", content="안녕")])
```

---

## 체크포인트

- [ ] setup `model:` 출력
- [ ] Session 1: `prompt_tokens` 증가, 스트림 한 줄
- [ ] `_out/multi_turn.json`, `korean_golden.jsonl`, `action_items.json`, `tool_loop_trace.json`, `route_comparison.json`

---

## 문제 해결

- API 키 없음 → Track 00
- `tool_calls` 비어 있음 → 모델이 function calling 지원하는지 확인
- JSON 스키마 실패 → `response_format` 지원 여부 확인

---

## K-EXAONE 2.0 · `enable_thinking` / `preserve_thinking`

이 트랙의 Session 1·2·3·4는 **단발 호출·잡담·JSON** 데모이므로 노트북에서 `ExaoneGenerateOptions(enable_thinking=False, …)` 를 씁니다. 지연과 토큰을 아끼는 패턴입니다.

Session 5 **ThinkingRouter**는 질문 유형에 따라 thinking on/off를 **라우팅**합니다. Track 02 **`ToolAgent` 멀티턴 루프**처럼 **agentic** 워크플로로 넘어가면 `enable_thinking=True`와 `preserve_thinking=True`를 **명시**하세요 — **효과**는 K-EXAONE 2.0+에서 reasoning trace가 유지됩니다.

| 상황 | `enable_thinking` | `preserve_thinking` |
|------|-------------------|---------------------|
| 이 트랙 chitchat · JSON · FC 데모 | `False` | `False` |
| Track 02+ ToolAgent / eval agentic | `True` | **`True`** (효과는 2.0+) |

`exaone.llm` 클라이언트는 `enable_thinking`만 설정합니다. `preserve_thinking`은 eval glue(`eval/exaone_api_kwargs.py`) 또는 `extra_body`로 **명시**합니다 — 모델 id 추측 없이 설정값을 payload에 그대로 실립니다. 상세: [`docs/k_exaone_2.md`](../../docs/k_exaone_2.md).
