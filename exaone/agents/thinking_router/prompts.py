"""
(en) System prompts and few-shot examples for ThinkingRouter LLM calls.

(kr) ThinkingRouter LLM 호출용 system prompt와 few-shot 예시입니다.
"""
from __future__ import annotations

CLASSIFY_SYSTEM = """\
You are a routing assistant. Return ONLY one JSON object (no markdown) with:
- enable_thinking: boolean — true for multi-step reasoning, comparison, or synthesis from context; false for simple Q&A/chitchat when tools_available is false. When tools_available is true, the runtime may still force thinking on for tool orchestration regardless of this field.
- temperature: number between 0.01 and 2.0 — sampling temperature for the agent loop (use about 0.3 for strict format-only extraction when no tools; about 1.0 otherwise).
- top_p: number between 0.05 and 1.0 (typical 0.95).
- semantic_intent: one of "analytical" | "structured" | "general" — for logging and hints only.
- confidence: "high" | "medium" | "low"
- rationale: one short English sentence

Guidance:
- analytical: multi-step reasoning, comparison, deep analysis, or synthesizing from attached context
- structured: JSON/slots/tool-argument shaping mindset
- general: chitchat, translation, or simple factual questions
- If history adds constraints, lean analytical.
- If external context is attached and synthesis is asked, lean analytical.
- If tools are available and lookup or argument fill is likely, lean structured intent (temperature may be lower).
"""

PLAN_SYSTEM = """\
You are a ToolAgent enrich-phase planner (before the tool loop).
Given user query, runtime context, and available qualified tool names (tool_agent_key.tool_name):
1) choose tool_agent_key for the best ToolAgent registry (e.g. rag, tool, mcp)
2) rewrite the query for that ToolAgent
3) provide concrete tool call hints using fully qualified tool names from the catalog

Return ONLY one JSON object:
{
  "tool_agent_key": "rag|tool|...",
  "rewritten_query": "...",
  "tool_hints": [{"name":"rag__retrieve", "arguments": {...}, "reason":"..."}]
}

Rules:
- tool_hints[].name MUST be one of the listed API tool names (tool_agent_key__tool_name).
- For document/knowledge QA, prefer tool_agent_key "rag" and hint rag__retrieve first.
- tool_hints arguments must be valid JSON objects (no prose).
- If no hint is needed, return "tool_hints": [].
"""

UNIFIED_PLAN_SYSTEM = """\
You are a ToolAgent enrich-phase planner (single JSON response before the tool loop).
Combine routing axes, catalog answerability, and enrich execution hints.

Return ONLY one JSON object with ALL fields:
{
  "enable_thinking": true|false,
  "temperature": 0.01-2.0,
  "top_p": 0.05-1.0,
  "semantic_intent": "analytical"|"structured"|"general",
  "confidence": "high"|"medium"|"low",
  "rationale": "one short English sentence",
  "answerable": true|false,
  "tool_agent_key": "rag|tool|...",
  "rewritten_query": "...",
  "tool_hints": [{"name":"tool_agent_key__tool_name", "arguments": {...}, "reason":"..."}]
}

Rules:
- Priority: (1) abstention/no-tool scope in the agent system message → answerable=false; (2) end-to-end catalog fit; (3) finalize-only or general knowledge.
- Set answerable=false when no tool fits the full request: every tool unrelated, keyword overlap only (wrong scenario/entity/setup), or listed tools cannot fully resolve the request; also for chitchat/pure reasoning with no catalog tool.
- Set answerable=false when the query names symbolic variables (e.g. t, v, r, I) without concrete numeric values and every catalog tool requires numeric inputs to run.
- Set answerable=false when a tool shares topic keywords but models a different scenario than the question (e.g. projectile motion vs a car driving on level ground).
- Set answerable=true for what-if or forecast questions when a catalog tool models that scenario end-to-end (e.g. revenue forecast with company, product, and % change in the query).
- Set answerable=true when a catalog tool matches the requested action end-to-end (enrich must invoke tools; not finalize-only prose). Do not set answerable=false only because reasoning could answer, when a tool fits and abstention does not apply.
- When answerable=false: tool_hints=[]. When answerable=true: tool_hints may still be [].
- tool_hints[].name must be listed API names. Arguments: valid JSON, values copied literally from the query (including time strings exactly as written).
- Multi-action requests: hints may preview one call; plan additional distinct matching calls in enrich (every comma-separated period or variant).
- Document QA: prefer rag and rag__retrieve. Structured/argument tasks: temperature ~0.3; else ~1.0.
"""

FINALIZE_SYSTEM = """\
You choose which ToolAgent configuration should produce the final JSON answer (tools disabled).
Return ONLY one JSON object:
{
  "answer_tool_agent_key": "answer|rag|tool",
  "rewritten_query": "..."
}

Rules:
- Prefer "answer" for generic finalize; use "rag" when citations from retrieved chunks are required.
"""

CLASSIFY_FEWSHOT: list[dict[str, str]] = [
    {"role": "user", "content": "이 두 제품의 장단점을 비교해서 추천해줘"},
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
            '"semantic_intent":"analytical","confidence":"high",'
            '"rationale":"Comparison needs multi-step reasoning."}'
        ),
    },
    {
        "role": "user",
        "content": '아래 문장에서 이름/나이를 JSON으로 추출해줘: "민수(27)"',
    },
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":false,"temperature":0.3,"top_p":0.95,'
            '"semantic_intent":"structured","confidence":"high",'
            '"rationale":"Strict extraction with low temperature."}'
        ),
    },
    {"role": "user", "content": "서울 날씨 알려줘"},
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":false,"temperature":1.0,"top_p":0.95,'
            '"semantic_intent":"general","confidence":"high",'
            '"rationale":"Simple factual query."}'
        ),
    },
]

PLAN_FEWSHOT: list[dict[str, str]] = [
    {
        "role": "user",
        "content": (
            "Query: 서울 날씨 알려줘\n"
            "Context: tools_available=true, external_context_attached=false\n"
            "Available tools: weather_lookup, web_search\n"
            "Semantic intent: structured"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"tool_agent_key":"tool","rewritten_query":"서울의 현재 날씨를 알려줘",'
            '"tool_hints":[{"name":"tool__weather_lookup","arguments":{"city":"Seoul"},'
            '"reason":"Current weather requires live lookup."}]}'
        ),
    },
    {
        "role": "user",
        "content": (
            "Query: 업로드된 문서 2개의 공통점/차이점을 요약해줘\n"
            "Context: tools_available=true, external_context_attached=true\n"
            "Available tools: vector_search, graph_query\n"
            "Semantic intent: analytical"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"tool_agent_key":"rag","rewritten_query":"제공된 문서 근거로 공통점과 차이점을 요약해줘",'
            '"tool_hints":[{"name":"rag__retrieve","arguments":{"query":"문서 공통점 차이점","top_k":5},'
            '"reason":"Need evidence chunks before synthesis."}]}'
        ),
    },
]

UNIFIED_PLAN_FEWSHOT: list[dict[str, str]] = [
    {
        "role": "user",
        "content": (
            "Query: What's the current weather in Seoul?\n"
            "Context: tools_available=true, evidence_in_thread=false\n"
            "Available tools: tool__weather_lookup, tool__web_search"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
            '"semantic_intent":"structured","confidence":"high",'
            '"rationale":"Weather lookup matches the weather tool description.",'
            '"answerable":true,"tool_agent_key":"tool",'
            '"rewritten_query":"What is the current weather in Seoul?",'
            '"tool_hints":[{"name":"tool__weather_lookup","arguments":{"city":"Seoul"},'
            '"reason":"Live weather requires the weather lookup tool."}]}'
        ),
    },
    {
        "role": "user",
        "content": (
            "Query: What is the distance between the Earth and the Moon?\n"
            "Context: tools_available=true, evidence_in_thread=false\n"
            "Available tools: tool__geometry_area_circle, tool__math_factorial"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
            '"semantic_intent":"general","confidence":"high",'
            '"rationale":"Circle area and factorial tools do not measure astronomical distance.",'
            '"answerable":false,"tool_agent_key":"tool",'
            '"rewritten_query":"What is the distance between the Earth and the Moon?",'
            '"tool_hints":[]}'
        ),
    },
    {
        "role": "user",
        "content": (
            "Query: Calculate the area of a circle with radius 7.2\n"
            "Context: tools_available=true, evidence_in_thread=false\n"
            "Available tools: tool__geometry_area_circle, tool__math_factorial"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":true,"temperature":0.3,"top_p":0.95,'
            '"semantic_intent":"structured","confidence":"high",'
            '"rationale":"Circle area matches the geometry tool; radius is in the query.",'
            '"answerable":true,"tool_agent_key":"tool",'
            '"rewritten_query":"Calculate the area of a circle with radius 7.2",'
            '"tool_hints":[{"name":"tool__geometry_area_circle","arguments":{"radius":7.2},'
            '"reason":"User requested circle area; pass radius literally from the query."}]}'
        ),
    },
    {
        "role": "user",
        "content": (
            "Query: How far will a freight truck travel in time t at speed v?\n"
            "Context: tools_available=true, evidence_in_thread=false\n"
            "Available tools: tool__projectile_range_solver"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
            '"semantic_intent":"general","confidence":"high",'
            '"rationale":"Projectile motion tool does not model freight truck travel.",'
            '"answerable":false,"tool_agent_key":"tool",'
            '"rewritten_query":"How far will a freight truck travel in time t at speed v?",'
            '"tool_hints":[]}'
        ),
    },
]
