# Track 07 — Safety, HITL & Observability

> 에이전트가 실수해도 **운영 리스크를 줄이기** — 사람 승인, 외부에서 온 텍스트 정화, 구조화 로그, SLO.
> Agent Learning Hub 매핑: **Stage 7** (안전·관측).

---

## 학습 목표

- [ ] 위험 도구(`sensitive_publish`) 실행 전 **HITL 승인·거절** 흐름을 재현한다.
- [ ] RAG/툴/로그에 섞인 **프롬프트 인젝션 페이로드** 를 sanitize·마스킹한다.
- [ ] `ToolAgent` 메타데이터를 **observability 필드** 규약에 맞춰 JSONL 트레이스로 남긴다.
- [ ] 팀용 **SLOSpec** + `production_defaults` 권장값을 문서화한다.

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()
# HITL / tools
registry = exaone.tools.ToolRegistry()
# Safety
clean = exaone.context_management.sanitize_untrusted_reference_text(raw)
safe_log = exaone.observability.sanitize_for_log(payload)
# SLO
slo = exaone.observability.SLOSpec(name="agent-api", p95_chat_latency_ms=8000)
```

[`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade)

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`07a_safety_and_observability_lab.ipynb`](./07a_safety_and_observability_lab.ipynb) | Session 1~4 — HITL · prompt injection · 관측 trace | `_out/hitl_trace.json`, `_out/injection_defense.json`, `_out/session_trace.jsonl`, `_out/field_glossary.md` |
| [`07b_slo_production_defaults.ipynb`](./07b_slo_production_defaults.ipynb) | **심화** SLOSpec · production 권장 env | `_out/slo_spec.json`, `_out/recommended_env.md` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 선수

- **Track 03** — `ToolRegistry`, `ToolResult`
- **Track 02** — `ToolAgent` 메타데이터
- (권장) **Track 04** — untrusted chunk 맥락

## 다음 트랙

- **Track 08** — M1~M9 평가
- **Track 10** — SLO 심화 노트북이 캡스톤 통과 기준
