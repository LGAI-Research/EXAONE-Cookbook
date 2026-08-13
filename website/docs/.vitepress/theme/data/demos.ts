import type { L10n, L10nList } from './site'

export interface Demo {
  id: string
  name: string
  upstream: string
  upstreamUrl: string
  pin: string
  status: L10n
  summary: L10n
  details: L10nList
  dir: string
  command: string
}

/**
 * Proof Gallery — external OSS harnesses driven by EXAONE.
 * Upstream repos are cloned by the user into `submodules/`; this repo only ships glue.
 */
export const demos: Demo[] = [
  {
    id: 'smolagents',
    name: 'smolagents',
    upstream: 'Hugging Face smolagents',
    upstreamUrl: 'https://github.com/huggingface/smolagents',
    pin: 'v1.26.0',
    status: { en: 'End-to-end', ko: 'E2E 검증' },
    summary: {
      en: 'A compact tool-calling loop where EXAONE is plugged in as an `OpenAIModel`, verified with an exact-arithmetic smoke test.',
      ko: 'EXAONE을 `OpenAIModel`로 연결한 간결한 도구 호출 루프. 정확한 산술 스모크 테스트로 검증합니다.',
    },
    details: {
      en: [
        'Shortest possible proof that EXAONE drives a third-party agent loop',
        'Ships `run_agent.py` and `eval_smoke.py`',
      ],
      ko: [
        'EXAONE이 서드파티 에이전트 루프를 구동한다는 가장 짧은 증명',
        '`run_agent.py`와 `eval_smoke.py` 포함',
      ],
    },
    dir: 'implementations/smolagents',
    command: './implementations/uv_run.sh smolagents python run_agent.py',
  },
  {
    id: 'browser-use',
    name: 'browser-use',
    upstream: 'browser-use',
    upstreamUrl: 'https://github.com/browser-use/browser-use',
    pin: '0.13.7',
    status: { en: 'End-to-end', ko: 'E2E 검증' },
    summary: {
      en: 'EXAONE driving a real browser through Playwright — forms, single-page apps and table extraction on live pages.',
      ko: 'Playwright로 실제 브라우저를 조작하는 EXAONE. 실제 페이지에서 폼 · SPA · 표 추출을 수행합니다.',
    },
    details: {
      en: [
        'Connected through the OpenAI-compatible `ChatOpenAI` interface',
        'Korean task file at `tasks/example_kr.yaml`; upstream telemetry disabled',
      ],
      ko: [
        'OpenAI 호환 `ChatOpenAI` 인터페이스로 연결',
        '한국어 태스크 `tasks/example_kr.yaml` 제공, upstream 텔레메트리 비활성화',
      ],
    },
    dir: 'implementations/browser-use',
    command: './implementations/uv_run.sh browser-use python run_task.py',
  },
  {
    id: 'crewai',
    name: 'CrewAI',
    upstream: 'CrewAI',
    upstreamUrl: 'https://github.com/crewAIInc/crewAI',
    pin: 'v1.10.0.1',
    status: { en: 'End-to-end', ko: 'E2E 검증' },
    summary: {
      en: 'A three-role crew — researcher, writer, reviewer — running entirely on EXAONE through `crewai.LLM`.',
      ko: 'researcher · writer · reviewer 3역할 크루를 `crewai.LLM`으로 전부 EXAONE 위에서 실행합니다.',
    },
    details: {
      en: [
        'Sequential multi-agent execution with a shared EXAONE backbone',
        'Uses `openai_compat_kwargs()` so thinking flags stay consistent',
      ],
      ko: [
        '공유 EXAONE 백본 위의 순차 멀티 에이전트 실행',
        '`openai_compat_kwargs()`로 thinking 플래그 일관성 유지',
      ],
    },
    dir: 'implementations/crewai',
    command: './implementations/uv_run.sh crewai python run_crew.py',
  },
  {
    id: 'nanoclaw',
    name: 'NanoClaw',
    upstream: 'NanoClaw',
    upstreamUrl: 'https://github.com/nanocoai/nanoclaw',
    pin: 'v2.1.54',
    status: { en: 'End-to-end', ko: 'E2E 검증' },
    summary: {
      en: 'A Docker-isolated coding agent CLI with EXAONE registered as an OpenCode custom provider.',
      ko: 'EXAONE을 OpenCode custom provider로 등록한 Docker 격리 코딩 에이전트 CLI입니다.',
    },
    details: {
      en: [
        'Container isolation for an agent that executes code',
        'Cookbook turn via `run_exaone_turn.py`; full chat loop is opt-in',
      ],
      ko: [
        '코드를 실행하는 에이전트를 위한 컨테이너 격리',
        '`run_exaone_turn.py`로 한 턴 실행, 전체 chat 루프는 opt-in',
      ],
    },
    dir: 'implementations/nanoclaw',
    command: './implementations/uv_run.sh nanoclaw python run_exaone_turn.py',
  },
  {
    id: 'hermes-agent',
    name: 'Hermes Agent',
    upstream: 'Hermes Agent',
    upstreamUrl: 'https://github.com/NousResearch/hermes-agent',
    pin: 'v2026.8.3',
    status: { en: 'End-to-end', ko: 'E2E 검증' },
    summary: {
      en: 'EXAONE wired in as a Hermes custom provider (`custom:exaone/<model>`) with a one-turn skills and CLI demo.',
      ko: 'Hermes custom provider(`custom:exaone/<model>`)로 EXAONE을 연결하고 스킬·CLI 한 턴을 보여줍니다.',
    },
    details: {
      en: [
        'Provider registration through `custom_providers`',
        'Reference point for the personal-agent capstone in Track 10',
      ],
      ko: [
        '`custom_providers`를 통한 provider 등록',
        'Track 10 개인 비서 캡스톤의 참조 구현',
      ],
    },
    dir: 'implementations/hermes-agent',
    command: './implementations/hermes-agent/run_cli_demo.sh',
  },
]
