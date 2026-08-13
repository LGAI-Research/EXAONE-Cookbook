<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import { SNAPSHOT, benchTakeaways } from '../data/benchmarks'

const { t } = useLocale()

const meta = {
  suites: { en: 'Suites', ko: '스위트' },
  run: { en: 'Run', ko: '실행 조건' },
  scoring: { en: 'Scoring', ko: '채점' },
}

const passLabel = SNAPSHOT.passK === 2 ? 'pass²' : `pass^${SNAPSHOT.passK}`

const runValue = {
  en: `${SNAPSHOT.tasks} tasks · ${SNAPSHOT.limit} per dataset`,
  ko: `과제 ${SNAPSHOT.tasks}개 · 데이터셋당 ${SNAPSHOT.limit}문항`,
}

const scoringValue = {
  en: `${passLabel} · higher is better on every metric`,
  ko: `${passLabel} · 모든 지표 높을수록 좋음`,
}
</script>

<template>
  <div class="notes">
    <dl class="snapshot">
      <div>
        <dt>{{ t(meta.suites) }}</dt>
        <dd>{{ SNAPSHOT.suites }}</dd>
      </div>
      <div>
        <dt>{{ t(meta.run) }}</dt>
        <dd>{{ t(runValue) }}</dd>
      </div>
      <div>
        <dt>{{ t(meta.scoring) }}</dt>
        <dd>{{ t(scoringValue) }}</dd>
      </div>
    </dl>

    <div class="ex-grid takeaways">
      <div v-for="item in benchTakeaways" :key="item.title.en" class="ex-card">
        <h3>{{ t(item.title) }}</h3>
        <p>{{ t(item.body) }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.snapshot {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 18px;
  margin: 0 0 28px;
  padding: 18px 22px;
  border: 1px solid var(--ex-border);
  border-radius: var(--ex-radius);
  background: var(--ex-surface-2);
}

.snapshot dt {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
}

.snapshot dd {
  margin: 5px 0 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--vp-c-text-1);
}

.snapshot a {
  color: var(--vp-c-brand-1);
  text-decoration: none;
}

.takeaways {
  margin-top: 4px;
}
</style>
