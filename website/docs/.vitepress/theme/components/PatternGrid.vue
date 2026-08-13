<script setup lang="ts">
import { computed } from 'vue'
import { useLocale } from '../composables/useLocale'
import { patterns } from '../data/patterns'
import { blob, tree } from '../data/site'
import { trackBySlug } from '../data/tracks'
import { ui } from '../data/ui'
import { inlineCode } from '../utils/text'

const props = withDefaults(
  defineProps<{ limit?: number; detailed?: boolean }>(),
  { detailed: false },
)

const { t, tl, link } = useLocale()

const visible = computed(() =>
  props.limit ? patterns.slice(0, props.limit) : patterns,
)

const sourceUrl = (path: string) => (path.endsWith('/') ? tree(path) : blob(path))
const sourceName = (path: string) => path.replace(/\/$/, '').split('/').slice(-1)[0]
</script>

<template>
  <div :class="detailed ? 'ex-grid-2' : 'ex-grid'">
    <article
      v-for="pattern in visible"
      :id="detailed ? pattern.id : undefined"
      :key="pattern.id"
      class="ex-card pattern"
    >
      <div class="pattern-head">
        <span class="pattern-icon">{{ pattern.icon }}</span>
        <div>
          <h3>{{ t(pattern.name) }}</h3>
          <p class="pattern-tagline">{{ t(pattern.tagline) }}</p>
        </div>
      </div>

      <ol class="pattern-flow">
        <li v-for="step in tl(pattern.flow)" :key="step">{{ step }}</li>
      </ol>

      <p v-if="detailed" class="pattern-body" v-html="inlineCode(t(pattern.description))" />

      <div class="pattern-foot">
        <div class="pattern-links">
          <span class="pattern-label">{{ t(ui.labels.viewSource) }}</span>
          <a
            v-for="path in pattern.source"
            :key="path"
            class="ex-chip"
            :href="sourceUrl(path)"
            target="_blank"
            rel="noreferrer"
          >
            {{ sourceName(path) }}
          </a>
        </div>
        <div v-if="pattern.tracks.length" class="pattern-links">
          <span class="pattern-label">{{ t(ui.labels.taughtIn) }}</span>
          <a
            v-for="slug in pattern.tracks"
            :key="slug"
            class="ex-badge is-topic"
            :href="link(`/learn/${slug}`)"
          >
            {{ t(ui.labels.track) }} {{ trackBySlug(slug)?.num }}
          </a>
        </div>
      </div>
    </article>
  </div>
</template>

<style scoped>
.pattern-head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.pattern-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-size: 17px;
  font-weight: 700;
}

.pattern-tagline {
  margin-top: 4px !important;
}

.pattern-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
}

.pattern-flow li {
  padding: 3px 9px;
  border-radius: 7px;
  border: 1px solid var(--ex-border);
  background: var(--ex-surface-2);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--vp-c-text-2);
}

.pattern-flow li + li::before {
  content: '→';
  margin-right: 7px;
  margin-left: -2px;
  color: var(--vp-c-text-3);
  font-weight: 500;
}

.pattern-body {
  font-size: 14.5px !important;
  line-height: 1.72 !important;
}

.pattern-foot {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--ex-border);
}

.pattern-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.pattern-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
  margin-right: 2px;
}

a.ex-chip:hover,
a.ex-badge:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

a.ex-chip,
a.ex-badge {
  text-decoration: none;
}
</style>
