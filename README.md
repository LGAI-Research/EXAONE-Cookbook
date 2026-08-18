# EXAONE Cookbook

An open-source cookbook for using [K-EXAONE](https://huggingface.co/collections/LGAI-EXAONE/k-exaone-20) / [K-EXAONE 1.0 (236B)](https://huggingface.co/LGAI-EXAONE/K-EXAONE-236B-A23B) / EXAONE models as **agents**.  
This repository provides Jupyter recipes (Track 00–10), the `exaone/` library, RAG infrastructure, benchmarks (`eval/`), and the Proof Gallery (`implementations/`) in one place.

Product name: **EXAONE Cookbook**

**Website:** [lgai-research.github.io/EXAONE-Cookbook](https://lgai-research.github.io/EXAONE-Cookbook/) — tracks, agent patterns, cookbooks, benchmarks

**Learning path (canonical):** [`recipes/README.md`](recipes/README.md) · **Practical guide:** [`PLAYBOOK.md`](PLAYBOOK.md) · **K-EXAONE 2.0 API:** [`docs/k_exaone_2.md`](docs/k_exaone_2.md) · **Docs index:** [`docs/README.md`](docs/README.md)

---

## Quick Start

Requires **Python 3.12+**. On macOS with Homebrew: `python3.12 -m venv .venv`.

```bash
git clone <cookbook-url>
cd <cookbook-root>
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL
python -m ipykernel install --user --name exaone-cookbook --display-name "Python (exaone-cookbook)"
python scripts/verify_recipes.py   # optional: smoke all Track 00–10
jupyter notebook recipes/track00_bootstrap/
```

With an API key, you can run **Track 00–01** right away (no Postgres or Docker required).

**Corporate network / SSL:** if API or HuggingFace calls fail with `CERTIFICATE_VERIFY_FAILED`, add `DISABLE_SSL_VERIFY=1` to `.env` (last resort) or set `REQUESTS_CA_BUNDLE` — see [`PLAYBOOK.md`](PLAYBOOK.md) Part 8.

> `requirements.txt` is generated from `pyproject.toml` / `uv.lock` (recipes + eval only; Proof Gallery deps are separate). Maintainers: `./scripts/regenerate_requirements.sh`.

> For the Proof Gallery (`implementations/`), you must **clone upstream repos yourself**.  
> Guide: [`implementations/README.md`](implementations/README.md) § Upstream clone.

---

## Installation Paths (Dependencies)

| Use case | Recommended setup | Python |
|----------|-------------------|--------|
| **Recipes · eval · exaone** (default) | `pip install -r requirements.txt` then `pip install -e .` | **3.12+** (CI baseline) |
| **Proof Gallery** (optional) | `uv sync --project implementations/<repo>` | Per repo (see README) |
| **Developer lockfile** | `uv sync` (root `pyproject.toml` / `uv.lock`) | 3.12+ |

- The **official OSS path** is `requirements.txt` + venv (same as CI and CONTRIBUTING).
- `pyproject.toml` / `uv.lock` are maintainer reproducibility lockfiles — pip users can ignore them.

---

## Project Structure

```
├── recipes/           # Track 00–10 Jupyter notebooks (+ per-track code such as mcp_demo)
├── exaone/            # LLM · agents · RAG · memory · observability library
├── eval/              # naive vs harness benchmarks (`python -m eval.run`)
├── infrastructure/    # Postgres (pgvector), embeddings, setup scripts
├── implementations/   # External OSS harnesses + EXAONE glue (advanced, optional)
├── submodules/        # Upstream clone location (not shipped — clone yourself)
├── docs/              # Per-folder guides
├── .env.example
└── requirements.txt
```

---

## Recipes (Track 00–10)

| Track | Directory | Summary |
|-------|-----------|---------|
| 00 | `track00_bootstrap/` | env, first API call |
| 01 | `track01_exaone_foundation/` | chat · JSON · tools · thinking · **K-EXAONE 2.0 `preserve_thinking`** |
| 02–07 | `track02_*` … `track07_*` | Agent loop, MCP, RAG, memory, safety |
| 08 | `track08_evaluation_m1_m10/` | M1–M10, `eval.run` |
| 09–10 | `track09_*`, `track10_*` | Framework bridges, AX capstones |

Per-notebook goals and deliverables: each track `README.md`, [`recipes/README.md`](recipes/README.md).

---

## Benchmarks (`eval/`)

```bash
python -m eval.run --limit 5 --pass-k-trials 1    # default: BFCL 4 suites
python -m eval.run --limit 25 --pass-k-trials 2 --sleep 3
# Cookbook matrix (M1–M10): docs/eval.md §4.1 — reference numbers in eval/reference/
```

Metrics and **Table A reference scores**: [`docs/eval.md`](docs/eval.md) · [`eval/reference/`](eval/reference/)

---

## Proof Gallery (`implementations/`, optional)

Demos that connect EXAONE to **external agent frameworks** after Track 00–10.

```bash
cp implementations/smolagents/.env.example implementations/smolagents/.env
uv sync --project implementations/smolagents
./implementations/uv_run.sh smolagents python scripts/check_env.py
```

[`implementations/README.md`](implementations/README.md) · [`docs/implementations.md`](docs/implementations.md)

---

## Infrastructure (RAG · Track 04)

```bash
cd infrastructure/setup
./step1_downloads.sh && ./step2_docker.sh && ./step3_build_rag.sh
```

[`infrastructure/setup/README.md`](infrastructure/setup/README.md)

---

## Development

```bash
pytest test/unit_exaone test/unit_eval test/unit_infrastructure test/unit_implementations \
  --ignore=test/unit_eval/datasets_smoke \
  -m "not integration and not eval_datasets" -q
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) · [`NOTICE.md`](NOTICE.md) · [`LICENSE.md`](LICENSE.md)

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `pip install -r requirements.txt` fails | Use Python **3.12+**; regenerate with `./scripts/regenerate_requirements.sh` |
| `EXAONE_API_KEY` / 401 | Check `.env` key, URL, and model |
| SSL (corporate network) | `DISABLE_SSL_VERIFY=1` or `REQUESTS_CA_BUNDLE` → [`PLAYBOOK.md`](PLAYBOOK.md) Part 8 |
| MCP spawn failure | `pip install -r requirements.txt`, `python recipes/track03_tools_and_mcp/mcp_demo/server.py` |
| RAG connection refused | `infrastructure/setup` step2–4 |

---

## License

- This cookbook: [`LICENSE.md`](LICENSE.md) — **BSD-3-Clause-LG AI Research License**
- Third-party OSS notice (canonical): [`NOTICE.md`](NOTICE.md)
- Summary and upstream table: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

EXAONE model weights and API are subject to separate LG AI Research terms.

---

## 한국어

# EXAONE Cookbook

[K-EXAONE](https://huggingface.co/collections/LGAI-EXAONE/k-exaone-20) / [K-EXAONE 1.0 (236B)](https://huggingface.co/LGAI-EXAONE/K-EXAONE-236B-A23B) / EXAONE 모델을 **에이전트**로 활용하기 위한 오픈소스 Cookbook입니다.  
Jupyter 레시피(Track 00–10), `exaone/` 라이브러리, RAG 인프라, 벤치마크(`eval/`), Proof Gallery(`implementations/`)를 한 저장소에서 제공합니다.

제품명: **EXAONE Cookbook**

**웹사이트:** [lgai-research.github.io/EXAONE-Cookbook](https://lgai-research.github.io/EXAONE-Cookbook/) — 트랙 · 에이전트 패턴 · Cookbook · 벤치마크

**학습 경로 정본:** [`recipes/README.md`](recipes/README.md) · **실무 가이드:** [`PLAYBOOK.md`](PLAYBOOK.md) · **K-EXAONE 2.0 API:** [`docs/k_exaone_2.md`](docs/k_exaone_2.md) · **문서 인덱스:** [`docs/README.md`](docs/README.md)

---

### 빠른 시작

**Python 3.12+** 필요. Homebrew 예: `python3.12 -m venv .venv`.

```bash
git clone <cookbook-url>
cd <cookbook-root>
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL
python -m ipykernel install --user --name exaone-cookbook --display-name "Python (exaone-cookbook)"
python scripts/verify_recipes.py   # 선택: Track 00–10 스모크
jupyter notebook recipes/track00_bootstrap/
```

API 키만 있으면 **Track 00–01**부터 바로 실행할 수 있습니다 (Postgres·Docker 불필요).

**회사망 SSL:** API·HuggingFace 호출이 `CERTIFICATE_VERIFY_FAILED` 이면 `.env` 에 `DISABLE_SSL_VERIFY=1`(최후 수단) 또는 `REQUESTS_CA_BUNDLE` — [`PLAYBOOK.md`](PLAYBOOK.md) Part 8.

> `requirements.txt` 는 `pyproject.toml` / `uv.lock` 에서 생성됩니다(recipes+eval; Proof Gallery 의존성 제외). maintainer: `./scripts/regenerate_requirements.sh`.

> Proof Gallery(`implementations/`)를 쓸 때는 upstream을 **직접 clone** 해야 합니다.  
> 가이드: [`implementations/README.md`](implementations/README.md) § Upstream clone.

---

### 설치 경로 (의존성)

| 용도 | 권장 방법 | Python |
|------|-----------|--------|
| **레시피·eval·exaone** (기본) | `pip install -r requirements.txt` 그다음 `pip install -e .` | **3.12+** (CI 기준) |
| **Proof Gallery** (선택) | `uv sync --project implementations/<repo>` | repo별 (README 참고) |
| **개발자 lockfile** | `uv sync` (루트 `pyproject.toml` / `uv.lock`) | 3.12+ |

- **공식 OSS 경로**는 `requirements.txt` + venv 입니다 (CI·CONTRIBUTING과 동일).
- `pyproject.toml` / `uv.lock` 은 maintainer용 재현 lockfile — pip 사용자는 무시해도 됩니다.

---

### 프로젝트 구조

```
├── recipes/           # Track 00–10 Jupyter 노트북 (+ 트랙별 mcp_demo 등 동반 코드)
├── exaone/            # LLM·에이전트·RAG·메모리·관측 라이브러리
├── eval/              # naive vs harness 벤치마크 (`python -m eval.run`)
├── infrastructure/    # Postgres(pgvector), 임베딩, setup 스크립트
├── implementations/   # 외부 OSS 하니스 + EXAONE 접착 (고수용, optional)
├── submodules/        # upstream clone 위치 (레포 미포함 — 직접 clone)
├── docs/              # 폴더별 안내
├── .env.example
└── requirements.txt
```

---

### 레시피 (Track 00–10)

| Track | 디렉터리 | 요약 |
|-------|----------|------|
| 00 | `track00_bootstrap/` | env, 첫 API 호출 |
| 01 | `track01_exaone_foundation/` | 대화·JSON·툴·thinking · **K-EXAONE 2.0 `preserve_thinking`** |
| 02–07 | `track02_*` … `track07_*` | Agent loop, MCP, RAG, memory, safety |
| 08 | `track08_evaluation_m1_m10/` | M1–M10, `eval.run` |
| 09–10 | `track09_*`, `track10_*` | Framework bridges, AX capstones |

노트북별 목표·산출물: 각 트랙 `README.md`, [`recipes/README.md`](recipes/README.md).

---

### 벤치마크 (`eval/`)

```bash
python -m eval.run --limit 5 --pass-k-trials 1    # default: BFCL 4종
python -m eval.run --limit 25 --pass-k-trials 2 --sleep 3
# Cookbook matrix (M1–M10): docs/eval.md §4.1 — reference numbers in eval/reference/
```

자세한 지표·**Table A reference 표**: [`docs/eval.md`](docs/eval.md) · [`eval/reference/`](eval/reference/)

---

### Proof Gallery (`implementations/`, optional)

Track 00–10 이후 **외부 에이전트 프레임워크**에 EXAONE을 붙이는 데모입니다.

```bash
cp implementations/smolagents/.env.example implementations/smolagents/.env
uv sync --project implementations/smolagents
./implementations/uv_run.sh smolagents python scripts/check_env.py
```

[`implementations/README.md`](implementations/README.md) · [`docs/implementations.md`](docs/implementations.md)

---

### 인프라 (RAG · Track 04)

```bash
cd infrastructure/setup
./step1_downloads.sh && ./step2_docker.sh && ./step3_build_rag.sh
```

[`infrastructure/setup/README.md`](infrastructure/setup/README.md)

---

### 개발

```bash
pytest test/unit_exaone test/unit_eval test/unit_infrastructure test/unit_implementations \
  --ignore=test/unit_eval/datasets_smoke \
  -m "not integration and not eval_datasets" -q
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) · [`NOTICE.md`](NOTICE.md) · [`LICENSE.md`](LICENSE.md)

---

### 트러블슈팅

| 증상 | 조치 |
|------|------|
| `pip install -r requirements.txt` 실패 | Python **3.12+** 확인; `./scripts/regenerate_requirements.sh` 로 재생성 |
| `EXAONE_API_KEY` / 401 | `.env` 키·URL·모델 확인 |
| SSL (회사망) | `DISABLE_SSL_VERIFY=1` 또는 `REQUESTS_CA_BUNDLE` → [`PLAYBOOK.md`](PLAYBOOK.md) Part 8 |
| MCP spawn 실패 | `pip install -r requirements.txt`, `python recipes/track03_tools_and_mcp/mcp_demo/server.py` |
| RAG connection refused | `infrastructure/setup` step2~4 |

---

### 라이선스

- 본 cookbook: [`LICENSE.md`](LICENSE.md) — **BSD-3-Clause-LG AI Research License**
- 서드파티 OSS Notice (정본): [`NOTICE.md`](NOTICE.md)
- 요약·upstream 표: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

EXAONE 모델 가중치·API는 LG AI Research 별도 약관을 따릅니다.
