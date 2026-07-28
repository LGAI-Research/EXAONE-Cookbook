"""
(en) Tool abstraction: bundles the schema passed to the LLM and the execute function in one unit.

(kr) 도구 추상 정의 모듈이다. LLM에 넘길 스키마와 실행 함수를 하나의 단위로 묶는다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    """
    (en) Single tool: OpenAPI/Hermes schema plus execute function.
    - schema: tool definition for LLM/API (type, function.name, function.description, function.parameters)
    - execute: (arguments: dict) -> result; name is fixed by schema name

    (kr) 단일 도구로 OpenAPI/Hermes 스키마와 실행 함수로 구성된다.
    - schema: LLM/API에 넘기는 도구 정의(type, function.name, function.description, function.parameters)
    - execute: (arguments: dict) -> 결과이며 이름은 스키마의 name으로 고정된다.
    """

    name: str
    schema: dict[str, Any]
    execute: Callable[[Any], Any]
    input_model: type[Any] | None = None
    input_parser: Callable[[dict[str, Any]], Any] | None = None

    def to_schema_dict(self) -> dict[str, Any]:
        """
        (en) Return the dict entry as-is for the LLM tools list.

        (kr) LLM tools 리스트에 넣을 항목을 그대로 반환한다.
        """
        return self.schema

    def run(self, arguments: dict[str, Any]) -> Any:
        """
        (en) Invoke this tool's execute (optionally parsing dict into structured input).

        (kr) 이 도구의 execute를 호출한다(필요 시 dict를 구조화 입력으로 변환).
        """
        payload: Any = arguments
        if self.input_parser is not None:
            payload = self.input_parser(arguments)
        elif self.input_model is not None:
            payload = self.input_model(**arguments)
        return self.execute(payload)


def tool_from_callable(
    name: str,
    schema: dict[str, Any],
    fn: Callable[[str, dict[str, Any]], Any],
) -> Tool:
    """
    (en) Wrap a legacy (name, args) -> result callable as a Tool.

    (kr) 기존 (name, args) -> result 형태의 호출부를 Tool로 래핑한다.
    """
    def execute(args: dict[str, Any]) -> Any:
        return fn(name, args)
    return Tool(name=name, schema=schema, execute=execute)


def tool_from_typed_callable(
    name: str,
    schema: dict[str, Any],
    input_model: type[Any],
    fn: Callable[[str, Any], Any],
) -> Tool:
    """
    (en) Wrap a (name, structured_args) -> result callable as a Tool.

    (kr) (name, structured_args) -> result 형태의 호출부를 Tool로 래핑한다.
    """

    def execute_typed(args_obj: Any) -> Any:
        return fn(name, args_obj)

    return Tool(
        name=name,
        schema=schema,
        execute=execute_typed,
        input_model=input_model,
    )
