import type { L10n } from './site'

export interface Metric {
  id: string
  name: L10n
  definition: L10n
  naive: number
  cookbook: number
}

export const SNAPSHOT = {
  suites: 'BFCL v3 (simple · multiple · parallel · irrelevance) + IFEval + HaluBench',
  passK: 2,
  limit: 25,
  tasks: 150,
  command:
    'python -m eval.run \\\n  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \\\n  --limit 25 --pass-k-trials 2 --sleep 3',
}

/** Table A of docs/eval.md — higher is better for every metric. */
export const metrics: Metric[] = [
  {
    id: 'M1',
    name: { en: 'Task Success Rate', ko: '과제 성공률' },
    definition: {
      en: 'Share of tasks judged correct against ground truth or a rubric.',
      ko: '정답 또는 rubric 기준으로 정답 판정된 과제 비율.',
    },
    naive: 0.8867,
    cookbook: 0.8867,
  },
  {
    id: 'M2',
    name: { en: 'pass² Reliability', ko: 'pass² 신뢰도' },
    definition: {
      en: 'Share of tasks solved in two consecutive independent attempts.',
      ko: '2회 연속 독립 시도에서 모두 성공한 과제 비율.',
    },
    naive: 0.88,
    cookbook: 0.88,
  },
  {
    id: 'M3',
    name: { en: 'Tool Selection Accuracy', ko: '도구 선택 정확도' },
    definition: {
      en: 'Chosen tool multiset matches the expected one.',
      ko: '선택한 도구 multiset이 기대값과 일치하는 비율.',
    },
    naive: 0.7733,
    cookbook: 0.84,
  },
  {
    id: 'M4',
    name: { en: 'Argument F1', ko: '인자 F1' },
    definition: {
      en: 'F1 over tool argument names, types and values.',
      ko: '도구 인자 이름 · 타입 · 값에 대한 F1.',
    },
    naive: 0.7547,
    cookbook: 0.7963,
  },
  {
    id: 'M5',
    name: { en: 'Abstention Score', ko: 'Abstention 점수' },
    definition: {
      en: 'Correctly returns no tool call when no tool applies.',
      ko: '도구가 필요 없을 때 호출하지 않는 비율.',
    },
    naive: 0.92,
    cookbook: 0.96,
  },
  {
    id: 'M6',
    name: { en: 'Schema Adherence', ko: '스키마 준수' },
    definition: {
      en: 'Output validates against the requested JSON schema (after repair).',
      ko: '요청한 JSON 스키마를 통과하는 비율(repair 포함).',
    },
    naive: 0.04,
    cookbook: 0.58,
  },
  {
    id: 'M7',
    name: { en: 'Token Efficiency', ko: '토큰 효율' },
    definition: {
      en: 'Success rate per 1k mean tokens — the price of reliability.',
      ko: '평균 1k 토큰당 성공률 — 신뢰성의 가격.',
    },
    naive: 0.4814,
    cookbook: 0.3171,
  },
  {
    id: 'M8',
    name: { en: 'Call Uniqueness', ko: '호출 고유성' },
    definition: {
      en: '1 − redundancy rate; duplicate tool calls are pure waste.',
      ko: '1 − 중복률. 중복 도구 호출은 순수 낭비입니다.',
    },
    naive: 0.8869,
    cookbook: 1.0,
  },
  {
    id: 'M9',
    name: { en: 'Faithfulness', ko: 'Faithfulness' },
    definition: {
      en: 'Answer stays grounded in the provided context.',
      ko: '답변이 제공된 컨텍스트에 근거하는 정도.',
    },
    naive: 0.4767,
    cookbook: 0.5178,
  },
  {
    id: 'M10',
    name: { en: 'Empty-response Recovery', ko: '빈 응답 복구' },
    definition: {
      en: 'Recovers after an empty or reasoning-only response.',
      ko: '빈 응답 또는 reasoning-only 응답 이후 복구하는 비율.',
    },
    naive: 0.0,
    cookbook: 1.0,
  },
]

export const benchTakeaways: { title: L10n; body: L10n }[] = [
  {
    title: { en: 'The harness buys correct behaviour', ko: '하니스는 올바른 동작을 삽니다' },
    body: {
      en: 'Schema adherence goes from 4.00% to 58.00%, empty-response recovery from nothing to 100%, and duplicate tool calls disappear entirely. Tool selection, argument quality, abstention and faithfulness each gain about 4 to 7 points.',
      ko: '스키마 준수가 4.00%에서 58.00%로, 빈 응답 복구가 0%에서 100%로 올라가고 중복 도구 호출은 완전히 사라집니다. 도구 선택 · 인자 품질 · abstention · faithfulness는 각각 4~7%p 개선됩니다.',
    },
  },
  {
    title: { en: 'And it costs tokens', ko: '그리고 토큰을 지불합니다' },
    body: {
      en: 'Token efficiency falls from 48.14% to 31.71% while task success and pass² stay level. Retries, planning and validation are not free — the gain is in how the agent behaves, not in a higher score.',
      ko: '토큰 효율은 48.14%에서 31.71%로 떨어지고 과제 성공률과 pass²는 동일합니다. 재시도 · 계획 · 검증은 공짜가 아니며, 이득은 점수가 아니라 에이전트의 동작 방식에서 나옵니다.',
    },
  },
  {
    title: { en: 'Measure your own workload', ko: '자기 워크로드로 측정하세요' },
    body: {
      en: 'These are 150 tasks across public suites, 25 per dataset, scored pass². Track 08 shows how to build a golden set from your own traffic and gate regressions on it.',
      ko: '이 수치는 공개 스위트 150개 과제(데이터셋당 25문항)를 pass²로 채점한 결과입니다. Track 08에서 자기 트래픽으로 골든셋을 만들고 회귀를 차단하는 방법을 다룹니다.',
    },
  },
]
