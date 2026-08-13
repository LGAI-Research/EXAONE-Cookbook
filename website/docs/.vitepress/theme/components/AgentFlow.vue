<script setup lang="ts">
import { useLocale } from '../composables/useLocale'

const { t } = useLocale()

const label = {
  goal: { en: 'User goal', ko: '사용자 목표' },
  router: { en: 'Thinking router', ko: 'Thinking 라우터' },
  loop: { en: 'Agent loop', ko: '에이전트 루프' },
  loopSub: { en: 'observe → think → act', ko: '관찰 → 사고 → 행동' },
  guard: { en: 'Guardrails · HITL', ko: '가드레일 · HITL' },
  tools: { en: 'Tools · MCP', ko: '도구 · MCP' },
  rag: { en: 'Retrieval', ko: '검색' },
  memory: { en: 'Memory ledger', ko: '메모리 ledger' },
  answer: { en: 'Cited answer', ko: '인용된 답변' },
  trace: { en: 'Trace · metrics', ko: 'Trace · 지표' },
}
</script>

<template>
  <svg
    class="ex-flow"
    viewBox="0 0 760 350"
    role="img"
    :aria-label="t(label.loop)"
    preserveAspectRatio="xMidYMid meet"
  >
    <defs>
      <linearGradient id="ex-flow-core" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="var(--vp-c-brand-2)" stop-opacity="0.22" />
        <stop offset="100%" stop-color="var(--ex-accent)" stop-opacity="0.16" />
      </linearGradient>
      <radialGradient id="ex-flow-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="var(--vp-c-brand-2)" stop-opacity="0.32" />
        <stop offset="100%" stop-color="var(--vp-c-brand-2)" stop-opacity="0" />
      </radialGradient>
      <marker
        id="ex-flow-arrow"
        viewBox="0 0 10 10"
        refX="8"
        refY="5"
        markerWidth="6"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
      </marker>
    </defs>

    <ellipse cx="410" cy="172" rx="210" ry="130" fill="url(#ex-flow-glow)" />

    <!-- edges -->
    <g class="ex-flow-edges" marker-end="url(#ex-flow-arrow)">
      <path class="ex-flow-edge d0" d="M 132 172 L 172 172" />
      <path class="ex-flow-edge d1" d="M 288 172 L 326 172" />
      <path class="ex-flow-edge d2" d="M 494 172 L 586 172" />
    </g>
    <g class="ex-flow-edges ex-flow-edges--soft">
      <path class="ex-flow-edge d3" d="M 410 122 L 410 84" />
      <path class="ex-flow-edge d4" d="M 380 222 C 378 250 330 246 302 266" />
      <path class="ex-flow-edge d5" d="M 410 222 L 410 264" />
      <path class="ex-flow-edge d6" d="M 442 222 C 444 250 496 246 524 266" />
    </g>

    <!-- nodes -->
    <g class="ex-flow-node">
      <rect x="22" y="146" width="110" height="52" rx="14" />
      <text x="77" y="177">{{ t(label.goal) }}</text>
    </g>

    <g class="ex-flow-node">
      <rect x="178" y="146" width="110" height="52" rx="14" />
      <text x="233" y="177">{{ t(label.router) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--core">
      <rect x="330" y="122" width="164" height="100" rx="20" fill="url(#ex-flow-core)" />
      <text class="ex-flow-spin" x="412" y="158">↻</text>
      <text x="412" y="184" class="ex-flow-title">{{ t(label.loop) }}</text>
      <text x="412" y="204" class="ex-flow-sub">{{ t(label.loopSub) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--muted">
      <rect x="322" y="36" width="180" height="48" rx="14" />
      <text x="412" y="65">{{ t(label.guard) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--muted">
      <rect x="238" y="266" width="128" height="46" rx="14" />
      <text x="302" y="294">{{ t(label.tools) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--muted">
      <rect x="374" y="266" width="76" height="46" rx="14" />
      <text x="412" y="294">{{ t(label.rag) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--muted">
      <rect x="458" y="266" width="132" height="46" rx="14" />
      <text x="524" y="294">{{ t(label.memory) }}</text>
    </g>

    <g class="ex-flow-node ex-flow-node--out">
      <rect x="590" y="146" width="132" height="52" rx="14" />
      <text x="656" y="170">{{ t(label.answer) }}</text>
      <text x="656" y="187" class="ex-flow-sub">{{ t(label.trace) }}</text>
    </g>
  </svg>
</template>

<style scoped>
.ex-flow {
  display: block;
  width: 100%;
  max-width: 860px;
  height: auto;
  margin: 0 auto;
  overflow: visible;
}

.ex-flow-node rect {
  fill: var(--ex-surface);
  stroke: var(--ex-border-strong);
  stroke-width: 1;
}

.ex-flow-node text {
  fill: var(--vp-c-text-1);
  font-size: 13.5px;
  font-weight: 600;
  text-anchor: middle;
  font-family: var(--vp-font-family-base);
}

.ex-flow-node--muted rect {
  fill: var(--ex-surface-2);
  stroke: var(--ex-border);
  stroke-dasharray: 4 4;
}

.ex-flow-node--muted text {
  fill: var(--vp-c-text-2);
  font-size: 12.5px;
  font-weight: 550;
}

.ex-flow-node--core rect {
  stroke: var(--vp-c-brand-2);
  stroke-width: 1.5;
}

.ex-flow-node--out rect {
  stroke: var(--ex-accent);
}

.ex-flow-title {
  font-size: 15px !important;
  font-weight: 700 !important;
}

.ex-flow-sub {
  font-size: 11.5px !important;
  font-weight: 500 !important;
  fill: var(--vp-c-text-3) !important;
  font-family: var(--vp-font-family-mono) !important;
}

.ex-flow-spin {
  font-size: 20px !important;
  fill: var(--vp-c-brand-1) !important;
  transform-box: fill-box;
  transform-origin: center;
  animation: ex-spin 6s linear infinite;
}

.ex-flow-edges {
  color: var(--vp-c-brand-2);
}

.ex-flow-edges--soft {
  color: var(--ex-border-strong);
}

.ex-flow-edge {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-dasharray: 6 7;
  animation: ex-dash 1.4s linear infinite;
}

.ex-flow-edges--soft .ex-flow-edge {
  stroke-width: 1.3;
  animation-duration: 2.2s;
}

.d1 { animation-delay: -0.35s; }
.d2 { animation-delay: -0.7s; }
.d3 { animation-delay: -0.2s; }
.d4 { animation-delay: -0.5s; }
.d5 { animation-delay: -0.9s; }
.d6 { animation-delay: -1.3s; }

@keyframes ex-dash {
  to {
    stroke-dashoffset: -26;
  }
}

@keyframes ex-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 520px) {
  .ex-flow {
    min-width: 560px;
  }
}
</style>
