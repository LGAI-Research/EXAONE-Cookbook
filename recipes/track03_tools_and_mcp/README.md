# Track 03 — Tools & MCP

> 도구 = **권한이 정의된 함수**. 등록·실행·실패 복구·외부 프로토콜(MCP) 연결까지.
> Agent Learning Hub 매핑: **Stage 2** (도구) + **Stage 5** (능력 패키징 토대).

---

## 학습 목표

- [ ] `exaone.tools.Tool` + `ToolRegistry` 로 스키마·실행·jsonschema 검증을 한 곳에서 관리한다.
- [ ] `ToolResult` / `exaone.tools.tool_executor_return_indicates_error` 로 *성공·빈 결과·검증 오류·전송 오류* 를 구분한다.
- [ ] 위험 도구와 안전 도구를 분리하고, 로그에는 `exaone.observability` sanitize 를 거친다.
- [ ] MCP stdio 서버를 띄우고 `web_search` 결과를 인용해 답하는 흐름을 본다.

---

## 코드 시작 패턴 (facade)

```python
import exaone

exaone.load_project_env()
registry = exaone.tools.ToolRegistry()
registry.register(exaone.tools.Tool(name="get_time", schema={...}, execute=...))
out = registry.execute("get_time", {})
if exaone.tools.tool_executor_return_indicates_error(out):
    ...
```

MCP 타임아웃은 `exaone.config.get_mcp_tool_timeout_s()` (config 네임스페이스는 유지). [`recipes/README.md` Section#4.1](../README.md#41-코드-시작-패턴--import-exaone-facade).

---

## 노트북

| 파일 | 내용 | 산출물 |
|---|---|---|
| [`03_tools_and_mcp_lab.ipynb`](./03_tools_and_mcp_lab.ipynb) | Session 1~3 — ToolRegistry · 안전 도구 설계 · MCP 클라이언트 | `_out/tool_golden.jsonl`, `_out/tool_checklist.md`, `_out/mcp_trace.json` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석**.

---

## 체크포인트

- [ ] `tool_golden.jsonl` 골든 5건 `pass: true` (의도된 실패 케이스는 `expect_error`).
- [ ] `tool_checklist.md` 가 팀 wiki 에 붙여넣을 분량.
- [ ] Session 3 MCP — 네트워크 없을 때도 *discovery* 셀까지 통과 (web_search 셀은 선택).

---

## 선수

- **Track 02** — `ToolRegistry` 를 이미 썼다면 바로 시작 가능.
- **커널:** Track 00 과 동일하게 프로젝트 `.venv` (**Python 3.12+**, 루트 `pyproject.toml` `requires-python`). Session 3 MCP 셀은 `mcp` 미설치 시스템 Python 에서는 실패할 수 있음.

## 다음 트랙

- **Track 04 — RAG**: `ToolAgent` + `rag.retrieve`
- **Track 07 — Safety**: Session 2 체크리스트가 정책 문서로 승격

---

## 문제 해결

- `jsonschema.ValidationError` → `ToolRegistry.execute` 가 인자 검증에 실패한 것. 스키마 `required` / `additionalProperties: false` 확인.
- MCP spawn 실패 → 루트에서 `pip install -r requirements.txt`, `python recipes/track03_tools_and_mcp/mcp_demo/server.py` 단독 실행.
- `web_search ok=False` → `CONTEXT7_API_KEY`·프록시·`source_diagnostics` tool 로 어느 source 가 죽었는지 확인 (`mcp_demo/README.md`).
