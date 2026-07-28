# Third-Party Notices

**제품명:** EXAONE Cookbook  
**저작권:** Copyright (c) 2026 the LG AI Research. All rights reserved.

## 정본

이 cookbook에 포함된·참조되는 오픈소스 소프트웨어의 **정식 OSS Notice(의존성 목록 + 라이선스 전문)** 는 아래 파일입니다.

→ **[`NOTICE.md`](NOTICE.md)**

본 cookbook 소스 코드의 라이선스는 **[`LICENSE.md`](LICENSE.md)** (BSD-3-Clause-LG AI Research License) 입니다.  
EXAONE 모델 가중치·API는 LG AI Research 별도 약관을 따릅니다.

## Upstream OSS (직접 clone, 레포 미포함)

`submodules/` 에 유저가 clone하는 upstream의 라이선스는 각 프로젝트 원본을 따릅니다.  
가이드: [`implementations/README.md`](implementations/README.md).

| Project | Upstream license | Upstream |
|---------|------------------|----------|
| [hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | NousResearch |
| [browser-use](https://github.com/browser-use/browser-use) | MIT | browser-use |
| [nanoclaw](https://github.com/nanocoai/nanoclaw) | MIT | nanocoai |
| [crewAI](https://github.com/crewAIInc/crewAI) | MIT | crewAIInc |
| [smolagents](https://github.com/huggingface/smolagents) | Apache-2.0 | Hugging Face |

`implementations/<repo>/` 접착 코드는 이 cookbook과 동일하게 [`LICENSE.md`](LICENSE.md)를 따릅니다.

## Benchmark data

| Dataset | Source |
|---------|--------|
| BFCL v3 | Berkeley Function Calling Leaderboard |
| IFEval | Google Research (bundled under `eval/ifeval/`) |
| τ-bench | [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench) (optional extra) |
| MS MARCO (RAG setup) | Microsoft / Hugging Face `datasets` |

재배포 전 각 데이터셋 라이선스를 확인하세요. 상세 고지는 [`NOTICE.md`](NOTICE.md)와 각 출처를 따릅니다.
