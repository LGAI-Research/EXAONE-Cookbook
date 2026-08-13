# Agents

Single runtime: **`ToolAgent`** (`BaseAgent` ReAct loop). Multiple **ToolAgent configurations** (separate tool registries) can be merged in one run via **`ToolAgentCatalog`**.

Optional **`ThinkingRouter`** + **`NextStepPlanner`**:

1. **`ThinkingRouter.plan_enrich_unified`** — axes + `answerable` + `tool_agent_key` + `tool_hints` in one LLM call (falls back to classify + `plan_enrich` on parse failure)  
2. **`NextStepPlanner.screen_catalog`** — can any registered tool help? (LLM only if Router is **off**)  
3. **`NextStepPlanner.evaluate_progress`** — after each enrich turn (full messages + ledger; LLM JSON only)  
4. **`ThinkingRouter.plan_finalize`** — `answer_tool_agent_key`, tools-off JSON answer (reuses enrich axes; no second classify when enrich ran)  

Duplicate tool calls are blocked deterministically via **`ToolInvocationLedger`** (canonical JSON args). No regex/content heuristics for stop decisions.

**`AgentResult.metadata["llm_calls"]`**: per-run LLM call log (`phase`, `schema_name`, `latency_ms`, …) via **`run_trace`** — use to audit or remove redundant planner/router calls.

There is no `RAGAgent` class. Document QA = **ToolAgent (rag)** with `rag.retrieve`.

## Naming

| Concept | Meaning |
|---------|---------|
| **ToolAgent** | The class you instantiate and call `.run()` on |
| **ToolAgent (tool)** | Configuration with general tools (`tool_agent_key=tool`) |
| **ToolAgent (rag)** | Configuration with retrieval tools (`tool_agent_key=rag`) |
| **ToolAgent A / B** | Informal labels in docs for two registries, e.g. A=tool, B=rag |

LLM tool names: **`{tool_agent_key}__{tool_name}`** (e.g. `rag__retrieve`, `tool__web_search`). Logical form `rag.retrieve` is accepted at dispatch for hints/logs.

## Examples

```python
from exaone.agents import ToolAgent, AgentContext, build_rag_tool_registry, RAG_TOOL_AGENT_KEY

# ToolAgent (rag) only
agent = ToolAgent(
    tool_agent_registries={RAG_TOOL_AGENT_KEY: build_rag_tool_registry(strategy)},
    system_prompt=DEFAULT_SYSTEM_PROMPT_RAG,
)

# ToolAgent (tool) only
agent = ToolAgent(tool_registry=registry)

result = agent.run(AgentContext(query="..."), llm=llm)
```

## Flow

- No eager retrieval at `run()` — **ToolAgent (rag)** uses `rag.retrieve` in the enrich phase.  
- One `ToolAgent` instance, merged catalog, enrich → evaluate → finalize.

## K-EXAONE 2.0 · reasoning across turns

`ToolAgent` enrich 루프는 **멀티턴 agentic** 워크플로입니다. `enable_thinking=True`와 `preserve_thinking=True`를 **명시**하세요 — **효과**는 K-EXAONE 2.0+에서 이전 턴 `reasoning_content`가 유지됩니다. 끄면 턴마다 reasoning이 리셋되어 도구 선택·계획이 흔들립니다.

| 워크플로 | `enable_thinking` | `preserve_thinking` |
|----------|-------------------|---------------------|
| chitchat · 단발 Q&A | `False` | `False` |
| **ToolAgent / agentic eval** | `True` | **`True`** (효과는 K-EXAONE 2.0+) |

- **`exaone` 패키지**: `ExaoneGenerateOptions.enable_thinking`만 설정합니다. `preserve_thinking`은 `eval/exaone_api_kwargs.py` 또는 `extra_body`로 **명시**합니다 — payload에는 항상 실리며, 1.0 배포에서는 무시됩니다.

→ [`docs/k_exaone_2.md`](../../docs/k_exaone_2.md)
