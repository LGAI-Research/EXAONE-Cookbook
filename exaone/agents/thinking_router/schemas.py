"""
(en) JSON schema response_format definitions for ThinkingRouter LLM calls.

(kr) ThinkingRouter LLM 호출용 JSON schema response_format 정의입니다.
"""
from __future__ import annotations

from typing import Any

_SEMANTIC_INTENTS = ("analytical", "structured", "general")

TOOL_HINT_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "arguments", "reason"],
    "properties": {
        "name": {"type": "string"},
        "arguments": {"type": "object"},
        "reason": {"type": "string"},
    },
}

ROUTER_OUTPUT_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "agent_response",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["answer", "confidence"],
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
}

CLASSIFY_JSON_SCHEMA: dict[str, Any] = {
    "name": "route_axes",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "enable_thinking",
            "temperature",
            "top_p",
            "semantic_intent",
            "confidence",
            "rationale",
        ],
        "properties": {
            "enable_thinking": {"type": "boolean"},
            "temperature": {"type": "number", "minimum": 0.01, "maximum": 2.0},
            "top_p": {"type": "number", "minimum": 0.05, "maximum": 1.0},
            "semantic_intent": {
                "type": "string",
                "enum": list(_SEMANTIC_INTENTS),
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "rationale": {"type": "string"},
        },
    },
}

CLASSIFY_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": CLASSIFY_JSON_SCHEMA,
}

PLAN_JSON_SCHEMA: dict[str, Any] = {
    "name": "route_plan_enrich",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["tool_agent_key", "rewritten_query", "tool_hints"],
        "properties": {
            "tool_agent_key": {"type": "string"},
            "rewritten_query": {"type": "string"},
            "tool_hints": {
                "type": "array",
                "items": TOOL_HINT_ITEM_SCHEMA,
            },
        },
    },
}

PLAN_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": PLAN_JSON_SCHEMA,
}

UNIFIED_PLAN_JSON_SCHEMA: dict[str, Any] = {
    "name": "route_plan_enrich_unified",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "enable_thinking",
            "temperature",
            "top_p",
            "semantic_intent",
            "confidence",
            "rationale",
            "answerable",
            "tool_agent_key",
            "rewritten_query",
            "tool_hints",
        ],
        "properties": {
            "enable_thinking": {"type": "boolean"},
            "temperature": {"type": "number", "minimum": 0.01, "maximum": 2.0},
            "top_p": {"type": "number", "minimum": 0.05, "maximum": 1.0},
            "semantic_intent": {
                "type": "string",
                "enum": list(_SEMANTIC_INTENTS),
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "rationale": {"type": "string"},
            "answerable": {"type": "boolean"},
            "tool_agent_key": {"type": "string"},
            "rewritten_query": {"type": "string"},
            "tool_hints": {
                "type": "array",
                "items": TOOL_HINT_ITEM_SCHEMA,
            },
        },
    },
}

UNIFIED_PLAN_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": UNIFIED_PLAN_JSON_SCHEMA,
}

FINALIZE_JSON_SCHEMA: dict[str, Any] = {
    "name": "route_plan_finalize",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["answer_tool_agent_key", "rewritten_query"],
        "properties": {
            "answer_tool_agent_key": {"type": "string"},
            "rewritten_query": {"type": "string"},
        },
    },
}

FINALIZE_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": FINALIZE_JSON_SCHEMA,
}
