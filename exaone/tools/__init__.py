"""
(en) Tool abstraction: Tool definition, ToolRegistry, and failure payloads.

Agents may inject a single ToolRegistry instead of a tools list plus tool_executor.
On custom tool_executor failure: raise or return tool_failure_payload().

(kr) 도구 추상화 패키지이다. Tool 정의, ToolRegistry, 실패 payload를 제공한다.

에이전트는 tools 리스트 + tool_executor 대신 ToolRegistry 하나로 주입할 수 있다.
커스텀 tool_executor 실패 시 예외를 던지거나 tool_failure_payload()를 반환한다.
"""
from exaone.tools.base import Tool, tool_from_callable, tool_from_typed_callable
from exaone.tools.results import (
    tool_executor_return_indicates_error,
    tool_failure_payload,
    tool_failure_payload_json,
)
from exaone.tools.tool_registry import ToolRegistry
from exaone.tools.tool_result import ToolOutcome, ToolResult, ToolResultModel

__all__ = [
    "Tool",
    "tool_from_callable",
    "tool_from_typed_callable",
    "ToolRegistry",
    "ToolOutcome",
    "ToolResult",
    "ToolResultModel",
    "tool_failure_payload",
    "tool_failure_payload_json",
    "tool_executor_return_indicates_error",
]
