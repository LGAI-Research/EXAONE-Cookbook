<script setup lang="ts">
import { computed } from 'vue'
import { useLocale } from '../composables/useLocale'
import { metrics } from '../data/benchmarks'
import { ui } from '../data/ui'

const props = withDefaults(
  defineProps<{ only?: string[]; showDefinition?: boolean }>(),
  { showDefinition: true },
)

const { t } = useLocale()

const rows = computed(() =>
  props.only ? metrics.filter((metric) => props.only!.includes(metric.id)) : metrics,
)

const fmt = (value: number) => `${(value * 100).toFixed(2)}%`
const delta = (metric: { naive: number; cookbook: number }) => metric.cookbook - metric.naive
const fmtDelta = (value: number) =>
  `${value < 0 ? '−' : '+'}${Math.abs(value * 100).toFixed(2)}%`
const pct = (value: number) => `${Math.max(value, 0) * 100}%`
</script>

<template>
  <div class="bench">
    <div class="bench-legend">
      <span><i class="swatch is-naive" />{{ t(ui.labels.naive) }}</span>
      <span><i class="swatch is-cookbook" />{{ t(ui.labels.cookbook) }}</span>
    </div>

    <ol class="bench-rows">
      <li v-for="metric in rows" :key="metric.id">
        <div class="bench-name">
          <span class="bench-id">{{ metric.id }}</span>
          <strong>{{ t(metric.name) }}</strong>
          <p v-if="showDefinition">{{ t(metric.definition) }}</p>
        </div>

        <div class="bench-bars">
          <div class="bar-row">
            <span class="bar-track"><i class="bar is-naive" :style="{ width: pct(metric.naive) }" /></span>
            <span class="bar-value">{{ fmt(metric.naive) }}</span>
          </div>
          <div class="bar-row">
            <span class="bar-track"><i class="bar is-cookbook" :style="{ width: pct(metric.cookbook) }" /></span>
            <span class="bar-value">{{ fmt(metric.cookbook) }}</span>
          </div>
        </div>

        <div
          class="bench-delta"
          :class="delta(metric) > 0 ? 'is-up' : delta(metric) < 0 ? 'is-down' : ''"
        >
          {{ fmtDelta(delta(metric)) }}
        </div>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.bench-legend {
  display: flex;
  gap: 18px;
  margin-bottom: 14px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vp-c-text-2);
}

.swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 7px;
  border-radius: 3px;
}

.swatch.is-naive,
.bar.is-naive {
  background: var(--vp-c-text-3);
}

.swatch.is-cookbook,
.bar.is-cookbook {
  background: linear-gradient(90deg, var(--vp-c-brand-2), var(--ex-accent));
}

.bench-rows {
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--ex-border);
  border-radius: var(--ex-radius);
  overflow: hidden;
  background: var(--ex-surface);
}

.bench-rows li {
  display: grid;
  grid-template-columns: minmax(200px, 1.15fr) minmax(200px, 1fr) 84px;
  gap: 18px;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid var(--ex-border);
}

.bench-rows li:first-child {
  border-top: none;
}

.bench-id {
  display: inline-block;
  margin-right: 8px;
  font-family: var(--vp-font-family-mono);
  font-size: 11.5px;
  font-weight: 700;
  color: var(--vp-c-brand-1);
}

.bench-name strong {
  font-size: 14.5px;
  font-weight: 640;
}

.bench-name p {
  margin: 4px 0 0;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--vp-c-text-3);
}

.bench-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: var(--ex-surface-2);
  overflow: hidden;
}

.bar {
  display: block;
  height: 100%;
  border-radius: 999px;
  min-width: 2px;
}

.bar-value {
  width: 58px;
  flex: none;
  white-space: nowrap;
  text-align: right;
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--vp-c-text-2);
}

.bench-delta {
  text-align: right;
  font-family: var(--vp-font-family-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--vp-c-text-3);
}

.bench-delta.is-up {
  color: var(--ex-accent);
}

.bench-delta.is-down {
  color: #d9534f;
}

@media (max-width: 720px) {
  .bench-rows li {
    grid-template-columns: 1fr 78px;
    grid-template-areas:
      'name delta'
      'bars bars';
    gap: 12px;
  }
  .bench-name {
    grid-area: name;
  }
  .bench-delta {
    grid-area: delta;
  }
  .bench-bars {
    grid-area: bars;
  }
}
</style>
