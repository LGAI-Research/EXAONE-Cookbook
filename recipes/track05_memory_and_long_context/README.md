# Track 05 — Memory & Long Context

> **긴 대화·큰 툴 결과·세션 간 유지** — context budget 압축과 ledger/artifact 2계층 메모리.
> Agent Learning Hub 매핑: **Stage 2** (일부) + **Stage 3** (context compaction).

---

## 학습 목표

- [ ] `CORE_CONTEXT_LENGTH_*` 와 `input + max_new_tokens` 예산을 `exaone.context_management` 로 계산·검증한다.
- [ ] 긴 회의록 멀티턴을 `compress_messages_for_turn` / `hard_cap_messages` 로 줄인다.
- [ ] `CONTEXT_TOOL_VERBATIM_MAX_TOKENS` 로 tool run 원문 cap 을 이해한다.
- [ ] `InMemoryLedger` + `InMemoryArtifactStore` + `store_large_tool_result` 패턴을 쓴다.
- [ ] 같은 `session_id` JSON 스냅샷으로 노트북 재실행 시 ledger 를 복원한다.

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()
# (en) CONTEXT_TOOL_VERBATIM_MAX_TOKENS lives in constants — import the submodule once in Setup.
# (kr) CONTEXT_TOOL_VERBATIM_MAX_TOKENS 는 constants 에 있으므로 Setup 에서 서브모듈을 한 번 import 한다.
import exaone.context_management.constants

tokens = exaone.context_management.estimate_tokens_from_messages(messages)
tool_cap = exaone.context_management.constants.CONTEXT_TOOL_VERBATIM_MAX_TOKENS
artifacts, ledger = exaone.memory.default_memory_pair()
exaone.memory.store_large_tool_result(
    result={...},
    artifacts=artifacts,
    ledger=ledger,
    tool_name="analytics_export",
)
```

모든 코드 셀은 `from exaone.* import ...` 없이 `exaone.memory.*`, `exaone.context_management.*` 점 접근만 사용합니다. [`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade).

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`05_memory_and_long_context_lab.ipynb`](./05_memory_and_long_context_lab.ipynb) | Session 1~2 — 컨텍스트 예산·압축 · Memory Ledger·세션 스냅샷 | `_out/compaction_report.json`, `_out/session_state.json` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `compaction_report.json` — 턴별 토큰·압축 전후 diff (LLM 없이도 budget/hard-cap 셀 통과).
- [ ] `session_state.json` 을 지운 뒤 1회 실행 → 재실행 시 ledger `entry_count` 가 이어진다.

---

## 선수

- **Track 02** (`ToolAgent` 루프)
- **Track 04** (context budget 맛보기) — 권장

## 다음 트랙

- **Track 06** — 멀티 에이전트 조율
- **Track 10 `10_06`** — Personal Agent (ledger 영속)

---

## 문제 해결

- `validate_input_tokens` 에러 → `prepare_messages_for_llm_chat` / `hard_cap_messages` 순으로 줄여 보기.
- `store_large_tool_result` 가 None → payload 가 `CORE_MEMORY_TOOL_RESULT_MIN_BYTES` 미만.
- 세션 복원 실패 → `_out/session_state.json` 경로·`session_id` 일치 확인.
