# Contributing

Thank you for contributing to **EXAONE Cookbook**.

## Getting started

```bash
git clone <cookbook-url>
cd <cookbook-root>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # fill EXAONE_* for live API runs
```

**Install policy:** use `requirements.txt` + venv for recipes, `exaone/`, and `eval/`.  
Root `pyproject.toml` / `uv.lock` is an optional maintainer lockfile (`uv sync`).  
Proof Gallery demos use per-repo `uv sync --project implementations/<repo>` and require **manual upstream clone** under `submodules/` — see [`implementations/README.md`](implementations/README.md).

```bash
pytest test/unit_exaone test/unit_eval test/unit_infrastructure test/unit_implementations \
  --ignore=test/unit_eval/datasets_smoke \
  -m "not integration and not eval_datasets" -q
```

- **Learning path:** [`recipes/README.md`](recipes/README.md) (Track 00–10)
- **Proof Gallery (optional):** [`implementations/README.md`](implementations/README.md) — separate `.env` / `uv` per demo

### Install paths

| Path | When |
|------|------|
| `pip install -r requirements.txt` + `pip install -e .` | Default — recipes notebooks, `exaone/`, `eval.run`, CI |
| `uv sync --project implementations/<repo>` | Proof Gallery demos only |
| `uv sync` at repo root | Optional — reproducible dev env via `uv.lock` |

Do not mix cookbook `.venv` with `implementations/<repo>/.venv`.

## Code comments (`.py`, notebooks, fenced examples)

All `#` comments in Python — including code cells in `.ipynb` and ` ```python ` blocks in docs — must use **bilingual pairs**:

```python
# (en) English explanation.
# (kr) 같은 내용의 한국어 설명.
<code>
```

- No inline trailing comments on code lines.
- Docstrings (`"""..."""`) are exempt but should stay bilingual where they already exist.
- Full rule: [`.cursor/rules/bilingual-comments.mdc`](.cursor/rules/bilingual-comments.mdc)

## Where to put code

| Goal | Location |
|------|----------|
| Library / harness | `exaone/` |
| Benchmarks | `eval/` |
| Tutorials | `recipes/trackNN_*/*.ipynb` |
| Track-specific demo scripts (stdio MCP, etc.) | `recipes/trackNN_*/_demo/` or `mcp_demo/` next to the notebook |
| External OSS glue | `implementations/<repo>/` only — **do not** edit `submodules/` |
| Infra | `infrastructure/` |

We **do not** add new top-level `reference_implementations/`. Teach by notebook + track-local demo files.

## Pull requests

1. Keep PRs focused (one track, one eval feature, or one implementation glue).
2. Run unit tests locally (no API key required for most).
3. Update docs if you change CLI (`eval.run`), env vars (`.env.example`), or track prerequisites.
4. Do not commit `.env`, `eval/reports/`, or `recipes/**/_out/`.

## Commit messages

Use imperative, concise subjects (English or Korean), e.g.:

- `feat(eval): add tau_bench runner`
- `docs(recipes): fix Track 03 MCP paths`

## License

Contributions to **EXAONE Cookbook** are subject to [`LICENSE.md`](LICENSE.md) (BSD-3-Clause-LG AI Research License).  
Third-party OSS notices: [`NOTICE.md`](NOTICE.md).

## Questions

Open a GitHub issue with repro steps, notebook name, and error text (redact API keys).
