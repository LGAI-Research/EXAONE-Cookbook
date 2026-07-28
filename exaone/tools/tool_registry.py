"""
(en) Tool registry: register Tools by name, expose schema list and unified executor.
Agents inject only the registry and use get_schemas() / execute(name, args).

(kr) 도구 등록소 모듈이다. 이름별 Tool 등록 후 스키마 리스트·통합 실행자를 제공한다.
에이전트는 registry만 주입받으면 get_schemas() / execute(name, args)로 사용한다.
"""
from __future__ import annotations

import logging
from typing import Any

import jsonschema

from exaone.tools.base import Tool
from exaone.tools.results import tool_failure_payload

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    (en) Tool registration and lookup.
    - register(tool): add Tool (ValueError on duplicate name)
    - get_schemas(): tools list for the LLM
    - execute(name, arguments): run the tool registered under name

    (kr) 도구 등록 및 조회 클래스이다.
    - register(tool): Tool 추가(이름 중복 시 ValueError)
    - get_schemas(): LLM에 넘길 tools 리스트
    - execute(name, arguments): name에 해당하는 도구 실행
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    @staticmethod
    def _validate_schema(schema: dict[str, Any], tool_name: str) -> None:
        if "type" not in schema or schema["type"] != "function":
            raise ValueError("Tool schema must have type='function'")
        fn = schema.get("function", {})
        if "name" not in fn:
            raise ValueError("Tool schema.function must have 'name'")
        schema_name = fn["name"]
        if schema_name != tool_name:
            raise ValueError(
                f"Tool name '{tool_name}' does not match schema function.name '{schema_name}'"
            )

    def register(self, tool: Tool) -> None:
        """
        (en) Register a tool by name.

        (kr) 도구를 이름으로 등록한다.
        """
        schema = tool.to_schema_dict()
        self._validate_schema(schema, tool.name)
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """
        (en) Remove a tool by name; returns True if it existed.

        (kr) 이름으로 도구를 제거하며 있으면 True를 반환한다.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Tool | None:
        """
        (en) Look up a tool by name.

        (kr) 이름으로 도구를 조회한다.
        """
        return self._tools.get(name)

    def get_schemas(self) -> list[dict[str, Any]]:
        """
        (en) Tools list for LLM/ExaoneClient (registration order preserved).

        (kr) LLM/ExaoneClient에 넘길 tools 리스트를 반환한다(순서 유지).
        """
        return [t.to_schema_dict() for t in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """
        (en) Run the registered tool with (name, arguments).
        Same signature as tool_executor in base_agent._run_reason_tool_loop.

        (kr) (name, arguments)로 등록된 도구를 실행한다.
        base_agent._run_reason_tool_loop의 tool_executor 시그니처와 동일하다.
        """
        tool = self._tools.get(name)
        if tool is None:
            return tool_failure_payload(f"Unknown tool: {name}", guidance=None)
        params_schema = tool.schema.get("function", {}).get("parameters")
        if params_schema:
            try:
                jsonschema.validate(arguments, params_schema)
            except jsonschema.ValidationError as e:
                return tool_failure_payload(f"Invalid arguments: {e.message}", guidance=None)
        try:
            return tool.run(arguments)
        except Exception as e:
            logger.exception("Tool execution failed: %s", name)
            return tool_failure_payload(str(e))

    def __len__(self) -> int:
        return len(self._tools)
