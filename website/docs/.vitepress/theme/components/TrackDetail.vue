<script setup lang="ts">
import { computed } from 'vue'
import { useData } from 'vitepress'
import MetaBadges from './MetaBadges.vue'
import { useLocale } from '../composables/useLocale'
import { tracks, trackBySlug } from '../data/tracks'
import { patternById } from '../data/patterns'
import { blob, nbviewer, tree } from '../data/site'
import { ui } from '../data/ui'
import { inlineCode } from '../utils/text'

const { params } = useData()
const { t, tl, link } = useLocale()

const slug = computed(() => String(params.value?.track ?? ''))
const track = computed(() => trackBySlug(slug.value))
const index = computed(() => tracks.findIndex((item) => item.slug === slug.value))
const prev = computed(() => (index.value > 0 ? tracks[index.value - 1] : undefined))
const next = computed(() =>
  index.value >= 0 && index.value < tracks.length - 1 ? tracks[index.value + 1] : undefined,
)

const relatedPatterns = computed(() =>
  (track.value?.patterns ?? []).map(patternById).filter(Boolean),
)
</script>

<template>
  <article v-if="track" class="detail">
    <a class="back" :href="link('/learn/')">← {{ t(ui.hero.secondary) }}</a>

    <header class="detail-head">
      <span class="detail-num">{{ t(ui.labels.track) }} {{ track.num }}</span>
      <h1>{{ t(track.title) }}</h1>
      <p class="detail-summary">{{ t(track.summary) }}</p>
      <MetaBadges
        :difficulty="track.difficulty"
        :minutes="track.minutes"
        :topics="track.topics"
        :max-topics="6"
      />
      <div class="detail-actions">
        <a
          class="ex-btn ex-btn-primary"
          :href="tree(track.dir)"
          target="_blank"
          rel="noreferrer"
        >
          {{ t(ui.labels.openGithub) }}
        </a>
        <a class="ex-btn ex-btn-ghost" :href="link('/guide/quick-start')">
          {{ t(ui.labels.quickStart) }}
        </a>
      </div>
    </header>

    <div class="detail-body">
      <div class="detail-main">
        <section>
          <h2>{{ t(ui.labels.overview) }}</h2>
          <p class="prose" v-html="inlineCode(t(track.overview))" />
        </section>

        <section>
          <h2>{{ t(ui.labels.outcomes) }}</h2>
          <ul class="ex-list">
            <li
              v-for="item in tl(track.outcomes)"
              :key="item"
              v-html="inlineCode(item)"
            />
          </ul>
        </section>

        <section>
          <h2>{{ t(ui.labels.notebooks) }}</h2>
          <ul class="notebooks">
            <li v-for="notebook in track.notebooks" :key="notebook.file">
              <div>
                <code>{{ notebook.file }}</code>
                <span>{{ t(notebook.title) }}</span>
              </div>
              <div class="notebook-links">
                <a :href="blob(notebook.path)" target="_blank" rel="noreferrer">
                  {{ t(ui.labels.openGithub) }}
                </a>
                <a :href="nbviewer(notebook.path)" target="_blank" rel="noreferrer">
                  {{ t(ui.labels.preview) }}
                </a>
              </div>
            </li>
          </ul>
        </section>
      </div>

      <aside class="detail-aside">
        <div class="ex-card">
          <h3>{{ t(ui.labels.prerequisites) }}</h3>
          <ul class="ex-list">
            <li
              v-for="item in tl(track.prerequisites)"
              :key="item"
              v-html="inlineCode(item)"
            />
          </ul>
        </div>

        <div v-if="track.symbols.length" class="ex-card">
          <h3>{{ t(ui.labels.library) }}</h3>
          <div class="ex-badges">
            <span v-for="symbol in track.symbols" :key="symbol" class="ex-chip">{{ symbol }}</span>
          </div>
        </div>

        <div v-if="relatedPatterns.length" class="ex-card">
          <h3>{{ t(ui.labels.patternsUsed) }}</h3>
          <ul class="pattern-links">
            <li v-for="pattern in relatedPatterns" :key="pattern!.id">
              <a :href="`${link('/patterns/')}#${pattern!.id}`">
                <span>{{ pattern!.icon }}</span>{{ t(pattern!.name) }}
              </a>
            </li>
          </ul>
        </div>
      </aside>
    </div>

    <nav class="detail-nav">
      <a v-if="prev" class="nav-card" :href="link(`/learn/${prev.slug}`)">
        <span>← {{ t(ui.labels.prev) }}</span>
        <strong>{{ t(ui.labels.track) }} {{ prev.num }} · {{ t(prev.title) }}</strong>
      </a>
      <span v-else />
      <a v-if="next" class="nav-card is-next" :href="link(`/learn/${next.slug}`)">
        <span>{{ t(ui.labels.next) }} →</span>
        <strong>{{ t(ui.labels.track) }} {{ next.num }} · {{ t(next.title) }}</strong>
      </a>
    </nav>
  </article>
</template>

<style scoped>
.detail {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 24px 72px;
}

.back {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--vp-c-text-3);
  text-decoration: none;
}

.back:hover {
  color: var(--vp-c-brand-1);
}

.detail-head {
  margin-top: 16px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--ex-border);
}

.detail-num {
  display: inline-block;
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vp-c-brand-1);
}

.detail-head h1 {
  margin: 10px 0 0;
  font-size: clamp(30px, 4.4vw, 44px);
  line-height: 1.14;
  font-weight: 760;
  letter-spacing: -0.03em;
  border: 0;
  padding: 0;
}

.detail-summary {
  margin: 14px 0 18px;
  font-size: 17px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.detail-body {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(260px, 1fr);
  gap: 40px;
  padding-top: 34px;
}

.detail-main section + section {
  margin-top: 34px;
}

.detail-main h2 {
  margin: 0 0 14px;
  padding: 0;
  border: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.015em;
}

.prose {
  margin: 0;
  font-size: 15.5px;
  line-height: 1.78;
  color: var(--vp-c-text-2);
}

.notebooks {
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--ex-border);
  border-radius: var(--ex-radius);
  overflow: hidden;
}

.notebooks li {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-top: 1px solid var(--ex-border);
  background: var(--ex-surface);
}

.notebooks li:first-child {
  border-top: none;
}

.notebooks code {
  display: block;
  font-size: 12.5px;
  color: var(--vp-c-brand-1);
  background: none;
  padding: 0;
}

.notebooks span {
  display: block;
  margin-top: 3px;
  font-size: 13.5px;
  color: var(--vp-c-text-2);
}

.notebook-links {
  display: flex;
  gap: 14px;
  font-size: 13px;
  font-weight: 600;
}

.notebook-links a {
  color: var(--vp-c-brand-1);
  text-decoration: none;
}

.detail-aside {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: calc(var(--vp-nav-height) + 24px);
  align-self: start;
}

.detail-aside h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
  border: 0;
  padding: 0;
}

.pattern-links {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-links a {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--vp-c-text-2);
  text-decoration: none;
}

.pattern-links a:hover {
  color: var(--vp-c-brand-1);
}

.detail-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 56px;
}

.nav-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 16px 20px;
  border: 1px solid var(--ex-border);
  border-radius: var(--ex-radius);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s ease;
}

.nav-card:hover {
  border-color: var(--vp-c-brand-1);
}

.nav-card span {
  font-size: 12px;
  color: var(--vp-c-text-3);
}

.nav-card strong {
  font-size: 14.5px;
  font-weight: 640;
}

.nav-card.is-next {
  text-align: right;
}

@media (max-width: 900px) {
  .detail-body {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .detail-aside {
    position: static;
  }
  .detail-nav {
    grid-template-columns: 1fr;
  }
}
</style>
