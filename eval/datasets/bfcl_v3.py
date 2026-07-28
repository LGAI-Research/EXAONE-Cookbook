"""
(en) Loader for the Berkeley Function Calling Leaderboard v3 (BFCL v3) dataset
hosted at HuggingFace `gorilla-llm/Berkeley-Function-Calling-Leaderboard`.

Supports four sub-categories required by `eval/README.md` section 3.3:

- ``simple``      — single function in catalog, single call expected (M3, M4)
- ``multiple``    — N functions in catalog, single call expected (M3, M4)
- ``parallel``    — single function in catalog, multiple parallel calls (M3, M4)
- ``irrelevance`` — tools provided but none should be called (M5, M6)

Each raw BFCL row has the following shape (line-delimited JSON, NOT a HF
`load_dataset` split because the repo is multi-file)::

    {"id": "simple_0",
     "question": [[{"role": "user", "content": "..."}]],
     "function": [{"name": "...", "description": "...", "parameters": {...}}]}

Possible-answer rows (only for simple / multiple / parallel) live under
``possible_answer/BFCL_v3_<category>.json`` and look like::

    {"id": "simple_0",
     "ground_truth": [{"<func_name>": {"<arg>": [accepted_val_1, accepted_val_2, ...]}}]}

The full list of acceptable values per argument is preserved in
``EvalTask.metadata["bfcl_ground_truth"]`` so that the M4 argument-F1 metric
can perform proper any-of matching, while the canonical ``ExpectedToolCall``
arguments use the first accepted value for stable display.

(kr) BFCL v3 데이터셋(HuggingFace `gorilla-llm/Berkeley-Function-Calling-Leaderboard`)의 로더이다.
`eval/README.md` 3.3절에서 요구하는 4개 서브카테고리(simple, multiple, parallel, irrelevance)를 지원한다.
원본 row 형식은 line-delimited JSON이며 multi-file 저장소이므로 HF `load_dataset` split이 아닌
`huggingface_hub.hf_hub_download`으로 직접 다운로드한다.
정답(`ground_truth`)은 인자별로 허용값 리스트를 갖는다. 첫 허용값을 canonical로 사용해
`ExpectedToolCall.arguments`에 채우고, 전체 허용값 리스트는 `metadata["bfcl_ground_truth"]`에 보존하여
M4 argument F1 지표가 any-of 매칭을 할 수 있도록 한다.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .schema import EvalTask, ExpectedToolCall, ToolSpec

logger = logging.getLogger(__name__)

BFCL_REPO_ID = "gorilla-llm/Berkeley-Function-Calling-Leaderboard"

# BFCL category -> question file under repo root (and matching possible_answer file when applicable)
# BFCL 카테고리 -> 저장소 루트의 질문 파일(해당되는 경우 possible_answer 파일도 동일 이름)
_CATEGORY_FILES: dict[str, dict[str, str | None]] = {
    "simple":      {"questions": "BFCL_v3_simple.json",      "answers": "possible_answer/BFCL_v3_simple.json"},
    "multiple":    {"questions": "BFCL_v3_multiple.json",    "answers": "possible_answer/BFCL_v3_multiple.json"},
    "parallel":    {"questions": "BFCL_v3_parallel.json",    "answers": "possible_answer/BFCL_v3_parallel.json"},
    "irrelevance": {"questions": "BFCL_v3_irrelevance.json", "answers": None},
}

# BFCL uses "dict" / "float" / "tuple" / "any" instead of the JSON Schema vocabulary.
# Only the top-level container needs normalising for the parameters block to be a valid JSON Schema object.
# BFCL은 "dict"/"float"/"tuple"/"any" 등을 사용한다. parameters 블록의 최상위 컨테이너만 정규화해도 JSON Schema로 사용 가능하다.
_BFCL_TOP_TYPE_REMAP = {"dict": "object"}


def _sanitize_tool_name(name: str) -> str:
    """
    (en) BFCL function names often contain ``.`` (e.g. ``math.factorial``,
    ``geometry.area_circle``) which OpenAI/Friendli ``function.name`` and the
    harness's ``ToolAgentCatalog.to_api_tool_name`` (``[a-zA-Z0-9_-]+``) both
    reject. Replace ``.`` with ``_`` so the same logical tool is identifiable
    end-to-end. We apply this to ToolSpec.name AND to expected_tool_calls /
    bfcl_ground_truth keys so M3/M4/judge see matching identifiers.

    (kr) BFCL 함수명에는 ``.`` (예: ``math.factorial``)이 자주 들어가는데,
    OpenAI/Friendli ``function.name``과 하네스 ``ToolAgentCatalog.to_api_tool_name``
    (``[a-zA-Z0-9_-]+``)이 모두 거부한다. ``.``을 ``_``로 치환해 동일 논리 도구를
    end-to-end 식별 가능하게 한다. ToolSpec.name뿐 아니라 expected_tool_calls /
    bfcl_ground_truth 키에도 동일 변환을 적용해 M3/M4/judge가 일관된 식별자를 본다.
    """
    return name.replace(".", "_")


def supported_categories() -> list[str]:
    """
    (en) Return the BFCL sub-category names this loader supports.
    (kr) 본 로더가 지원하는 BFCL 서브카테고리 이름 목록을 반환한다.
    """
    return list(_CATEGORY_FILES.keys())


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    """
    (en) Lazily yield JSON objects from a UTF-8 line-delimited file. BFCL files
    use one JSON object per line.
    (kr) UTF-8 line-delimited 파일에서 JSON 객체를 lazy하게 yield한다. BFCL 파일은 한 줄에 한 JSON 객체이다.
    """
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _hf_download(filename: str) -> Path:
    """
    (en) Resolve a single file from the BFCL repo to a local cache path.
    Raises `RuntimeError` if `huggingface_hub` is unavailable or download fails.
    (kr) BFCL 저장소의 단일 파일을 로컬 캐시 경로로 해석한다.
    `huggingface_hub`가 없거나 다운로드 실패 시 `RuntimeError`를 발생시킨다.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is required to load BFCL v3; install with `pip install huggingface_hub`."
        ) from exc

    from ._cache import ensure_dataset_cache, hub_cache_dir

    ensure_dataset_cache()

    try:
        return Path(
            hf_hub_download(
                repo_id=BFCL_REPO_ID,
                filename=filename,
                repo_type="dataset",
                cache_dir=str(hub_cache_dir()),
            )
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download '{filename}' from {BFCL_REPO_ID}: {exc}"
        ) from exc


def _normalise_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    (en) Minimal BFCL → JSON-Schema normalisation: rewrite top-level
    ``type: 'dict'`` to ``type: 'object'`` and leave nested types untouched
    (callers that need strict JSON Schema can post-process).

    (kr) 최소한의 BFCL → JSON Schema 정규화이다. 최상위 ``type: 'dict'``를
    ``type: 'object'``로 바꾸며 중첩 타입은 보존한다(엄격 JSON Schema가 필요하면 호출 측에서 추가 처리).
    """
    if not isinstance(parameters, dict):
        return {"type": "object", "properties": {}}
    out = dict(parameters)
    top_type = out.get("type")
    if isinstance(top_type, str) and top_type in _BFCL_TOP_TYPE_REMAP:
        out["type"] = _BFCL_TOP_TYPE_REMAP[top_type]
    return out


def _build_tools(functions: list[dict[str, Any]]) -> list[ToolSpec]:
    return [
        ToolSpec(
            name=_sanitize_tool_name(fn.get("name", "")),
            description=fn.get("description", ""),
            parameters=_normalise_parameters(fn.get("parameters", {})),
        )
        for fn in functions
    ]


def _extract_query(question: Any) -> str:
    """
    (en) Flatten BFCL's ``question`` field (a list of conversations, each a
    list of role/content messages) into a single user-visible string. For BFCL
    v3 simple/multiple/parallel/irrelevance there is exactly one conversation
    with one user message — but we keep this resilient.

    (kr) BFCL의 ``question`` 필드(대화 리스트, 각 대화는 role/content 메시지 리스트)를 단일 사용자 문자열로 평탄화한다.
    simple/multiple/parallel/irrelevance는 보통 단일 대화·단일 user 메시지지만 일반 케이스도 처리한다.
    """
    if isinstance(question, str):
        return question
    if not isinstance(question, list):
        return str(question)

    parts: list[str] = []
    for convo in question:
        if isinstance(convo, list):
            for msg in convo:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    parts.append(str(msg.get("content", "")))
        elif isinstance(convo, dict) and convo.get("role") == "user":
            parts.append(str(convo.get("content", "")))
    return "\n\n".join(p for p in parts if p)


def _canonical_arguments(args_with_choices: dict[str, Any]) -> dict[str, Any]:
    """
    (en) Pick the first acceptable value for each argument. Empty-string
    sentinels in BFCL signal "argument may be omitted"; we skip those when a
    real value exists. The full possible-answer payload is preserved separately.

    (kr) 인자별 첫 허용값을 선택한다. BFCL의 빈 문자열 sentinel은 "인자 생략 가능"을 의미하며,
    실제 값이 있으면 건너뛴다. 전체 허용값 payload는 별도로 보존한다.
    """
    out: dict[str, Any] = {}
    for arg_name, choices in args_with_choices.items():
        if isinstance(choices, list) and choices:
            chosen = next((c for c in choices if c != "" and c is not None), choices[0])
            out[arg_name] = chosen
        else:
            out[arg_name] = choices
    return out


def _build_expected_calls(ground_truth: list[dict[str, dict[str, Any]]]) -> list[ExpectedToolCall]:
    calls: list[ExpectedToolCall] = []
    for entry in ground_truth or []:
        for func_name, args in entry.items():
            calls.append(
                ExpectedToolCall(
                    name=_sanitize_tool_name(func_name),
                    arguments=_canonical_arguments(args),
                )
            )
    return calls


def _sanitize_ground_truth(
    ground_truth: list[dict[str, dict[str, Any]]] | None,
) -> list[dict[str, dict[str, Any]]]:
    """
    (en) Apply `_sanitize_tool_name` to every function-name key while preserving
    the any-of arguments payload (used by `BFCLAnyOfJudge` and M4 any-of matching).

    (kr) function-name 키에 `_sanitize_tool_name`을 적용하되 any-of 인자 payload는
    그대로 보존(`BFCLAnyOfJudge`·M4 any-of 매칭에 사용).
    """
    out: list[dict[str, dict[str, Any]]] = []
    for entry in ground_truth or []:
        out.append({_sanitize_tool_name(fn): args for fn, args in entry.items()})
    return out


def _load_category(category: str, limit: int | None) -> list[EvalTask]:
    spec = _CATEGORY_FILES[category]
    q_path = _hf_download(spec["questions"])

    answers_by_id: dict[str, list[dict[str, dict[str, Any]]]] = {}
    if spec["answers"] is not None:
        a_path = _hf_download(spec["answers"])
        for row in _read_jsonl(a_path):
            rid = row.get("id")
            if rid is not None:
                answers_by_id[rid] = row.get("ground_truth", [])

    tasks: list[EvalTask] = []
    for row in _read_jsonl(q_path):
        rid = row.get("id", "")
        functions = row.get("function", []) or []
        query = _extract_query(row.get("question"))
        tools = _build_tools(functions)

        if category == "irrelevance":
            tasks.append(
                EvalTask(
                    task_id=str(rid),
                    dataset=f"bfcl_v3.{category}",
                    category=category,
                    query=query,
                    tools=tools,
                    expected_tool_calls=None,
                    expected_no_tools=True,
                    metadata={"bfcl_raw_question": row.get("question")},
                )
            )
        else:
            gt = answers_by_id.get(rid, [])
            sanitized_gt = _sanitize_ground_truth(gt)
            tasks.append(
                EvalTask(
                    task_id=str(rid),
                    dataset=f"bfcl_v3.{category}",
                    category=category,
                    query=query,
                    tools=tools,
                    expected_tool_calls=_build_expected_calls(gt),
                    expected_no_tools=False,
                    metadata={
                        "bfcl_ground_truth": sanitized_gt,
                        "bfcl_raw_ground_truth": gt,
                        "bfcl_raw_question": row.get("question"),
                    },
                )
            )

        if limit is not None and len(tasks) >= limit:
            break

    return tasks


def load(category: str | None = None, limit: int | None = None) -> list[EvalTask]:
    """
    (en) Load BFCL v3 tasks. When ``category`` is None, every supported
    sub-category is loaded and concatenated; the ``limit`` (if given) is then
    applied to the concatenated list. When ``category`` is a single
    sub-category name (``simple|multiple|parallel|irrelevance``), the limit
    applies per call to that category.

    (kr) BFCL v3 태스크를 로드한다. ``category``가 None이면 지원되는 모든 서브카테고리를 로드해 이어 붙이며,
    이 경우 ``limit``은 합쳐진 리스트 전체에 적용된다. 단일 서브카테고리 이름이 주어지면 해당 카테고리에 ``limit``이 적용된다.
    """
    if category is None:
        out: list[EvalTask] = []
        for cat in supported_categories():
            out.extend(_load_category(cat, limit=None))
        if limit is not None:
            return out[:limit]
        return out

    if category not in _CATEGORY_FILES:
        raise ValueError(
            f"Unsupported BFCL category '{category}'. Supported: {supported_categories()}"
        )
    return _load_category(category, limit=limit)


__all__ = ["load", "supported_categories", "BFCL_REPO_ID"]
