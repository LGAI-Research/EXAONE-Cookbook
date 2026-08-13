import type { Difficulty, L10n, L10nList, Topic } from './site'

export interface Cookbook {
  id: string
  icon: string
  title: L10n
  summary: L10n
  /** Concrete things the finished recipe does. */
  highlights: L10nList
  path: string
  difficulty: Difficulty
  minutes: number
  topics: Topic[]
  patterns: string[]
  needs: L10n
}

export const cookbooks: Cookbook[] = [
  {
    id: 'internal-kb-qa',
    icon: '📚',
    title: { en: 'Internal KB QA', ko: '사내 지식베이스 QA' },
    summary: {
      en: 'A cited RAG agent over internal policy documents, gated so uncited answers never ship.',
      ko: '사내 정책 문서를 대상으로 하는 인용 기반 RAG 에이전트. 인용 없는 답변은 나가지 못하게 게이트를 겁니다.',
    },
    highlights: {
      en: [
        'Retrieval exposed as a tool with re-query on weak evidence',
        'A citation gate that fails the answer rather than guessing',
        'Live evaluation against a small golden set',
      ],
      ko: [
        '근거가 약하면 재질의하는 검색 도구',
        '추측 대신 답변을 실패시키는 인용 게이트',
        '소규모 골든셋 기반 라이브 평가',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_01_capstone_internal_kb_qa.ipynb',
    difficulty: 'advanced',
    minutes: 45,
    topics: ['rag', 'evaluation', 'capstone'],
    patterns: ['rag-tool', 'react'],
    needs: { en: 'Tracks 04, 08', ko: 'Track 04 · 08' },
  },
  {
    id: 'meeting-minutes',
    icon: '🗒️',
    title: { en: 'Meeting Minutes → Actions', ko: '회의록 → 액션 아이템' },
    summary: {
      en: 'Turn raw minutes into typed action items through a STRICT → LOOSE → REPAIR JSON pipeline.',
      ko: 'STRICT → LOOSE → REPAIR JSON 파이프라인으로 원문 회의록을 타입이 있는 액션 아이템으로 바꿉니다.',
    },
    highlights: {
      en: [
        'Schema-first extraction with owner, due date and confidence',
        'Three-stage fallback so one malformed field never loses the run',
        'Schema adherence measured, not assumed',
      ],
      ko: [
        '담당자 · 기한 · 확신도를 포함한 스키마 우선 추출',
        '필드 하나가 깨져도 실행 전체를 잃지 않는 3단 폴백',
        '가정하지 않고 측정하는 스키마 준수율',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_02_capstone_meeting_minutes_to_actions.ipynb',
    difficulty: 'advanced',
    minutes: 40,
    topics: ['structured', 'evaluation', 'capstone'],
    patterns: ['structured'],
    needs: { en: 'Tracks 01, 08', ko: 'Track 01 · 08' },
  },
  {
    id: 'code-review',
    icon: '🔍',
    title: { en: 'Code Review Assistant', ko: '코드 리뷰 어시스턴트' },
    summary: {
      en: 'Review a PR diff with a regex pre-scan plus EXAONE semantic review, and block merge behind a human gate.',
      ko: '정규식 사전 스캔과 EXAONE 의미 리뷰로 PR diff를 검토하고, 사람 승인 게이트로 머지를 차단합니다.',
    },
    highlights: {
      en: [
        'Deterministic secret and pattern scan before any model call',
        'Semantic review that explains risk instead of listing lines',
        'Merge blocked until a reviewer approves',
      ],
      ko: [
        '모델 호출 전에 수행하는 결정적 시크릿·패턴 스캔',
        '라인 나열이 아니라 위험을 설명하는 의미 리뷰',
        '리뷰어 승인 전까지 차단되는 머지',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_03_capstone_code_review_assistant.ipynb',
    difficulty: 'advanced',
    minutes: 45,
    topics: ['safety', 'hitl', 'capstone'],
    patterns: ['hitl', 'guardrails'],
    needs: { en: 'Tracks 03, 07', ko: 'Track 03 · 07' },
  },
  {
    id: 'data-analyst',
    icon: '📈',
    title: { en: 'Data Analyst Agent', ko: '데이터 분석 에이전트' },
    summary: {
      en: 'Answer questions over CSVs, contrasting a free SQL sandbox with an allowlisted aggregate-only tool.',
      ko: 'CSV 질의응답을 자유 SQL 샌드박스와 집계 전용 허용목록 도구로 나눠 비교합니다.',
    },
    highlights: {
      en: [
        'Two capability designs measured side by side',
        'Allowlist that makes the dangerous query unrepresentable',
        'Numeric answers checked against ground truth',
      ],
      ko: [
        '두 가지 권한 설계를 나란히 측정',
        '위험한 질의를 표현 자체가 불가능하게 만드는 허용목록',
        '정답과 대조하는 수치 검증',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_04_capstone_data_analyst.ipynb',
    difficulty: 'advanced',
    minutes: 45,
    topics: ['tools', 'safety', 'capstone'],
    patterns: ['guardrails', 'react'],
    needs: { en: 'Tracks 03, 07', ko: 'Track 03 · 07' },
  },
  {
    id: 'support-router',
    icon: '🎫',
    title: { en: 'Customer Support Router', ko: '고객지원 라우터' },
    summary: {
      en: 'Classify tickets into billing, IT and general queues, drafting replies that only send after approval.',
      ko: '티켓을 billing · IT · general 큐로 분류하고, 승인 후에만 발송되는 답변 초안을 작성합니다.',
    },
    highlights: {
      en: [
        'Routing accuracy tracked per queue',
        'Draft-then-approve flow for outbound messages',
        'Traces that show why a ticket was routed where it was',
      ],
      ko: [
        '큐별로 추적하는 라우팅 정확도',
        '외부 발송을 위한 초안 후 승인 플로우',
        '왜 그 큐로 갔는지 보여주는 trace',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_05_capstone_customer_support_router.ipynb',
    difficulty: 'advanced',
    minutes: 40,
    topics: ['orchestration', 'hitl', 'capstone'],
    patterns: ['router', 'hitl'],
    needs: { en: 'Tracks 06, 07', ko: 'Track 06 · 07' },
  },
  {
    id: 'personal-agent',
    icon: '🤖',
    title: { en: 'Personal Agent (Hermes-minimal)', ko: '개인 비서 (Hermes-minimal)' },
    summary: {
      en: 'A minimal assistant with an append-only memory ledger, two skills, and session restore.',
      ko: 'append-only 메모리 ledger, 두 개의 스킬, 세션 복원을 갖춘 최소 개인 비서입니다.',
    },
    highlights: {
      en: [
        'Calendar and reminder skills behind one loop',
        'Ledger that survives a restart',
        'Deterministic run — no live model required to follow along',
      ],
      ko: [
        '하나의 루프 뒤에 놓인 캘린더·리마인더 스킬',
        '재시작을 견디는 ledger',
        '라이브 모델 없이도 따라갈 수 있는 결정적 실행',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_06_capstone_personal_agent_hermes_minimal.ipynb',
    difficulty: 'advanced',
    minutes: 40,
    topics: ['memory', 'loop', 'capstone'],
    patterns: ['memory', 'react'],
    needs: { en: 'Tracks 02, 05', ko: 'Track 02 · 05' },
  },
  {
    id: 'production-harness',
    icon: '🚀',
    title: { en: 'Production Harness', ko: '운영 하니스' },
    summary: {
      en: 'Wrap any capstone in `capstone_runner`, static regression, an `eval.run` smoke test and a CI template.',
      ko: '아무 캡스톤이나 `capstone_runner` · 정적 회귀 · `eval.run` 스모크 · CI 템플릿으로 감쌉니다.',
    },
    highlights: {
      en: [
        'One runner interface for every capstone',
        'Regression gate that runs without an API key',
        'A CI workflow you can copy into your own repo',
      ],
      ko: [
        '모든 캡스톤에 공통인 runner 인터페이스',
        'API 키 없이도 도는 회귀 게이트',
        '자기 저장소로 복사할 수 있는 CI 워크플로',
      ],
    },
    path: 'recipes/track10_ax_capstones/10_07_capstone_production_harness.ipynb',
    difficulty: 'advanced',
    minutes: 45,
    topics: ['production', 'evaluation', 'capstone'],
    patterns: ['guardrails'],
    needs: { en: 'Track 08', ko: 'Track 08' },
  },
]
