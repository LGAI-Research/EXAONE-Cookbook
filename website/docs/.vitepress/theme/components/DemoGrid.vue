<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import { demos } from '../data/demos'
import { tree } from '../data/site'
import { ui } from '../data/ui'
import { inlineCode } from '../utils/text'

withDefaults(defineProps<{ detailed?: boolean }>(), { detailed: false })

const { t, tl } = useLocale()
</script>

<template>
  <div :class="detailed ? 'ex-grid-2' : 'ex-grid'">
    <article v-for="demo in demos" :key="demo.id" class="ex-card demo">
      <div class="demo-head">
        <h3>{{ demo.name }}</h3>
        <span class="ex-badge is-beginner">{{ t(demo.status) }}</span>
      </div>

      <p v-html="inlineCode(t(demo.summary))" />

      <ul v-if="detailed" class="ex-list">
        <li v-for="item in tl(demo.details)" :key="item" v-html="inlineCode(item)" />
      </ul>

      <dl class="demo-meta">
        <div>
          <dt>{{ t(ui.labels.upstream) }}</dt>
          <dd>
            <a :href="demo.upstreamUrl" target="_blank" rel="noreferrer">{{ demo.upstream }}</a>
          </dd>
        </div>
        <div>
          <dt>{{ t(ui.labels.pinned) }}</dt>
          <dd class="ex-mono">{{ demo.pin }}</dd>
        </div>
      </dl>

      <code class="demo-cmd">{{ demo.command }}</code>

      <a class="ex-link-arrow" :href="tree(demo.dir)" target="_blank" rel="noreferrer">
        {{ t(ui.labels.viewSource) }}
      </a>
    </article>
  </div>
</template>

<style scoped>
.demo-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.demo-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin: 4px 0 0;
}

.demo-meta dt {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
}

.demo-meta dd {
  margin: 3px 0 0;
  font-size: 13.5px;
  color: var(--vp-c-text-2);
}

.demo-meta a {
  color: var(--vp-c-brand-1);
  text-decoration: none;
}

.demo-cmd {
  display: block;
  margin-top: auto;
  padding: 10px 12px;
  border-radius: 9px;
  border: 1px solid var(--ex-border);
  background: var(--ex-surface-2);
  font-family: var(--vp-font-family-mono);
  font-size: 11.5px;
  line-height: 1.5;
  color: var(--vp-c-text-2);
  overflow-x: auto;
  white-space: pre;
}
</style>
