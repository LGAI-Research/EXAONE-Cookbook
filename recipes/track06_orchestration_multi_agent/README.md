# Track 06 — Orchestration & Multi-Agent

> **멀티 에이전트는 조율(coordination) 문제**입니다 — 언제 단일 `ToolAgent` 가 낫고, 언제 역할을 나누는지를 비교합니다.
> Agent Learning Hub 매핑: **Stage 4** (조율·멀티 에이전트).

---

## 학습 목표

- [ ] **planner → executor → critic** 3롤 워크플로를 *명시적* 오케스트레이션으로 돌리고 트레이스를 남긴다.
- [ ] `ThinkingRouter` 로 입력을 **서브 에이전트 프로필**(FAQ / 데이터 / 코드리뷰)에 핸드오프한다.
- [ ] 같은 문제를 **단일 vs 멀티** 로 비교해 의사결정 트리 초안을 만든다.

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()
client = exaone.llm.ExaoneAPIClient(...)
router = exaone.agents.ThinkingRouter(client=client, model=client.model)
planner = exaone.agents.NextStepPlanner(client, client.model)
agent = exaone.agents.ToolAgent(tool_registry=registry, use_next_step_planner=True)
result = agent.run(exaone.agents.AgentContext(query="..."), llm=client)
```

전체 규칙: [`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade).

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`06_orchestration_lab.ipynb`](./06_orchestration_lab.ipynb) | Session 1~3 — Planner·Executor·Critic · 라우터 핸드오프 · 단일 vs 멀티 비교 | `_out/workflow_trace.json`, `_out/routing_table.json`, `_out/comparison.json`, `_out/decision_tree.md` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `workflow_trace.json` 에 `planner` / `executor` / `critic` 단계의 success·latency 와 executor 의 `stop_reason` 이 있다.
- [ ] `routing_table.json` 에 20건 입력 × `semantic_intent` × `chosen_profile` 이 있다.
- [ ] `decision_tree.md` 에 “단일 agent” / “멀티 롤” 선택 기준이 5줄 이상 서술되어 있다.

---

## 선수

- **Track 02** — `ToolAgent`, `AgentContext` / `AgentResult`
- **Track 03** — `ToolRegistry` (executor 도구)
- **Track 01** — `ThinkingRouter` / `RouteDecision` 맛보기

## 다음 트랙

- **Track 07** — HITL·관측 (workflow trace 필드가 관측으로 연결)
- **Track 09** — LangGraph 로 같은 조율 문제를 다른 하니스로 비교
- **Track 10 캡스톤** — Session 3 의사결정 트리로 캡스톤 유형 선택

---

## 문제 해결

- planner JSON 파싱 실패 → `exaone.output.StructuredOutputPipeline` 또는 `response_format=json_object` 지원 여부 확인.
- executor 가 도구를 안 부름 → `lookup_policy` 스키마·시스템 프롬프트에 “반드시 도구로 조회” 문구 확인.
- router 가 전부 `general` → 입력 문체·길이를 Track 01 Session 5 처럼 더 다양하게 (`data/routing_inputs.jsonl` 참고).
