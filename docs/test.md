# `test/` — 단위·통합 테스트

**여기는 어떤 곳인가요?**  
`pytest`로 **exaone**, **infrastructure**, **eval**, **implementations** 접착 코드를 자동 검증하는 디렉터리입니다.

| 경로 | 대상 | CI |
|------|------|-----|
| `test/unit_exaone/` | `exaone/` 라이브러리 | PR (fast) |
| `test/unit_eval/` | `eval/` metrics·runners·report·datasets | PR (fast; `datasets_smoke/` 제외) |
| `test/unit_infrastructure/` | `infrastructure/` | PR (`-m "not integration"`) |
| `test/unit_implementations/` | `implementations/` glue (`implementations/<repo>/.env`) | PR (fast) |
| `test/unit_eval/datasets_smoke/` | HF / optional τ-bench 로더 스모크 | **main push only** |

상세·로컬 실행 명령: [`test/README.md`](../test/README.md)
