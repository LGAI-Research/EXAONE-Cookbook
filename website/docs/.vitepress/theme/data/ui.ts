import type { L10n } from './site'

export interface BuildIntent {
  id: string
  icon: string
  title: L10n
  description: L10n
  link: string
  meta: L10n
}

/** "What do you want to build?" — entry points that skip the linear track order. */
export const buildIntents: BuildIntent[] = [
  {
    id: 'first-call',
    icon: '⚡',
    title: { en: 'My first EXAONE call', ko: '첫 EXAONE 호출' },
    description: {
      en: 'Environment, key, kernel, and a response on screen in half an hour.',
      ko: '환경 · 키 · 커널 설정부터 화면에 응답이 뜨기까지 30분.',
    },
    link: '/learn/track-00',
    meta: { en: 'Beginner · 30 min', ko: '입문 · 30분' },
  },
  {
    id: 'tool-agent',
    icon: '🔧',
    title: { en: 'An agent that uses tools', ko: '도구를 쓰는 에이전트' },
    description: {
      en: 'Write the ReAct loop yourself, then compare it against the harness.',
      ko: 'ReAct 루프를 직접 작성하고 하니스와 비교합니다.',
    },
    link: '/learn/track-02',
    meta: { en: 'Intermediate · 75 min', ko: '중급 · 75분' },
  },
  {
    id: 'rag-agent',
    icon: '📚',
    title: { en: 'An agent that cites sources', ko: '근거를 인용하는 에이전트' },
    description: {
      en: 'Retrieval as a callable tool, with citations and failure recovery.',
      ko: '호출 가능한 도구로서의 검색 — 인용과 실패 복구까지.',
    },
    link: '/learn/track-04',
    meta: { en: 'Intermediate · 90 min', ko: '중급 · 90분' },
  },
  {
    id: 'multi-agent',
    icon: '⁂',
    title: { en: 'A team of agents', ko: '에이전트 팀' },
    description: {
      en: 'Planner, executor and critic — plus the experiment that says whether it was worth it.',
      ko: 'planner · executor · critic, 그리고 그럴 가치가 있었는지 확인하는 실험.',
    },
    link: '/learn/track-06',
    meta: { en: 'Intermediate · 60 min', ko: '중급 · 60분' },
  },
  {
    id: 'safe-agent',
    icon: '⚑',
    title: { en: 'An agent I can deploy', ko: '배포할 수 있는 에이전트' },
    description: {
      en: 'Human approval gates, injection defence, traces and an SLO spec.',
      ko: '사람 승인 게이트 · 인젝션 방어 · trace · SLO 스펙.',
    },
    link: '/learn/track-07',
    meta: { en: 'Intermediate · 60 min', ko: '중급 · 60분' },
  },
  {
    id: 'measured-agent',
    icon: '📊',
    title: { en: 'Proof that it actually works', ko: '실제로 동작한다는 증거' },
    description: {
      en: 'Ten metrics, your own golden set, and a regression gate in CI.',
      ko: '10개 지표 · 자체 골든셋 · CI 회귀 게이트.',
    },
    link: '/learn/track-08',
    meta: { en: 'Intermediate · 75 min', ko: '중급 · 75분' },
  },
]

export const ui = {
  hero: {
    eyebrow: {
      en: 'K-EXAONE 2.0 · Agent Cookbook',
      ko: 'K-EXAONE 2.0 · 에이전트 Cookbook',
    },
    title: { en: 'Build agent systems', ko: '에이전트 시스템을' },
    titleAccent: { en: 'with EXAONE', ko: 'EXAONE으로 만듭니다' },
    lede: {
      en: 'Eleven hands-on tracks, a working agent library, ten benchmark metrics and five external-framework proofs — from your first API call to an agent with human gates, traces and CI.',
      ko: '11개 실습 트랙, 실제 동작하는 에이전트 라이브러리, 10개 벤치마크 지표, 5개 외부 프레임워크 증명. 첫 API 호출부터 사람 승인 · trace · CI를 갖춘 에이전트까지.',
    },
    primary: { en: 'Start building', ko: '시작하기' },
    secondary: { en: 'Explore tracks', ko: '트랙 둘러보기' },
    github: { en: 'GitHub', ko: 'GitHub' },
  },
  stats: [
    { value: '11', label: { en: 'Learning tracks', ko: '학습 트랙' } },
    { value: '18', label: { en: 'Lab notebooks', ko: '실습 노트북' } },
    { value: '10', label: { en: 'Eval metrics', ko: '평가 지표' } },
    { value: '5', label: { en: 'Framework proofs', ko: '프레임워크 증명' } },
  ],
  sections: {
    build: {
      eyebrow: { en: 'Start anywhere', ko: '어디서든 시작' },
      title: { en: 'What do you want to build?', ko: '무엇을 만들고 싶으세요?' },
      body: {
        en: 'The tracks are ordered, but you do not have to be. Pick the outcome you need and the prerequisites are listed on the page.',
        ko: '트랙에는 순서가 있지만 반드시 따를 필요는 없습니다. 필요한 결과물을 고르면 각 페이지에 선수 조건이 정리되어 있습니다.',
      },
    },
    path: {
      eyebrow: { en: 'Learning path', ko: '학습 경로' },
      title: { en: 'Track 00 → 10', ko: 'Track 00 → 10' },
      body: {
        en: 'A single spine: environment, model fundamentals, the agent loop, tools, retrieval, memory, orchestration, safety, evaluation, frameworks, and shippable capstones.',
        ko: '하나의 축입니다. 환경 → 모델 기본기 → 에이전트 루프 → 도구 → 검색 → 메모리 → 오케스트레이션 → 안전 → 평가 → 프레임워크 → 출시형 캡스톤.',
      },
    },
    patterns: {
      eyebrow: { en: 'Patterns', ko: '패턴' },
      title: { en: 'Agent patterns, with source', ko: '소스가 있는 에이전트 패턴' },
      body: {
        en: 'Every pattern below is implemented in this repository, not just described. Each card links to the file where it lives and the track that teaches it.',
        ko: '아래 패턴은 설명이 아니라 이 저장소에 실제 구현되어 있습니다. 각 카드는 구현 파일과 이를 다루는 트랙으로 연결됩니다.',
      },
    },
    cookbooks: {
      eyebrow: { en: 'Cookbooks', ko: 'Cookbook' },
      title: { en: 'Complete recipes', ko: '완성형 레시피' },
      body: {
        en: 'Seven capstone agents for real internal workflows — each with a golden set, evaluation, traces and a human gate where it matters.',
        ko: '실제 사내 업무를 대상으로 한 7개 캡스톤 에이전트. 각각 골든셋 · 평가 · trace, 그리고 필요한 곳의 사람 승인 게이트를 갖췄습니다.',
      },
    },
    demos: {
      eyebrow: { en: 'Proof Gallery', ko: 'Proof Gallery' },
      title: { en: 'EXAONE inside other frameworks', ko: '다른 프레임워크 안의 EXAONE' },
      body: {
        en: 'Five external OSS harnesses running on EXAONE through the OpenAI-compatible API. Upstream repos are pinned; this repo ships only the glue.',
        ko: 'OpenAI 호환 API로 EXAONE 위에서 동작하는 5개 외부 OSS 하니스. upstream은 버전이 고정되어 있고 이 저장소는 접착 코드만 제공합니다.',
      },
    },
    bench: {
      eyebrow: { en: 'Benchmarks', ko: '벤치마크' },
      title: { en: 'Cookbook vs naive, measured', ko: 'Cookbook vs naive, 측정값' },
      body: {
        en: 'The same ten metrics the cookbook teaches, run on public suites. Both the wins and the costs are published.',
        ko: 'Cookbook이 가르치는 동일한 10개 지표를 공개 스위트에서 실행한 결과입니다. 개선과 비용을 모두 공개합니다.',
      },
    },
  },
  labels: {
    all: { en: 'All', ko: '전체' },
    difficulty: { en: 'Level', ko: '난이도' },
    topic: { en: 'Topic', ko: '주제' },
    search: { en: 'Search tracks…', ko: '트랙 검색…' },
    results: { en: 'results', ko: '개 결과' },
    reset: { en: 'Reset', ko: '초기화' },
    empty: {
      en: 'No track matches these filters.',
      ko: '조건에 맞는 트랙이 없습니다.',
    },
    minutes: { en: 'min', ko: '분' },
    track: { en: 'Track', ko: 'Track' },
    overview: { en: 'Overview', ko: '개요' },
    outcomes: { en: "What you'll build", ko: '만들게 되는 것' },
    prerequisites: { en: 'Prerequisites', ko: '선수 조건' },
    notebooks: { en: 'Notebooks', ko: '노트북' },
    notebookOne: { en: '1 notebook', ko: '노트북 1개' },
    notebookMany: { en: '{n} notebooks', ko: '노트북 {n}개' },
    patternsUsed: { en: 'Patterns in this track', ko: '이 트랙의 패턴' },
    library: { en: 'Library surface', ko: '사용 라이브러리' },
    openGithub: { en: 'Open on GitHub', ko: 'GitHub에서 열기' },
    preview: { en: 'Preview', ko: '미리보기' },
    prev: { en: 'Previous', ko: '이전' },
    next: { en: 'Next', ko: '다음' },
    viewSource: { en: 'Source', ko: '소스' },
    taughtIn: { en: 'Taught in', ko: '학습 트랙' },
    setup: { en: 'Setup', ko: '설치' },
    quickStart: { en: 'Quick Start', ko: '빠른 시작' },
    upstream: { en: 'Upstream', ko: 'Upstream' },
    pinned: { en: 'Pinned', ko: '고정 버전' },
    naive: { en: 'Naive', ko: 'Naive' },
    cookbook: { en: 'Cookbook', ko: 'Cookbook' },
    delta: { en: 'Δ', ko: 'Δ' },
    viewAll: { en: 'View all', ko: '전체 보기' },
    requires: { en: 'Requires', ko: '필요 조건' },
  },
} as const
