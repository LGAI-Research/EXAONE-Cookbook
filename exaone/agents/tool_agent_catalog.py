"""
(en) Merge multiple ToolAgent tool registries into one LLM tool list and dispatch executor.

Each registry is a logical ToolAgent configuration (e.g. ToolAgent rag, ToolAgent tool).
Logical qualified name: ``{tool_agent_key}.{tool_name}`` (e.g. rag.retrieve).
LLM/API function.name uses ``{tool_agent_key}__{tool_name}`` — dots are rejected by some providers.

(kr) 여러 ToolAgent tool registry를 하나의 LLM tool 목록으로 병합하고 dispatch executor를 제공합니다.

각 registry는 논리적 ToolAgent 구성입니다(예: ToolAgent rag, ToolAgent tool).
논리적 qualified 이름은 ``{tool_agent_key}.{tool_name}`` 형식입니다(예: rag.retrieve).
LLM/API function.name은 ``{tool_agent_key}__{tool_name}`` 형식을 사용합니다(일부 provider는 dot을 거부함).
"""
from __future__ import annotations

import logging
import re
from typing import Any

from exaone.tools import ToolRegistry, tool_failure_payload

logger = logging.getLogger(__name__)

QUALIFIED_SEP = "."
API_TOOL_SEP = "__"
DEFAULT_TOOL_AGENT_KEY = "tool"
ANSWER_TOOL_AGENT_KEY = "answer"
RAG_TOOL_AGENT_KEY = "rag"
MAX_CATALOG_TOOLS = 32
MAX_TOOL_AGENTS = 4

_API_TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def split_qualified_tool_name(name: str) -> tuple[str | None, str]:
    """(en) Split logical ``tool_agent_key.tool_name`` (first dot only).

    (kr) 논리적 ``tool_agent_key.tool_name``을 분리합니다(첫 dot만 기준).
    """
    if QUALIFIED_SEP in name:
        tool_agent_key, tool = name.split(QUALIFIED_SEP, 1)
        return tool_agent_key.strip().lower() or None, tool.strip()
    return None, name.strip()


def qualify_tool_name(tool_agent_key: str, tool_name: str) -> str:
    """(en) Logical qualified name (docs, logs).

    (kr) 논리적 qualified 이름입니다(문서, 로그용).
    """
    return f"{tool_agent_key.strip().lower()}{QUALIFIED_SEP}{tool_name.strip()}"


def to_api_tool_name(tool_agent_key: str, tool_name: str) -> str:
    """(en) Provider-safe function.name for LLM tool schemas and tool_calls.

    (kr) LLM tool schema 및 tool_calls용 provider-safe function.name입니다.
    """
    api = f"{tool_agent_key.strip().lower()}{API_TOOL_SEP}{tool_name.strip()}"
    if not _API_TOOL_NAME_RE.match(api):
        raise ValueError(
            f"API tool name must match [a-zA-Z0-9_-]+, got: {api!r} "
            f"(tool_agent_key={tool_agent_key!r}, tool_name={tool_name!r})"
        )
    return api


def split_tool_name(name: str) -> tuple[str | None, str]:
    """(en) Split API (``key__tool``) or logical (``key.tool``) qualified name.

    (kr) API(``key__tool``) 또는 논리적(``key.tool``) qualified 이름을 분리합니다.
    """
    name = (name or "").strip()
    if API_TOOL_SEP in name:
        tool_agent_key, tool = name.split(API_TOOL_SEP, 1)
        return tool_agent_key.strip().lower() or None, tool.strip()
    return split_qualified_tool_name(name)


def normalize_api_tool_name(
    name: str,
    *,
    default_tool_agent_key: str = DEFAULT_TOOL_AGENT_KEY,
) -> str:
    """(en) Normalize hint/planner/LLM tool name to API-safe qualified form.

    (kr) hint/planner/LLM tool 이름을 API-safe qualified 형식으로 정규화합니다.
    """
    name = (name or "").strip()
    if not name:
        return name
    if API_TOOL_SEP in name:
        key, local = name.split(API_TOOL_SEP, 1)
        return to_api_tool_name(key or default_tool_agent_key, local)
    if QUALIFIED_SEP in name:
        key, local = split_qualified_tool_name(name)
        if key:
            return to_api_tool_name(key, local)
    return to_api_tool_name(default_tool_agent_key, name)


class ToolAgentCatalog:
    """(en) One runtime ToolAgent surface: merged schemas + dispatch by tool_agent_key.

    (kr) 런타임 ToolAgent 단일 표면입니다. 병합 schema와 tool_agent_key 기준 dispatch를 제공합니다.
    """

    def __init__(self) -> None:
        self._registries: dict[str, ToolRegistry] = {}

    def register_tool_agent(self, tool_agent_key: str, registry: ToolRegistry) -> None:
        key = tool_agent_key.strip().lower()
        if not key:
            raise ValueError("tool_agent_key must be non-empty")
        if key in self._registries:
            raise ValueError(f"ToolAgent registry already registered: {key}")
        if len(self._registries) >= MAX_TOOL_AGENTS:
            raise ValueError(f"at most {MAX_TOOL_AGENTS} ToolAgent registries allowed")
        self._registries[key] = registry

    @classmethod
    def from_single_registry(
        cls,
        registry: ToolRegistry,
        *,
        tool_agent_key: str = DEFAULT_TOOL_AGENT_KEY,
    ) -> ToolAgentCatalog:
        cat = cls()
        cat.register_tool_agent(tool_agent_key, registry)
        return cat

    @property
    def tool_agent_keys(self) -> list[str]:
        return list(self._registries.keys())

    def has_tools(self) -> bool:
        return any(len(reg) > 0 for reg in self._registries.values())

    def catalog_tool_names(self) -> list[str]:
        """(en) API-safe names exposed to the LLM and planners.

        (kr) LLM과 planner에 노출되는 API-safe 이름 목록입니다.
        """
        return [e["qualified_name"] for e in self.catalog_entries_for_planner()]

    def catalog_entries_for_planner(self) -> list[dict[str, str]]:
        """(en) Metadata-only catalog rows for NextStepPlanner (API name + description).

        (kr) NextStepPlanner용 메타데이터 전용 catalog 행입니다(API name + description).
        """
        entries: list[dict[str, str]] = []
        for tool_agent_key, reg in self._registries.items():
            for schema in reg.get_schemas():
                fn = schema.get("function") or {}
                local = fn.get("name")
                if not local:
                    continue
                api_name = to_api_tool_name(tool_agent_key, str(local))
                desc = str(fn.get("description") or "").strip()
                entries.append({"qualified_name": api_name, "description": desc})
                if len(entries) >= MAX_CATALOG_TOOLS:
                    return entries
        return entries

    def get_merged_schemas(self) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for tool_agent_key, reg in self._registries.items():
            for schema in reg.get_schemas():
                merged.append(_qualify_schema_for_api(tool_agent_key, schema))
                if len(merged) >= MAX_CATALOG_TOOLS:
                    return merged
        return merged

    def resolve_hint_tool_name(self, name: str, tool_agent_key: str | None) -> str:
        key = (tool_agent_key or DEFAULT_TOOL_AGENT_KEY).strip().lower()
        return normalize_api_tool_name(name, default_tool_agent_key=key)

    def dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        tool_agent_key, local_name = split_tool_name(name)
        if tool_agent_key is None:
            return tool_failure_payload(
                f"Tool name must be qualified as tool_agent_key__tool_name, got: {name!r}"
            )
        reg = self._registries.get(tool_agent_key)
        if reg is None:
            return tool_failure_payload(f"Unknown ToolAgent registry: {tool_agent_key}")
        return reg.execute(local_name, arguments)


def _qualify_schema_for_api(tool_agent_key: str, schema: dict[str, Any]) -> dict[str, Any]:
    import copy

    out = copy.deepcopy(schema)
    fn = out.setdefault("function", {})
    local = fn.get("name")
    if local:
        fn["name"] = to_api_tool_name(tool_agent_key, str(local))
    return out
