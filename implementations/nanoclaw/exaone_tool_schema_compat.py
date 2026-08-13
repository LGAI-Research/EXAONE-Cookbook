"""
(en) EXAONE OpenAI-compatible tool schema probes for NanoClaw / OpenCode integration.

(kr) NanoClaw / OpenCode 연동용 EXAONE OpenAI-compatible tool schema 프로브.

Friendli EXAONE rejects nested ``oneOf`` in tool parameter schemas (HTTP 422) but
accepts ``anyOf``. OpenCode built-in tools may emit ``oneOf``; cookbook vendor
pins ``@ai-sdk/openai-compatible`` and documents this subset for upstream fixes.
"""
from __future__ import annotations

import os
from typing import Any

import requests

ONEOF_REJECTED_MESSAGE = "'oneOf' with multiple schemas is not supported"


def chat_completions_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def ssl_verify_from_env() -> bool:
    raw = os.environ.get("DISABLE_SSL_VERIFY", "").strip().lower()
    return raw not in ("1", "true", "yes")


def tool_function_schema(parameters: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "schema_probe",
                "description": "cookbook schema compatibility probe",
                "parameters": parameters,
            },
        }
    ]


def nested_oneof_parameters() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "number"},
                ]
            }
        },
    }


def nested_anyof_parameters() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                ]
            }
        },
    }


def post_tool_schema_probe(
    *,
    base_url: str,
    api_key: str,
    model: str,
    parameters: dict[str, Any],
    timeout_s: float = 60.0,
) -> requests.Response:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "reply with ok"}],
        "tools": tool_function_schema(parameters),
        "max_tokens": 8,
    }
    return requests.post(
        chat_completions_url(base_url),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout_s,
        verify=ssl_verify_from_env(),
    )
