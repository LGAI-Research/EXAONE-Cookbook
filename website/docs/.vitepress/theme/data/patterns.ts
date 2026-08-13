import type { L10n, L10nList } from './site'

export interface Pattern {
  id: string
  icon: string
  name: L10n
  tagline: L10n
  description: L10n
  /** Loop / flow rendered as a chain of short steps. */
  flow: L10nList
  /** Repo paths where the pattern actually lives. */
  source: string[]
  /** Track slugs that teach it. */
  tracks: string[]
}

export const patterns: Pattern[] = [
  {
    id: 'react',
    icon: '↻',
    name: { en: 'ReAct Loop', ko: 'ReAct 루프' },
    tagline: {
      en: 'Reason, call a tool, observe, repeat until done.',
      ko: '추론 → 도구 호출 → 관찰을 종료 조건까지 반복.',
    },
    description: {
      en: 'The default runtime of the cookbook. `ToolAgent` runs a bounded observe–think–act loop with tool validation, retry on malformed calls, and a trace of every turn. Track 02 has you write the same loop by hand first, so nothing about the harness stays magic.',
      ko: 'Cookbook의 기본 런타임입니다. `ToolAgent`는 도구 검증 · 잘못된 호출 재시도 · 턴별 trace를 갖춘 유한 관찰–사고–행동 루프를 실행합니다. Track 02에서 같은 루프를 손으로 먼저 작성하므로 하니스가 마법처럼 남지 않습니다.',
    },
    flow: {
      en: ['User goal', 'Reason', 'Tool call', 'Observation', 'Answer'],
      ko: ['사용자 목표', '추론', '도구 호출', '관찰', '답변'],
    },
    source: ['exaone/agents/tool_agent.py', 'exaone/agents/base_agent.py'],
    tracks: ['track-02', 'track-04'],
  },
  {
    id: 'router',
    icon: '⇉',
    name: { en: 'Thinking Router', ko: 'Thinking 라우터' },
    tagline: {
      en: 'Spend reasoning tokens only where they change the answer.',
      ko: '답이 달라지는 곳에만 추론 토큰을 씁니다.',
    },
    description: {
      en: '`ThinkingRouter` classifies each request and decides between a fast non-thinking call and a full reasoning pass — the cheapest reliability win in the whole cookbook. The same routing idea later dispatches requests to specialised sub-agents in Track 06.',
      ko: '`ThinkingRouter`는 요청을 분류해 빠른 non-thinking 호출과 완전한 추론 경로 중 하나를 고릅니다. Cookbook에서 가장 저렴한 신뢰성 개선이며, 같은 라우팅 아이디어가 Track 06에서 전문화된 서브 에이전트 분기로 확장됩니다.',
    },
    flow: {
      en: ['Request', 'Classify', 'Fast path / Thinking path', 'Response'],
      ko: ['요청', '분류', '빠른 경로 / 추론 경로', '응답'],
    },
    source: ['exaone/agents/thinking_router/'],
    tracks: ['track-01', 'track-06'],
  },
  {
    id: 'planning',
    icon: '◆',
    name: { en: 'Next-Step Planning', ko: '다음 단계 계획' },
    tagline: {
      en: 'Decide the next action explicitly instead of hoping the model loops well.',
      ko: '모델의 루프 감각에 맡기지 않고 다음 행동을 명시적으로 결정합니다.',
    },
    description: {
      en: '`NextStepPlanner` sits between turns and answers one question: what is the next useful action, given what we already tried? It carries an invocation ledger that kills duplicate tool calls — the single biggest source of wasted tokens in naive loops.',
      ko: '`NextStepPlanner`는 턴 사이에서 "지금까지 시도한 것을 감안할 때 다음에 무엇이 유용한가" 하나만 답합니다. 호출 ledger를 함께 유지해 중복 도구 호출을 차단하며, 이는 naive 루프에서 토큰이 가장 많이 새는 지점입니다.',
    },
    flow: {
      en: ['State', 'Candidate actions', 'Dedup via ledger', 'Chosen step'],
      ko: ['현재 상태', '후보 행동', 'ledger 중복 제거', '선택된 단계'],
    },
    source: ['exaone/agents/next_step_planner.py'],
    tracks: ['track-02'],
  },
  {
    id: 'plan-execute',
    icon: '⌗',
    name: { en: 'Planner → Executor → Critic', ko: 'Planner → Executor → Critic' },
    tagline: {
      en: 'Split a hard task into three roles with explicit handoffs.',
      ko: '어려운 과제를 명시적 핸드오프가 있는 세 역할로 나눕니다.',
    },
    description: {
      en: 'A planner decomposes, an executor runs tools, a critic checks the result against the original goal before it reaches the user. Track 06 builds it directly and then rebuilds it as a LangGraph graph in Track 09, so you can compare hand-rolled orchestration with a framework.',
      ko: 'planner가 분해하고 executor가 도구를 실행하며, critic이 사용자에게 가기 전에 원래 목표와 대조합니다. Track 06에서 직접 구현하고 Track 09에서 LangGraph 그래프로 다시 만들어, 직접 만든 오케스트레이션과 프레임워크를 비교합니다.',
    },
    flow: {
      en: ['Goal', 'Plan', 'Execute', 'Critique', 'Deliver'],
      ko: ['목표', '계획', '실행', '검증', '전달'],
    },
    source: [
      'recipes/track06_orchestration_multi_agent/06_orchestration_lab.ipynb',
      'recipes/track09_framework_bridges/09_framework_bridges_lab.ipynb',
    ],
    tracks: ['track-06', 'track-09'],
  },
  {
    id: 'multi-agent',
    icon: '⁂',
    name: { en: 'Multi-Agent Handoff', ko: '멀티 에이전트 핸드오프' },
    tagline: {
      en: 'Specialised agents — only when a single agent measurably loses.',
      ko: '단일 에이전트가 측정 가능하게 열릴 때만 전문화 에이전트를 씁니다.',
    },
    description: {
      en: 'Role-based agents with narrow tools and narrow prompts, dispatched by a router. The cookbook insists on the control experiment: run the same tasks through one agent and through the crew, then compare success and token cost before you keep the extra hops.',
      ko: '좁은 도구와 좁은 프롬프트를 가진 역할별 에이전트를 라우터가 분기시킵니다. Cookbook은 대조 실험을 요구합니다. 같은 과제를 단일 에이전트와 크루로 각각 돌려 성공률과 토큰 비용을 비교한 뒤에야 추가 홉을 유지합니다.',
    },
    flow: {
      en: ['Router', 'Specialist A / B / C', 'Merge', 'Answer'],
      ko: ['라우터', '전문 에이전트 A / B / C', '병합', '답변'],
    },
    source: [
      'recipes/track06_orchestration_multi_agent/',
      'implementations/crewai/run_crew.py',
    ],
    tracks: ['track-06', 'track-09'],
  },
  {
    id: 'memory',
    icon: '▤',
    name: { en: 'Ledger Memory & Compaction', ko: 'Ledger 메모리와 압축' },
    tagline: {
      en: 'Keep decisions, drop transcripts, survive long sessions.',
      ko: '결정은 남기고 전문(全文)은 버려 긴 세션을 견딥니다.',
    },
    description: {
      en: 'A two-tier design: an append-only ledger for what happened and an artifact store for bulky payloads, with LLM-assisted compaction keeping the live window inside an explicit token budget. Sessions can be snapshotted and resumed without replaying history.',
      ko: '2단 구조입니다. 무슨 일이 있었는지는 append-only ledger에, 큰 payload는 artifact store에 두고, LLM 보조 압축이 활성 윈도를 명시적 토큰 예산 안에 유지합니다. 히스토리를 재생하지 않고도 세션을 스냅샷·재개할 수 있습니다.',
    },
    flow: {
      en: ['Turn', 'Ledger append', 'Budget check', 'Compact', 'Continue'],
      ko: ['턴 진행', 'ledger 기록', '예산 확인', '압축', '계속'],
    },
    source: ['exaone/memory/', 'exaone/context_management/'],
    tracks: ['track-05'],
  },
  {
    id: 'hitl',
    icon: '⚑',
    name: { en: 'Human-in-the-Loop Gate', ko: 'HITL 승인 게이트' },
    tagline: {
      en: 'Side effects wait for a human yes.',
      ko: '부수효과는 사람의 승인을 기다립니다.',
    },
    description: {
      en: 'Approval is enforced inside tool execution, not in the prompt — a model cannot talk its way past it. Risky tools declare themselves, dry-run first, and block until approved, which is also how the capstones keep merge, send and write actions safe.',
      ko: '승인은 프롬프트가 아니라 도구 실행 내부에서 강제됩니다. 모델이 말로 우회할 수 없습니다. 위험한 도구는 스스로를 선언하고 dry-run을 먼저 수행하며 승인 전까지 차단됩니다. 캡스톤의 merge · 발송 · 쓰기 동작도 같은 방식으로 보호됩니다.',
    },
    flow: {
      en: ['Tool call', 'Risk check', 'Dry run', 'Human approve', 'Execute'],
      ko: ['도구 호출', '위험도 확인', 'dry run', '사람 승인', '실행'],
    },
    source: [
      'recipes/track07_safety_hitl_observability/07a_safety_and_observability_lab.ipynb',
    ],
    tracks: ['track-07', 'track-10'],
  },
  {
    id: 'guardrails',
    icon: '⛨',
    name: { en: 'Guardrails & Sanitization', ko: '가드레일과 정제' },
    tagline: {
      en: 'Treat retrieved text and tool output as untrusted input.',
      ko: '검색 텍스트와 도구 출력은 신뢰할 수 없는 입력으로 취급합니다.',
    },
    description: {
      en: 'Untrusted text is wrapped and neutralised before it enters the context, logs are sanitised before they leave the process, tool budgets bound runaway loops, and allowlists replace free-form execution wherever a capability can be enumerated.',
      ko: '신뢰할 수 없는 텍스트는 컨텍스트에 들어가기 전에 감싸고 무력화하며, 로그는 프로세스를 떠나기 전에 정제합니다. 도구 예산이 폭주 루프를 제한하고, 능력을 열거할 수 있는 곳에서는 자유 실행 대신 허용목록을 씁니다.',
    },
    flow: {
      en: ['Untrusted text', 'Sanitize', 'Budgeted tool call', 'Sanitized log'],
      ko: ['비신뢰 텍스트', '정제', '예산 내 도구 호출', '정제된 로그'],
    },
    source: [
      'exaone/context_management/untrusted_text.py',
      'exaone/observability/log_sanitize.py',
    ],
    tracks: ['track-03', 'track-07'],
  },
  {
    id: 'structured',
    icon: '{ }',
    name: { en: 'Structured Output Repair', ko: '구조화 출력 repair' },
    tagline: {
      en: 'Extract, repair, then validate — never parse and pray.',
      ko: '추출 → repair → 검증. 파싱 후 기도하지 않습니다.',
    },
    description: {
      en: 'A three-stage pipeline turns almost-JSON into schema-valid JSON: extract the payload, repair common model damage, validate against the schema. Its measured effect is one of the largest in the benchmark table — schema adherence goes from 4.00% to 58.00%.',
      ko: '3단 파이프라인이 "거의 JSON"을 스키마에 맞는 JSON으로 바꿉니다. payload 추출 → 흔한 손상 repair → 스키마 검증. 벤치마크 표에서 가장 큰 개선폭 중 하나로, 스키마 준수가 4.00%에서 58.00%로 올라갑니다.',
    },
    flow: {
      en: ['Raw output', 'Extract', 'Repair', 'Validate', 'Typed object'],
      ko: ['원시 출력', '추출', 'repair', '검증', '타입 객체'],
    },
    source: ['exaone/output/'],
    tracks: ['track-01', 'track-08'],
  },
  {
    id: 'rag-tool',
    icon: '⌕',
    name: { en: 'Retrieval as a Tool', ko: '도구로서의 검색' },
    tagline: {
      en: 'The agent decides when to search, and cites what it used.',
      ko: '검색 시점은 에이전트가 정하고, 사용한 근거를 인용합니다.',
    },
    description: {
      en: 'Instead of stuffing context ahead of time, retrieval is exposed as a callable tool the agent can invoke, re-query and abandon. Answers carry citations, empty results trigger recovery behaviour, and vector, graph and hybrid strategies are compared on identical questions.',
      ko: '컨텍스트를 미리 채우는 대신, 검색을 에이전트가 호출·재질의·포기할 수 있는 도구로 노출합니다. 답변에는 인용이 붙고 빈 결과는 복구 동작을 유발하며, 동일 질문에서 vector · graph · hybrid 전략을 비교합니다.',
    },
    flow: {
      en: ['Question', 'Search tool', 'Evidence', 'Cited answer'],
      ko: ['질문', '검색 도구', '근거', '인용 답변'],
    },
    source: ['exaone/retrieval/', 'recipes/track04_rag_and_knowledge/'],
    tracks: ['track-04'],
  },
]

export const patternById = (id: string) => patterns.find((pattern) => pattern.id === id)
