# Quick Start

With an API key you can run **Track 00–01** immediately — no Postgres or Docker required.

```bash
git clone https://github.com/LGAI-Research/EXAONE-Cookbook.git
cd EXAONE-Cookbook
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL
python -m ipykernel install --user --name exaone-cookbook --display-name "Python (exaone-cookbook)"
jupyter notebook recipes/track00_bootstrap/
```

In Jupyter, select the **`Python (exaone-cookbook)`** kernel.

## Environment variables

| Variable | Description |
| -------- | ----------- |
| `EXAONE_API_KEY` | API key for your EXAONE deployment |
| `EXAONE_BASE_URL` | OpenAI-compatible base URL (ends with `/v1`) |
| `EXAONE_MODEL` | Model ID on your endpoint |

::: tip One `.env`, no inline comments
Secrets, SSL and proxy settings live in a single `.env` at the repository root. Do not put `# comments` after a `KEY=value` line — some editors and Jupyter read the comment as part of the value.
:::

## The first cell of every notebook

Notebooks never patch `sys.path`. After the editable install, this is all you need:

```python
import exaone

exaone.load_project_env()
ROOT = exaone.project_root()
```

## Installation paths

| Use case | Setup | Python |
| -------- | ----- | ------ |
| Recipes · eval · exaone (default) | `pip install -r requirements.txt` then `pip install -e .` | 3.12+ |
| Proof Gallery (optional) | `uv sync --project implementations/<repo>` | per repo |
| Developer lockfile | `uv sync` at repo root | 3.12+ |

The official OSS path is `requirements.txt` + venv, matching CI. `pyproject.toml` and `uv.lock` are maintainer reproducibility lockfiles.

## Project layout

```
├── recipes/           # Track 00–10 notebooks
├── exaone/            # LLM · agents · RAG library
├── eval/              # Benchmark harness
├── infrastructure/    # Postgres, embeddings, setup scripts
├── implementations/   # Proof Gallery (optional)
└── docs/              # Repository documentation
```

## Thinking flags on K-EXAONE 2.0

| Workload | `enable_thinking` | `preserve_thinking` |
| -------- | ----------------- | ------------------- |
| Chitchat, one-shot QA | `False` | `False` |
| Agentic runs (`ToolAgent`, Track 02+) | `True` | `True` |

The flags take effect on 2.0+; on 1.0 they are carried in the payload and ignored. Details: [`docs/k_exaone_2.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/docs/k_exaone_2.md).

## Troubleshooting

| Symptom | Action |
| ------- | ------ |
| `EXAONE_API_KEY` error or 401 | Re-check key, base URL and model in `.env` |
| SSL failure on a corporate network | Set `REQUESTS_CA_BUNDLE` — [`PLAYBOOK.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/PLAYBOOK.md) Part 8 |
| MCP server fails to spawn | `pip install -r requirements.txt`, then run `python recipes/track03_tools_and_mcp/mcp_demo/server.py` |
| RAG connection refused | Run `infrastructure/setup` steps 2–4 |

::: warning Proof Gallery
Upstream repos for `implementations/` are **not** vendored. Clone them yourself — see [implementations/README](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/implementations/README.md).
:::

## Next

- [Track 00 — Bootstrap](/learn/track-00) verifies this setup end to end
- [Track 01 — EXAONE Foundation](/learn/track-01) covers chat, JSON, tools and the thinking router
- [Agent patterns](/patterns/) maps each pattern to the file that implements it
