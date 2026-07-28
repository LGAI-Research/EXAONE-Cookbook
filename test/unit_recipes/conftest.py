"""
(en) Add recipes/track03 mcp_demo to sys.path for unit_recipes tests.

(kr) unit_recipes 테스트용 recipes/track03 mcp_demo 를 sys.path 에 추가한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_DEMO = REPO_ROOT / "recipes" / "track03_tools_and_mcp" / "mcp_demo"

for _path in (REPO_ROOT, MCP_DEMO):
    _path_s = str(_path)
    if _path_s not in sys.path:
        sys.path.insert(0, _path_s)
