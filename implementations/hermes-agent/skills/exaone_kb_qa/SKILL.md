---
name: exaone-kb-qa
description: Answer questions about the EXAONE Cookbook layout (recipes vs exaone vs implementations) in Korean when the user asks about this repository.
version: 1.0.0
author: EXAONE Cookbook
license: BSD-3-Clause-LG AI Research
platforms: [linux, macos]
metadata:
  hermes:
    tags: [exaone, cookbook, korean, ax]
---

# EXAONE Cookbook — 레이어 안내 (한국어)

이 스킬은 **EXAONE Cookbook** 저장소 구조를 설명할 때 사용합니다. 코드를 실행하기 전에 사용자 질문이 “이 레포 어디에 뭐가 있나?”인지 확인하세요.

## 레이어 표 (암기용)

| 경로 | 독자 | 역할 |
|------|------|------|
| `recipes/track00_*` … `track10_*` | 입문 | Jupyter 튜토리얼 — EXAONE·에이전트 학습 |
| `exaone/` | 개발자 | 공식 Python 패키지 — ToolAgent, RAG, memory |
| `implementations/` | 고수 | Proof Gallery — 선진 OSS 하니스 + EXAONE 접착 |
| `infrastructure/` | RAG 운영 | Postgres, embedding, ingest |
| `eval/` | 벤치 | naive vs harness M1–M10 |

## recipes vs implementations (자주 묻는 질문)

- **recipes**: LangGraph, MCP, pgvector 등을 **노트북으로 가르침**. submodule으로 Hermes 전체를 넣지 않음.
- **implementations**: Hermes, browser-use 등 **실제 upstream**을 submodule로 pin 하고, `implementations/<repo>/` 에만 YAML·스크립트·스킬 접착.
- **중복 금지**: recipes에 있는 주제를 implementations에 또 submodule 하지 않음 (`docs/implementations.md`).

## EXAONE 백본 (Hermes + EXAONE)

- `implementations/hermes-agent/.env`: `EXAONE_API_KEY`, `EXAONE_BASE_URL`, `EXAONE_MODEL`
- Hermes: `custom_providers` 이름 `exaone`, `key_env: EXAONE_API_KEY`
- 세션: `/model custom:exaone/<EXAONE_MODEL>`
- Cookbook 스모크: `implementations/hermes-agent/run_cli_demo.sh`

## 응답 가이드

1. 사용자 언어가 한국어면 **한국어**로 답한다.
2. 시스템 프롬프트는 영어를 유지해도 된다(Hermes 기본).
3. API 키·`.env` 값은 **절대 출력하지 않는다**.
4. Gateway·terminal·delegation은 기본 데모에서 **권장하지 않음** — Expert opt-in만 언급.

## 관련 문서

- `docs/exaone.md`, `docs/recipes.md`, `docs/implementations.md`
- 루트 `PLAYBOOK.md` — 빈 응답 / thinking 복구 (§6.3.1)
