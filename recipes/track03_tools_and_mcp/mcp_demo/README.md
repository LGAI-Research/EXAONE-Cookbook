# Track 03 MCP demo (stdio server + client adapter)

학습용 **stdio MCP 서버**와 Context7·DuckDuckGo `web_search` 클라이언트입니다. 노트북 [`03_tools_and_mcp_lab.ipynb`](../03_tools_and_mcp_lab.ipynb) Session 3 에서 사용합니다.

## 단독 실행

```bash
# repo root
python recipes/track03_tools_and_mcp/mcp_demo/server.py
```

## 환경 변수

- `CONTEXT7_API_KEY` — Context7 문서 검색 (선택)
- `MCP_TOOL_TIMEOUT_S` — 클라이언트 타임아웃 (기본 `exaone.config`)

## 테스트

```bash
pytest test/unit_recipes/test_mcp_demo_helpers.py -q
```
