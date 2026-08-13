# Track 02 — Minimum Agent Loop

> 에이전트는 **`observe → think → act → observe` 제어 루프**입니다. 이 트랙에서는 루프를 직접 구현한 뒤, 같은 일을 `exaone.agents.ToolAgent`가 어떤 구조로 처리하는지 분해해 봅니다.
> Agent Learning Hub 매핑: **Stage 1** (최소 루프) + **Stage 3** 입문 (하니스 분해).

---

## 학습 목표

- [ ] 도구 한두 개로 동작하는 에이전트를 **120줄 안에 직접** 짜본다 (프레임워크 없이).
- [ ] 같은 문제를 `exaone.agents.ToolAgent`로 다시 풀고 **줄 단위로 비교**한다.
- [ ] 에이전트의 *중간 사고 / 도구 호출 / 최종 답* 을 **SSE 채널별로 나눠** 콘솔에서 확인한다.
- [ ] `BaseAgent → ToolAgent → NextStepPlanner → ThinkingRouter`의 **책임 분담**을 한 그림으로 정리한다.

---

## 코드 시작 패턴 (facade)

Session 1에서는 **프레임워크 없이** `exaone.llm`만 쓰고, 이후 Session에서 `ToolAgent` 하니스를 사용합니다.

```python
import exaone

exaone.load_project_env()
client = exaone.llm.ExaoneAPIClient(...)
registry = exaone.tools.ToolRegistry()
registry.register(exaone.tools.Tool(name="convert_money", ...))
agent = exaone.agents.ToolAgent(tool_registry=registry, ...)
result = agent.run(exaone.agents.AgentContext(query="..."), llm=client)
```

스트리밍은 `for ev in agent.run_stream(ctx, llm=client):` → `exaone.agents.agent_event_to_sse(ev)` 흐름으로 확인합니다. 자세한 시작 패턴은 [`recipes/README.md` 4.1절](../README.md#41-코드-시작-패턴--import-exaone-facade)을 참고하세요.

**K-EXAONE 2.0:** `ToolAgent` 루프는 **agentic 멀티턴**입니다. `enable_thinking=True`와 `preserve_thinking=True`를 **명시**하세요(환경 변수 또는 `eval/exaone_api_kwargs.py`). payload에는 항상 실리며, **효과**는 K-EXAONE 2.0+ — 1.0은 무시합니다. chitchat·단발 QA는 둘 다 `False`(Track 01). → [`docs/k_exaone_2.md`](../../docs/k_exaone_2.md)

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`02a_minimum_agent_loop_lab.ipynb`](./02a_minimum_agent_loop_lab.ipynb) | Session 1~3 — 손코딩 루프 · ToolAgent 비교 · SSE 스트리밍 | `_out/loop_trace.json`, `_out/comparison.json`, `_out/stream_trace.jsonl`, `_out/stream.sse.txt` |
| [`02b_harness_anatomy.ipynb`](./02b_harness_anatomy.ipynb) | **심화** harness 5가지 결정 그리드 해부 | `_out/anatomy_matrix.json`, `_out/sequence_*.md`, `_out/checklist.md` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `_out/loop_trace.json` — 손코딩 루프 trace 5건 저장.
- [ ] `_out/comparison.json` — scratch / tool_agent_full / tool_agent_minimal의 핵심 정답 토큰 포함 여부.
- [ ] `_out/stream_trace.jsonl` — `run_start` … `run_end` 이벤트 각 1회 이상.
- [ ] `_out/anatomy_matrix.json` (심화) — `many_tools`에서 strict 3종은 예산 차단으로 F가 되고, `summary.pass_rate_by_harness.bare == 1.0` 이며 full/no_router/no_planner는 1.0보다 낮은지 확인 (안전 예산이 완성도를 좌우).

---

## 다음 트랙

- **Track 03 — Tools & MCP**: `ToolRegistry` 위에서 *안전한 도구 정의*와 MCP 프로토콜을 다룹니다.
- **Track 06 — Multi-Agent**: 단일 에이전트의 한계가 보이면 *router + sub-agent* 구조로 확장합니다.
- **Track 07 — Observability**: Session 3의 SSE 이벤트를 운영 트레이싱의 기본 단위로 사용합니다.
- **Track 08 — Evaluation**: `comparison.json` 형식이 회귀 테스트의 기본 단위.

---

## 문제 해결

- Session 1에서 `tool_calls`가 오지 않으면: Track 01 Session 4 가이드를 그대로 따릅니다. 모델과 base_url이 OpenAI 호환 `tools`를 지원해야 합니다.
- Session 2에서 `ToolAgent.run`이 빈 답을 내면: `verbose=True`로 enrich/finalize 단계를 확인합니다.
- Session 3의 SSE 출력이 너무 빠르면: `stream_enrich_reasoning=False`로 reasoning 채널을 끕니다.
- 심화 harness의 차이가 잘 보이지 않으면: safety 효과는 `many_tools`의 `b`·`P/F`, planner/router 비용은 `l`(LLM 호출 수) 열에서 확인합니다. 그래도 차이가 약하면 다단계 추론(ANALYTICAL) 질의를 추가하세요.
