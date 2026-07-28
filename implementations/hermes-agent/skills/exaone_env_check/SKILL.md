---
name: exaone-env-check
description: Verify EXAONE_API_KEY, EXAONE_BASE_URL, and EXAONE_MODEL from implementations/hermes-agent/.env without printing secrets.
version: 1.0.0
author: EXAONE Cookbook
license: BSD-3-Clause-LG AI Research
platforms: [linux, macos]
metadata:
  hermes:
    tags: [exaone, env, diagnostics]
---

# EXAONE 환경 점검

Cookbook 루트에서 `implementations/hermes-agent/.env` 를 기준으로 EXAONE 연동 전 환경만 검사합니다. **API 키 본문은 로그·답변에 넣지 마세요.**

## 점검 명령

```bash
cd /path/to/<cookbook-root>
./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py check
```

## 통과 기준

| 항목 | 기대 |
|------|------|
| `api_key_set` | `true` |
| `base_url` | `https://.../v1` 형태 (끝 `/v1` 확인) |
| `model` | `implementations/hermes-agent/.env` 의 `EXAONE_MODEL` |
| `submodule_hermes_agent` | `true` (선택: Hermes 데모 시) |

## Hermes config 생성

```bash
source implementations/hermes-agent/scripts/env.sh
./implementations/uv_run.sh hermes-agent python scripts/hermes_glue.py render
```

## 실패 시

| 증상 | 조치 |
|------|------|
| `EXAONE_API_KEY is missing` | `implementations/hermes-agent/.env` 에 키 설정 |
| 401/403 | 키·엔드포인트 재확인 |
| 빈 assistant content | `PLAYBOOK.md` §6.3.1 — thinking off 재시도 |
