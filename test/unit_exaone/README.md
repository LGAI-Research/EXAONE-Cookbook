# Exaone 테스트 시나리오 (test/unit_exaone)

`exaone` 모듈의 context_management 및 에이전트 연동 시나리오입니다.

## 실행

```bash
# 프로젝트 루트에서
pytest test/unit_exaone/ -v
```

- **test_context_management.py**: `exaone.context_management` 단위 테스트  
  - 인풋+생성 예약 검사(`validate_input_tokens`), `max_input_tokens_for_context`, 아웃풋 캡, `ensure_input_within_limit`, `compress_messages_for_turn` (LLM mock)
- **test_agents_context.py**: exaone 에이전트의 context_management 연동 시나리오  
  - `input+reserved` > max → 에러, recommended 예산 초과 → 압축, `ensure`/`compress`에 `reserved_new_tokens` 전달, 멀티턴 후 압축  
  - for-loop 기반 reason→tool 루프 동작 검증
- **test_thinking_router.py**: `ThinkingRouter` — 축 JSON(`semantic_intent` 등), `RoutePlan` / 캐시, `exaone.agents` export
