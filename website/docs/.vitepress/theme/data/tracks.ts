import type { Difficulty, L10n, L10nList, Topic } from './site'

export interface Notebook {
  file: string
  path: string
  title: L10n
}

export interface Track {
  slug: string
  num: string
  dir: string
  title: L10n
  /** Compact label for the learning-path rail. */
  short: L10n
  summary: L10n
  overview: L10n
  difficulty: Difficulty
  minutes: number
  topics: Topic[]
  outcomes: L10nList
  prerequisites: L10nList
  notebooks: Notebook[]
  /** Library symbols the track leans on — shown as chips on the detail page. */
  symbols: string[]
  patterns: string[]
}

export const tracks: Track[] = [
  {
    slug: 'track-00',
    num: '00',
    dir: 'recipes/track00_bootstrap',
    title: { en: 'Bootstrap', ko: '부트스트랩' },
    short: { en: 'Bootstrap', ko: '부트스트랩' },
    summary: {
      en: 'Verify your environment and make your first EXAONE API call.',
      ko: '실행 환경을 점검하고 첫 EXAONE API 호출을 실행합니다.',
    },
    overview: {
      en: 'Start here. You install the cookbook as an editable package, wire a single root `.env`, register the Jupyter kernel, and compare a baseline call against thinking mode and streaming so the rest of the tracks run without setup surprises.',
      ko: '여기서 시작합니다. Cookbook을 editable 패키지로 설치하고 루트 `.env` 하나에 비밀값을 모은 뒤 Jupyter 커널을 등록하고, 기본 호출 · thinking · 스트리밍을 비교해 이후 트랙이 환경 문제 없이 돌아가도록 만듭니다.',
    },
    difficulty: 'beginner',
    minutes: 30,
    topics: ['setup', 'chat', 'streaming'],
    outcomes: {
      en: [
        'A working `.venv` with `exaone` installed in editable mode',
        'A single root `.env` holding key, base URL, model and proxy settings',
        'Your first chat completion, plus thinking and streaming variants side by side',
      ],
      ko: [
        '`exaone`이 editable 모드로 설치된 `.venv`',
        '키 · base URL · 모델 · 프록시를 담은 루트 `.env` 한 파일',
        '첫 chat completion과 thinking · 스트리밍 변형 비교',
      ],
    },
    prerequisites: {
      en: ['Python 3.12+', 'An EXAONE API key, base URL and model id'],
      ko: ['Python 3.12+', 'EXAONE API 키 · base URL · 모델 ID'],
    },
    notebooks: [
      {
        file: '00_bootstrap_lab.ipynb',
        path: 'recipes/track00_bootstrap/00_bootstrap_lab.ipynb',
        title: {
          en: 'Environment check and first API calls',
          ko: '환경 점검과 첫 API 호출',
        },
      },
    ],
    symbols: ['exaone.load_project_env', 'exaone.project_root', 'exaone.llm'],
    patterns: [],
  },
  {
    slug: 'track-01',
    num: '01',
    dir: 'recipes/track01_exaone_foundation',
    title: { en: 'EXAONE Foundation', ko: 'EXAONE 기본기' },
    short: { en: 'Foundation', ko: '기본기' },
    summary: {
      en: 'Multi-turn chat, structured JSON, function calling and thinking control.',
      ko: '멀티턴 대화 · 구조화 JSON · 함수 호출 · thinking 제어를 익힙니다.',
    },
    overview: {
      en: 'Everything an agent loop later depends on: message construction, streaming, schema-constrained JSON with automatic repair, function calling, and the `ThinkingRouter` that decides when reasoning is worth its latency. This is also where K-EXAONE 2.0 `enable_thinking` / `preserve_thinking` semantics are introduced.',
      ko: '이후 에이전트 루프가 기대는 모든 기본기입니다. 메시지 구성 · 스트리밍 · 스키마 기반 JSON(자동 repair 포함) · 함수 호출, 그리고 추론 비용을 언제 지불할지 결정하는 `ThinkingRouter`를 다룹니다. K-EXAONE 2.0의 `enable_thinking` / `preserve_thinking` 의미도 여기서 처음 등장합니다.',
    },
    difficulty: 'beginner',
    minutes: 60,
    topics: ['chat', 'structured', 'tools', 'streaming'],
    outcomes: {
      en: [
        'Multi-turn conversations with explicit context control',
        'JSON output that survives real models: extract → repair → validate',
        'A first function-calling round trip',
        'A router that picks thinking vs non-thinking per request',
      ],
      ko: [
        '컨텍스트를 명시적으로 관리하는 멀티턴 대화',
        '실제 모델에서 버티는 JSON 파이프라인: 추출 → repair → 검증',
        '첫 함수 호출 왕복',
        '요청별로 thinking 사용 여부를 고르는 라우터',
      ],
    },
    prerequisites: {
      en: ['Track 00 complete', 'A model endpoint that supports tools and `response_format`'],
      ko: ['Track 00 완료', 'tools · `response_format`를 지원하는 모델 엔드포인트'],
    },
    notebooks: [
      {
        file: '01_exaone_foundation_lab.ipynb',
        path: 'recipes/track01_exaone_foundation/01_exaone_foundation_lab.ipynb',
        title: {
          en: 'Chat, streaming, JSON schema, function calling, router',
          ko: '대화 · 스트리밍 · JSON 스키마 · 함수 호출 · 라우터',
        },
      },
    ],
    symbols: ['exaone.llm', 'exaone.output', 'ThinkingRouter'],
    patterns: ['router'],
  },
  {
    slug: 'track-02',
    num: '02',
    dir: 'recipes/track02_minimum_agent_loop',
    title: { en: 'Minimum Agent Loop', ko: '최소 에이전트 루프' },
    short: { en: 'Agent Loop', ko: '에이전트 루프' },
    summary: {
      en: 'Write the observe–think–act loop by hand, then compare it with ToolAgent.',
      ko: '관찰–사고–행동 루프를 직접 구현하고 ToolAgent와 비교합니다.',
    },
    overview: {
      en: 'The heart of the cookbook. You build a ReAct loop from scratch — no framework — so every turn, tool result and stop condition is visible, then swap in `ToolAgent` and see exactly which guarantees a harness adds. The deep dive opens the harness up: planner, invocation ledger, tool budget, retry and safety knobs.',
      ko: 'Cookbook의 핵심입니다. 프레임워크 없이 ReAct 루프를 직접 만들어 매 턴 · 도구 결과 · 종료 조건을 눈으로 확인한 뒤, `ToolAgent`로 교체해 하니스가 무엇을 보장해 주는지 비교합니다. 심화 노트북에서는 planner · 호출 ledger · 도구 예산 · 재시도 · 안전 knob까지 해부합니다.',
    },
    difficulty: 'intermediate',
    minutes: 75,
    topics: ['loop', 'tools', 'streaming', 'observability'],
    outcomes: {
      en: [
        'A hand-written agent loop you fully understand',
        'A `ToolAgent` run producing an inspectable trace',
        'SSE streaming of intermediate agent events',
        'A mental model of every harness knob and when to turn it',
      ],
      ko: [
        '전 과정을 이해한 상태의 손코딩 에이전트 루프',
        '추적 가능한 trace를 남기는 `ToolAgent` 실행',
        '중간 이벤트를 SSE로 스트리밍',
        '하니스 knob별 의미와 조정 시점에 대한 감각',
      ],
    },
    prerequisites: {
      en: ['Track 01 (function calling)', 'K-EXAONE 2.0: `enable_thinking` and `preserve_thinking` both `True` for agentic runs'],
      ko: ['Track 01(함수 호출)', 'K-EXAONE 2.0: agentic 실행은 `enable_thinking` · `preserve_thinking` 모두 `True`'],
    },
    notebooks: [
      {
        file: '02a_minimum_agent_loop_lab.ipynb',
        path: 'recipes/track02_minimum_agent_loop/02a_minimum_agent_loop_lab.ipynb',
        title: {
          en: 'Scratch loop, ToolAgent comparison, SSE streaming',
          ko: '손코딩 루프 · ToolAgent 비교 · SSE 스트리밍',
        },
      },
      {
        file: '02b_harness_anatomy.ipynb',
        path: 'recipes/track02_minimum_agent_loop/02b_harness_anatomy.ipynb',
        title: {
          en: 'Deep dive — planner, ledger, budget, safety knobs',
          ko: '심화 — planner · ledger · 예산 · 안전 knob',
        },
      },
    ],
    symbols: ['ToolAgent', 'NextStepPlanner', 'ToolInvocationLedger'],
    patterns: ['react', 'planning', 'guardrails'],
  },
  {
    slug: 'track-03',
    num: '03',
    dir: 'recipes/track03_tools_and_mcp',
    title: { en: 'Tools & MCP', ko: '도구와 MCP' },
    short: { en: 'Tools & MCP', ko: '도구·MCP' },
    summary: {
      en: 'Design, validate and register tools — then connect an MCP server.',
      ko: '도구를 설계·검증·등록하고 MCP 서버를 연결합니다.',
    },
    overview: {
      en: 'Tool quality decides agent quality. You define schemas with `ToolRegistry`, validate arguments before execution, separate safe reads from risky writes with dry-run gates, and finally speak MCP over stdio so the same agent can use tools it did not ship with.',
      ko: '도구 품질이 곧 에이전트 품질입니다. `ToolRegistry`로 스키마를 정의하고 실행 전 인자를 검증하며, dry-run 게이트로 안전한 읽기와 위험한 쓰기를 분리한 뒤, stdio로 MCP를 연결해 내장하지 않은 도구까지 쓰게 만듭니다.',
    },
    difficulty: 'intermediate',
    minutes: 60,
    topics: ['tools', 'mcp', 'safety'],
    outcomes: {
      en: [
        'A registry of typed tools with argument validation',
        'A safety checklist separating read-only and side-effecting tools',
        'An MCP stdio client wired into your agent',
      ],
      ko: [
        '인자 검증이 포함된 타입 기반 도구 레지스트리',
        '읽기 전용 도구와 부수효과 도구를 분리하는 안전 체크리스트',
        '에이전트에 연결된 MCP stdio 클라이언트',
      ],
    },
    prerequisites: {
      en: ['Track 02', 'The `mcp` package for the MCP session'],
      ko: ['Track 02', 'MCP 세션을 위한 `mcp` 패키지'],
    },
    notebooks: [
      {
        file: '03_tools_and_mcp_lab.ipynb',
        path: 'recipes/track03_tools_and_mcp/03_tools_and_mcp_lab.ipynb',
        title: {
          en: 'ToolRegistry, safety checklist, MCP client',
          ko: 'ToolRegistry · 안전 체크리스트 · MCP 클라이언트',
        },
      },
    ],
    symbols: ['ToolRegistry', 'ToolResult', 'exaone.tools'],
    patterns: ['guardrails'],
  },
  {
    slug: 'track-04',
    num: '04',
    dir: 'recipes/track04_rag_and_knowledge',
    title: { en: 'RAG & Knowledge', ko: 'RAG & 지식' },
    short: { en: 'RAG', ko: 'RAG' },
    summary: {
      en: 'Evidence-based answers: embeddings, retrieval strategies, citations.',
      ko: '근거 기반 답변: 임베딩 · 검색 전략 · 인용.',
    },
    overview: {
      en: 'Retrieval turned into an agent tool rather than a prompt prefix. You build an in-memory pipeline first, add citation and failure-recovery behaviour, then scale into pgvector and compare vector, graph and hybrid strategies on the same questions.',
      ko: '검색을 프롬프트 접두사가 아니라 에이전트 도구로 다룹니다. 먼저 인메모리 파이프라인을 만들고 인용·실패 복구 동작을 붙인 다음, pgvector로 확장해 동일 질문에서 vector · graph · hybrid 전략을 비교합니다.',
    },
    difficulty: 'intermediate',
    minutes: 90,
    topics: ['rag', 'tools', 'loop'],
    outcomes: {
      en: [
        'A retrieval tool an agent can call, retry and cite',
        'Recovery behaviour when retrieval returns nothing useful',
        'A pgvector index and a vector / graph / hybrid comparison',
      ],
      ko: [
        '에이전트가 호출·재시도·인용할 수 있는 검색 도구',
        '검색 결과가 쓸모없을 때의 복구 동작',
        'pgvector 인덱스와 vector / graph / hybrid 전략 비교',
      ],
    },
    prerequisites: {
      en: [
        'Tracks 01–03',
        'An embedding server for session 1+',
        'Deep dive only: Docker Postgres + pgvector via `infrastructure/setup`',
      ],
      ko: [
        'Track 01–03',
        '세션 1 이후 임베딩 서버',
        '심화 전용: `infrastructure/setup`으로 구성한 Docker Postgres + pgvector',
      ],
    },
    notebooks: [
      {
        file: '04a_rag_and_knowledge_lab.ipynb',
        path: 'recipes/track04_rag_and_knowledge/04a_rag_and_knowledge_lab.ipynb',
        title: {
          en: 'Embeddings, in-memory RAG, failure recovery',
          ko: '임베딩 · 인메모리 RAG · 실패 복구',
        },
      },
      {
        file: '04b_pgvector_and_strategies.ipynb',
        path: 'recipes/track04_rag_and_knowledge/04b_pgvector_and_strategies.ipynb',
        title: {
          en: 'Deep dive — pgvector index, vector / graph / hybrid',
          ko: '심화 — pgvector 인덱스, vector / graph / hybrid',
        },
      },
    ],
    symbols: ['exaone.retrieval', 'exaone.agents (RAG tools)'],
    patterns: ['react', 'guardrails'],
  },
  {
    slug: 'track-05',
    num: '05',
    dir: 'recipes/track05_memory_and_long_context',
    title: { en: 'Memory & Long Context', ko: '메모리 & 롱 컨텍스트' },
    short: { en: 'Memory', ko: '메모리' },
    summary: {
      en: 'Budget the context window, compact history, persist sessions.',
      ko: '컨텍스트 예산을 관리하고 히스토리를 압축하며 세션을 보존합니다.',
    },
    overview: {
      en: 'Long runs fail on context, not on reasoning. You cap oversized tool results, compact history under an explicit token budget, and move durable state into a two-tier memory ledger plus artifact store so a session can be stopped and resumed.',
      ko: '긴 실행은 추론이 아니라 컨텍스트에서 무너집니다. 과대한 도구 결과를 cap 하고 명시적 토큰 예산 아래에서 히스토리를 압축하며, 지속 상태를 2단 메모리 ledger와 artifact store로 옮겨 세션을 중단·재개할 수 있게 만듭니다.',
    },
    difficulty: 'intermediate',
    minutes: 45,
    topics: ['memory', 'context', 'loop'],
    outcomes: {
      en: [
        'A token budget the agent respects instead of hoping to fit',
        'Compaction that preserves decisions while dropping noise',
        'Session snapshot and restore through the memory ledger',
      ],
      ko: [
        '운에 맡기지 않고 실제로 지키는 토큰 예산',
        '결정은 남기고 노이즈만 버리는 압축',
        '메모리 ledger를 통한 세션 스냅샷·복원',
      ],
    },
    prerequisites: {
      en: ['Track 02', 'Track 04 recommended'],
      ko: ['Track 02', 'Track 04 권장'],
    },
    notebooks: [
      {
        file: '05_memory_and_long_context_lab.ipynb',
        path: 'recipes/track05_memory_and_long_context/05_memory_and_long_context_lab.ipynb',
        title: {
          en: 'Context compaction and ledger session restore',
          ko: '컨텍스트 압축과 ledger 세션 복원',
        },
      },
    ],
    symbols: ['exaone.context_management', 'exaone.memory'],
    patterns: ['memory'],
  },
  {
    slug: 'track-06',
    num: '06',
    dir: 'recipes/track06_orchestration_multi_agent',
    title: { en: 'Orchestration & Multi-Agent', ko: '오케스트레이션 & 멀티 에이전트' },
    short: { en: 'Multi-Agent', ko: '멀티에이전트' },
    summary: {
      en: 'Planner → executor → critic, router handoff, and when not to split.',
      ko: 'Planner → executor → critic, 라우터 핸드오프, 그리고 나누지 말아야 할 때.',
    },
    overview: {
      en: 'Multi-agent is a cost, not a feature. You build an explicit planner → executor → critic workflow, route requests to sub-agent profiles, then measure a single agent against the multi-agent version on the same tasks to decide whether the extra hops earned their tokens.',
      ko: '멀티 에이전트는 기능이 아니라 비용입니다. planner → executor → critic 워크플로를 명시적으로 만들고 요청을 서브 에이전트 프로필로 라우팅한 뒤, 같은 과제에서 단일 에이전트와 비교해 추가 홉이 토큰값을 했는지 판단합니다.',
    },
    difficulty: 'intermediate',
    minutes: 60,
    topics: ['multiagent', 'orchestration', 'tools'],
    outcomes: {
      en: [
        'A three-role workflow with explicit handoff contracts',
        'A router that dispatches to specialised sub-agents',
        'A single vs multi-agent comparison on identical tasks',
      ],
      ko: [
        '핸드오프 계약이 명시된 3역할 워크플로',
        '전문화된 서브 에이전트로 분기하는 라우터',
        '동일 과제에서의 단일 vs 멀티 에이전트 비교',
      ],
    },
    prerequisites: {
      en: ['Tracks 01–03'],
      ko: ['Track 01–03'],
    },
    notebooks: [
      {
        file: '06_orchestration_lab.ipynb',
        path: 'recipes/track06_orchestration_multi_agent/06_orchestration_lab.ipynb',
        title: {
          en: 'Three-role workflow, router handoff, single vs multi',
          ko: '3역할 워크플로 · 라우터 핸드오프 · 단일 vs 멀티',
        },
      },
    ],
    symbols: ['ToolAgent', 'ThinkingRouter'],
    patterns: ['plan-execute', 'router', 'multi-agent'],
  },
  {
    slug: 'track-07',
    num: '07',
    dir: 'recipes/track07_safety_hitl_observability',
    title: { en: 'Safety, HITL & Observability', ko: '안전 · HITL · 관측' },
    short: { en: 'Safety & HITL', ko: '안전·HITL' },
    summary: {
      en: 'Approval gates, prompt-injection defence, structured traces, SLOs.',
      ko: '승인 게이트 · 프롬프트 인젝션 방어 · 구조화 trace · SLO.',
    },
    overview: {
      en: 'The track that makes an agent deployable. Risky tools go behind human approval, untrusted text from RAG and the web is sanitised before it can steer the loop, every run emits structured JSONL traces with secrets stripped, and the deep dive turns that into an SLO spec with production defaults.',
      ko: '에이전트를 배포 가능하게 만드는 트랙입니다. 위험한 도구는 사람 승인 뒤로 보내고, RAG·웹에서 온 신뢰할 수 없는 텍스트는 루프를 조종하기 전에 정제하며, 모든 실행은 비밀값이 제거된 JSONL trace를 남깁니다. 심화에서는 이를 SLO 스펙과 운영 기본값으로 정리합니다.',
    },
    difficulty: 'intermediate',
    minutes: 60,
    topics: ['safety', 'hitl', 'observability', 'production'],
    outcomes: {
      en: [
        'A human approval gate inside tool execution',
        'Prompt-injection defence for untrusted retrieved text',
        'JSONL traces with sanitised fields, ready for a log pipeline',
        'An SLO spec and recommended production environment',
      ],
      ko: [
        '도구 실행 내부의 사람 승인 게이트',
        '신뢰할 수 없는 검색 텍스트에 대한 프롬프트 인젝션 방어',
        '필드가 정제되어 로그 파이프라인에 바로 넣을 수 있는 JSONL trace',
        'SLO 스펙과 권장 운영 환경',
      ],
    },
    prerequisites: {
      en: ['Tracks 02–03', 'Track 04 recommended for untrusted RAG chunks'],
      ko: ['Track 02–03', '신뢰할 수 없는 RAG chunk 실습을 위해 Track 04 권장'],
    },
    notebooks: [
      {
        file: '07a_safety_and_observability_lab.ipynb',
        path: 'recipes/track07_safety_hitl_observability/07a_safety_and_observability_lab.ipynb',
        title: {
          en: 'HITL gates, injection defence, JSONL traces',
          ko: 'HITL 게이트 · 인젝션 방어 · JSONL trace',
        },
      },
      {
        file: '07b_slo_production_defaults.ipynb',
        path: 'recipes/track07_safety_hitl_observability/07b_slo_production_defaults.ipynb',
        title: {
          en: 'Deep dive — SLOSpec and production defaults',
          ko: '심화 — SLOSpec과 운영 기본값',
        },
      },
    ],
    symbols: ['exaone.observability', 'exaone.context_management (sanitize)'],
    patterns: ['hitl', 'guardrails'],
  },
  {
    slug: 'track-08',
    num: '08',
    dir: 'recipes/track08_evaluation_m1_m10',
    title: { en: 'Evaluation M1–M10', ko: '평가 M1–M10' },
    short: { en: 'Evaluation', ko: '평가' },
    summary: {
      en: 'Ten metrics, a team golden set, and regression gates.',
      ko: '10개 지표 · 팀 골든셋 · 회귀 게이트.',
    },
    overview: {
      en: 'Stop judging agents by vibes. You compute all ten cookbook metrics — success, pass^k reliability, tool selection, argument F1, abstention, schema adherence, token efficiency, call uniqueness, faithfulness, empty-response recovery — build a golden set from your own traffic, and wire it as a regression gate in front of `eval.run`.',
      ko: '체감으로 에이전트를 판단하지 않습니다. success · pass^k 신뢰도 · 도구 선택 · 인자 F1 · abstention · 스키마 준수 · 토큰 효율 · 호출 고유성 · faithfulness · 빈 응답 복구까지 10개 지표를 직접 계산하고, 자체 트래픽으로 골든셋을 만들어 `eval.run` 앞단의 회귀 게이트로 연결합니다.',
    },
    difficulty: 'intermediate',
    minutes: 75,
    topics: ['evaluation', 'tools', 'safety'],
    outcomes: {
      en: [
        'M1–M10 computed on synthetic trials you can read line by line',
        'A golden set that reflects your own task distribution',
        'A regression gate wired to `python -m eval.run`',
      ],
      ko: [
        '한 줄씩 읽어볼 수 있는 합성 trial 기반 M1–M10 계산',
        '자기 과제 분포를 반영하는 골든셋',
        '`python -m eval.run`에 연결된 회귀 게이트',
      ],
    },
    prerequisites: {
      en: ['`pip install -e .` so the local `eval` package resolves', 'API key optional — most sessions run offline'],
      ko: ['로컬 `eval` 패키지 인식을 위한 `pip install -e .`', 'API 키는 선택 — 대부분 세션은 오프라인 동작'],
    },
    notebooks: [
      {
        file: '08a_evaluation_lab.ipynb',
        path: 'recipes/track08_evaluation_m1_m10/08a_evaluation_lab.ipynb',
        title: {
          en: 'M1–M10 metric map and synthetic scoring',
          ko: 'M1–M10 지표 맵과 합성 채점',
        },
      },
      {
        file: '08b_my_golden_set.ipynb',
        path: 'recipes/track08_evaluation_m1_m10/08b_my_golden_set.ipynb',
        title: {
          en: 'Deep dive — golden set regression gates',
          ko: '심화 — 골든셋 회귀 게이트',
        },
      },
    ],
    symbols: ['eval.run', 'eval.metrics', 'eval.judges'],
    patterns: [],
  },
  {
    slug: 'track-09',
    num: '09',
    dir: 'recipes/track09_framework_bridges',
    title: { en: 'Framework Bridges', ko: '프레임워크 브리지' },
    short: { en: 'Bridges', ko: '브리지' },
    summary: {
      en: 'Run EXAONE inside LangChain, LlamaIndex, LangGraph and Gradio.',
      ko: 'LangChain · LlamaIndex · LangGraph · Gradio에서 EXAONE을 실행합니다.',
    },
    overview: {
      en: 'EXAONE speaks the OpenAI-compatible protocol, so existing frameworks work with an adapter rather than a rewrite. You connect four of them, run the same task through each, and compare what a framework harness gives you versus the cookbook loop from Track 02.',
      ko: 'EXAONE은 OpenAI 호환 프로토콜을 사용하므로, 기존 프레임워크는 재작성이 아니라 어댑터만으로 붙습니다. 네 가지를 연결해 같은 과제를 돌려보고, 프레임워크 하니스가 주는 것과 Track 02의 Cookbook 루프를 비교합니다.',
    },
    difficulty: 'intermediate',
    minutes: 60,
    topics: ['frameworks', 'rag', 'multiagent', 'streaming'],
    outcomes: {
      en: [
        'EXAONE as a LangChain chat model and a LlamaIndex LLM',
        'A LangGraph graph running an EXAONE-backed agent',
        'A Gradio UI streaming agent output',
      ],
      ko: [
        'LangChain chat model · LlamaIndex LLM으로 동작하는 EXAONE',
        'EXAONE 기반 에이전트를 실행하는 LangGraph 그래프',
        '에이전트 출력을 스트리밍하는 Gradio UI',
      ],
    },
    prerequisites: {
      en: ['Tracks 02, 04, 06', 'Root `requirements.txt` (langchain, llama-index, langgraph, gradio)'],
      ko: ['Track 02 · 04 · 06', '루트 `requirements.txt`(langchain · llama-index · langgraph · gradio)'],
    },
    notebooks: [
      {
        file: '09_framework_bridges_lab.ipynb',
        path: 'recipes/track09_framework_bridges/09_framework_bridges_lab.ipynb',
        title: {
          en: 'LangChain, LlamaIndex, LangGraph and Gradio bridges',
          ko: 'LangChain · LlamaIndex · LangGraph · Gradio 브리지',
        },
      },
    ],
    symbols: ['exaone.integrations'],
    patterns: ['react', 'plan-execute', 'multi-agent'],
  },
  {
    slug: 'track-10',
    num: '10',
    dir: 'recipes/track10_ax_capstones',
    title: { en: 'AX Capstones', ko: 'AX 캡스톤' },
    short: { en: 'Capstones', ko: '캡스톤' },
    summary: {
      en: 'Seven shippable agents with golden sets, traces, HITL and CI.',
      ko: '골든셋 · trace · HITL · CI를 갖춘 7개의 출시형 에이전트.',
    },
    overview: {
      en: 'Where the tracks converge. Each capstone is a small but complete agent for a real internal workflow, shipped with a golden set, live evaluation, traces, human gates and an SLO spec — and `10_07` wires the whole thing into `capstone_runner` and a CI workflow template.',
      ko: '앞선 트랙이 합류하는 지점입니다. 각 캡스톤은 실제 사내 업무를 대상으로 한 작지만 완결된 에이전트로, 골든셋 · 라이브 평가 · trace · 사람 승인 · SLO 스펙을 갖춥니다. `10_07`은 이 전부를 `capstone_runner`와 CI 워크플로 템플릿으로 묶습니다.',
    },
    difficulty: 'advanced',
    minutes: 45,
    topics: ['capstone', 'evaluation', 'safety', 'hitl', 'production'],
    outcomes: {
      en: [
        'One production-shaped agent for your own use case',
        'A golden set and live evaluation attached to it',
        'A CI workflow that blocks regressions before merge',
      ],
      ko: [
        '자기 use case에 맞춘 운영형 에이전트 하나',
        '거기에 붙은 골든셋과 라이브 평가',
        'merge 전에 회귀를 막는 CI 워크플로',
      ],
    },
    prerequisites: {
      en: ['Tracks 04–08 depending on the capstone', '`pip install -e .`, API key for live evaluation paths'],
      ko: ['선택한 캡스톤에 따라 Track 04–08', '`pip install -e .`, 라이브 평가 경로용 API 키'],
    },
    notebooks: [
      {
        file: '10_01_capstone_internal_kb_qa.ipynb',
        path: 'recipes/track10_ax_capstones/10_01_capstone_internal_kb_qa.ipynb',
        title: { en: 'Internal KB QA with citation gate', ko: '인용 게이트가 있는 사내 KB QA' },
      },
      {
        file: '10_02_capstone_meeting_minutes_to_actions.ipynb',
        path: 'recipes/track10_ax_capstones/10_02_capstone_meeting_minutes_to_actions.ipynb',
        title: { en: 'Meeting minutes to action items', ko: '회의록 → 액션 아이템' },
      },
      {
        file: '10_03_capstone_code_review_assistant.ipynb',
        path: 'recipes/track10_ax_capstones/10_03_capstone_code_review_assistant.ipynb',
        title: { en: 'Code review with HITL merge block', ko: 'HITL 머지 차단이 있는 코드 리뷰' },
      },
      {
        file: '10_04_capstone_data_analyst.ipynb',
        path: 'recipes/track10_ax_capstones/10_04_capstone_data_analyst.ipynb',
        title: { en: 'CSV analyst — sandbox vs allowlist', ko: 'CSV 분석 — 샌드박스 vs 허용목록' },
      },
      {
        file: '10_05_capstone_customer_support_router.ipynb',
        path: 'recipes/track10_ax_capstones/10_05_capstone_customer_support_router.ipynb',
        title: { en: 'Support ticket router with reply gate', ko: '발송 게이트가 있는 티켓 라우터' },
      },
      {
        file: '10_06_capstone_personal_agent_hermes_minimal.ipynb',
        path: 'recipes/track10_ax_capstones/10_06_capstone_personal_agent_hermes_minimal.ipynb',
        title: { en: 'Personal agent with memory ledger', ko: '메모리 ledger 기반 개인 비서' },
      },
      {
        file: '10_07_capstone_production_harness.ipynb',
        path: 'recipes/track10_ax_capstones/10_07_capstone_production_harness.ipynb',
        title: { en: 'Production harness, eval and CI', ko: '운영 하니스 · eval · CI' },
      },
    ],
    symbols: ['capstone_runner', 'eval.run', 'exaone.observability'],
    patterns: ['react', 'hitl', 'memory', 'guardrails'],
  },
]

export const trackBySlug = (slug: string) => tracks.find((track) => track.slug === slug)
