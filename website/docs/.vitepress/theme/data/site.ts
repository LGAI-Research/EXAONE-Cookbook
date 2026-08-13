export type Lang = 'en' | 'ko'

/** A string that exists in both site locales. */
export interface L10n {
  en: string
  ko: string
}

export interface L10nList {
  en: string[]
  ko: string[]
}

export const REPO = 'LGAI-Research/EXAONE-Cookbook'
export const REPO_URL = `https://github.com/${REPO}`
export const BRANCH = 'main'

export const blob = (path: string) => `${REPO_URL}/blob/${BRANCH}/${path}`
export const tree = (path: string) => `${REPO_URL}/tree/${BRANCH}/${path}`
export const nbviewer = (path: string) =>
  `https://nbviewer.org/github/${REPO}/blob/${BRANCH}/${path}`

export type Difficulty = 'beginner' | 'intermediate' | 'advanced'

export const DIFFICULTY_LABEL: Record<Difficulty, L10n> = {
  beginner: { en: 'Beginner', ko: '입문' },
  intermediate: { en: 'Intermediate', ko: '중급' },
  advanced: { en: 'Advanced', ko: '고급' },
}

/**
 * Topic vocabulary shared by tracks, capstones and demos. Keys are stable ids
 * used by the filter UI; labels are rendered per locale.
 */
export const TOPIC_LABEL = {
  setup: { en: 'Setup', ko: '환경 설정' },
  chat: { en: 'Chat', ko: '대화' },
  structured: { en: 'Structured Output', ko: '구조화 출력' },
  tools: { en: 'Tool Calling', ko: '도구 호출' },
  loop: { en: 'Agent Loop', ko: '에이전트 루프' },
  mcp: { en: 'MCP', ko: 'MCP' },
  rag: { en: 'RAG', ko: 'RAG' },
  memory: { en: 'Memory', ko: '메모리' },
  context: { en: 'Long Context', ko: '롱 컨텍스트' },
  multiagent: { en: 'Multi-Agent', ko: '멀티 에이전트' },
  orchestration: { en: 'Orchestration', ko: '오케스트레이션' },
  safety: { en: 'Safety', ko: '안전' },
  hitl: { en: 'HITL', ko: 'HITL' },
  observability: { en: 'Observability', ko: '관측' },
  evaluation: { en: 'Evaluation', ko: '평가' },
  frameworks: { en: 'Frameworks', ko: '프레임워크' },
  capstone: { en: 'Capstone', ko: '캡스톤' },
  streaming: { en: 'Streaming', ko: '스트리밍' },
  production: { en: 'Production', ko: '운영' },
} as const

export type Topic = keyof typeof TOPIC_LABEL

export const t = (value: L10n, lang: Lang) => value[lang]
export const tList = (value: L10nList, lang: Lang) => value[lang]
