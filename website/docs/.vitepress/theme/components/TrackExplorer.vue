<script setup lang="ts">
import { computed, ref } from 'vue'
import MetaBadges from './MetaBadges.vue'
import { useLocale } from '../composables/useLocale'
import { tracks } from '../data/tracks'
import { DIFFICULTY_LABEL, TOPIC_LABEL } from '../data/site'
import type { Difficulty, Topic } from '../data/site'
import { ui } from '../data/ui'

const { t, locale, link } = useLocale()

const query = ref('')
const level = ref<Difficulty | 'all'>('all')
const topic = ref<Topic | 'all'>('all')

const levels: (Difficulty | 'all')[] = ['all', 'beginner', 'intermediate', 'advanced']

const topics = computed<(Topic | 'all')[]>(() => {
  const used = new Set<Topic>()
  tracks.forEach((track) => track.topics.forEach((item) => used.add(item)))
  return ['all', ...(Object.keys(TOPIC_LABEL) as Topic[]).filter((item) => used.has(item))]
})

const filtered = computed(() =>
  tracks.filter((track) => {
    if (level.value !== 'all' && track.difficulty !== level.value) return false
    if (topic.value !== 'all' && !track.topics.includes(topic.value)) return false

    const term = query.value.trim().toLowerCase()
    if (!term) return true

    const haystack = [
      track.num,
      t(track.title),
      t(track.summary),
      track.dir,
      ...track.notebooks.map((notebook) => notebook.file),
      ...track.topics.map((item) => TOPIC_LABEL[item][locale.value]),
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(term)
  }),
)

const dirty = computed(
  () => level.value !== 'all' || topic.value !== 'all' || query.value.trim() !== '',
)

const notebookCount = (count: number) =>
  count === 1
    ? t(ui.labels.notebookOne)
    : t(ui.labels.notebookMany).replace('{n}', String(count))

const reset = () => {
  level.value = 'all'
  topic.value = 'all'
  query.value = ''
}
</script>

<template>
  <div class="explorer">
    <div class="filters">
      <input
        v-model="query"
        class="search"
        type="search"
        :placeholder="t(ui.labels.search)"
        :aria-label="t(ui.labels.search)"
      />

      <div class="filter-group">
        <span class="filter-label">{{ t(ui.labels.difficulty) }}</span>
        <button
          v-for="item in levels"
          :key="item"
          type="button"
          class="pill"
          :class="{ 'is-active': level === item }"
          @click="level = item"
        >
          {{ item === 'all' ? t(ui.labels.all) : t(DIFFICULTY_LABEL[item]) }}
        </button>
      </div>

      <div class="filter-group">
        <span class="filter-label">{{ t(ui.labels.topic) }}</span>
        <button
          v-for="item in topics"
          :key="item"
          type="button"
          class="pill"
          :class="{ 'is-active': topic === item }"
          @click="topic = item"
        >
          {{ item === 'all' ? t(ui.labels.all) : t(TOPIC_LABEL[item]) }}
        </button>
      </div>

      <div class="filter-foot">
        <span>{{ filtered.length }} {{ t(ui.labels.results) }}</span>
        <button v-if="dirty" type="button" class="reset" @click="reset">
          {{ t(ui.labels.reset) }}
        </button>
      </div>
    </div>

    <div v-if="filtered.length" class="ex-grid">
      <a
        v-for="track in filtered"
        :key="track.slug"
        class="ex-card track"
        :href="link(`/learn/${track.slug}`)"
      >
        <div class="track-head">
          <span class="track-num">{{ track.num }}</span>
          <h3>{{ t(track.title) }}</h3>
        </div>
        <MetaBadges
          :difficulty="track.difficulty"
          :minutes="track.minutes"
          :topics="track.topics"
          :max-topics="2"
        />
        <p>{{ t(track.summary) }}</p>
        <span class="track-foot">{{ notebookCount(track.notebooks.length) }}</span>
      </a>
    </div>

    <p v-else class="empty">{{ t(ui.labels.empty) }}</p>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 26px;
  padding: 20px 22px;
  border: 1px solid var(--ex-border);
  border-radius: var(--ex-radius);
  background: var(--ex-surface-2);
}

.search {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--ex-border-strong);
  border-radius: 10px;
  background: var(--ex-surface);
  color: var(--vp-c-text-1);
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease;
}

.search:focus {
  border-color: var(--vp-c-brand-1);
}

.filter-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.filter-label {
  margin-right: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
}

.pill {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--ex-border);
  background: var(--ex-surface);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: border-color 0.16s ease, color 0.16s ease, background 0.16s ease;
}

.pill:hover {
  border-color: var(--vp-c-brand-2);
  color: var(--vp-c-brand-1);
}

.pill.is-active {
  border-color: transparent;
  background: var(--vp-c-brand-1);
  color: #fff;
}

.dark .pill.is-active {
  color: #14141b;
}

.filter-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12.5px;
  color: var(--vp-c-text-3);
}

.reset {
  border: none;
  background: none;
  padding: 0;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vp-c-brand-1);
  cursor: pointer;
}

.track-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.track-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex: none;
  border-radius: 10px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-family: var(--vp-font-family-mono);
  font-size: 13px;
  font-weight: 700;
}

.track-foot {
  margin-top: auto;
  padding-top: 12px;
  font-size: 12px;
  color: var(--vp-c-text-3);
}

.empty {
  padding: 48px 0;
  text-align: center;
  color: var(--vp-c-text-3);
}
</style>
