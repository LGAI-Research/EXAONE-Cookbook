<script setup lang="ts">
import HomeHero from './HomeHero.vue'
import SectionHead from './SectionHead.vue'
import BuildGrid from './BuildGrid.vue'
import TrackPath from './TrackPath.vue'
import PatternGrid from './PatternGrid.vue'
import CookbookGrid from './CookbookGrid.vue'
import DemoGrid from './DemoGrid.vue'
import BenchTable from './BenchTable.vue'
import { useLocale } from '../composables/useLocale'
import { blob } from '../data/site'
import { ui } from '../data/ui'
import { inlineCode } from '../utils/text'

const { t, link } = useLocale()

const resources = [
  {
    title: { en: 'Playbook', ko: 'Playbook' },
    body: {
      en: 'The notebook-first practical guide, including proxy and SSL survival notes.',
      ko: '프록시·SSL 대응까지 담은 노트북 중심 실무 가이드.',
    },
    href: blob('PLAYBOOK.md'),
  },
  {
    title: { en: 'K-EXAONE 2.0 API', ko: 'K-EXAONE 2.0 API' },
    body: {
      en: '`enable_thinking`, `preserve_thinking` and what changes for agentic runs.',
      ko: '`enable_thinking` · `preserve_thinking`과 agentic 실행에서 달라지는 점.',
    },
    href: blob('docs/k_exaone_2.md'),
  },
  {
    title: { en: 'Library reference', ko: '라이브러리 레퍼런스' },
    body: {
      en: 'Module map for `exaone/` — llm, agents, tools, retrieval, memory, observability.',
      ko: '`exaone/` 모듈 맵 — llm · agents · tools · retrieval · memory · observability.',
    },
    href: blob('docs/exaone.md'),
  },
  {
    title: { en: 'Contributing', ko: '기여 가이드' },
    body: {
      en: 'Test layout, CI scope and the conventions this repository follows.',
      ko: '테스트 구성 · CI 범위 · 저장소가 따르는 규약.',
    },
    href: blob('CONTRIBUTING.md'),
  },
]

const resourceHead = {
  eyebrow: { en: 'Reference', ko: '레퍼런스' },
  title: { en: 'Go deeper in the repository', ko: '저장소에서 더 깊이 보기' },
}
</script>

<template>
  <div class="ex-page">
    <HomeHero />

    <section class="ex-section">
      <div class="ex-wrap">
        <SectionHead
          :eyebrow="ui.sections.build.eyebrow"
          :title="ui.sections.build.title"
          :body="ui.sections.build.body"
        />
        <BuildGrid />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <div class="head-row">
          <SectionHead
            :eyebrow="ui.sections.path.eyebrow"
            :title="ui.sections.path.title"
            :body="ui.sections.path.body"
          />
          <a class="ex-link-arrow" :href="link('/learn/')">{{ t(ui.labels.viewAll) }}</a>
        </div>
        <TrackPath />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <div class="head-row">
          <SectionHead
            :eyebrow="ui.sections.patterns.eyebrow"
            :title="ui.sections.patterns.title"
            :body="ui.sections.patterns.body"
          />
          <a class="ex-link-arrow" :href="link('/patterns/')">{{ t(ui.labels.viewAll) }}</a>
        </div>
        <PatternGrid :limit="6" />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <div class="head-row">
          <SectionHead
            :eyebrow="ui.sections.cookbooks.eyebrow"
            :title="ui.sections.cookbooks.title"
            :body="ui.sections.cookbooks.body"
          />
          <a class="ex-link-arrow" :href="link('/cookbooks/')">{{ t(ui.labels.viewAll) }}</a>
        </div>
        <CookbookGrid :limit="6" />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <div class="head-row">
          <SectionHead
            :eyebrow="ui.sections.bench.eyebrow"
            :title="ui.sections.bench.title"
            :body="ui.sections.bench.body"
          />
          <a class="ex-link-arrow" :href="link('/benchmarks')">{{ t(ui.labels.viewAll) }}</a>
        </div>
        <BenchTable :only="['M3', 'M4', 'M6', 'M8', 'M10', 'M7']" :show-definition="false" />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <div class="head-row">
          <SectionHead
            :eyebrow="ui.sections.demos.eyebrow"
            :title="ui.sections.demos.title"
            :body="ui.sections.demos.body"
          />
          <a class="ex-link-arrow" :href="link('/demos/')">{{ t(ui.labels.viewAll) }}</a>
        </div>
        <DemoGrid />
      </div>
    </section>

    <section class="ex-section">
      <div class="ex-wrap">
        <SectionHead :eyebrow="resourceHead.eyebrow" :title="resourceHead.title" />
        <div class="ex-grid">
          <a
            v-for="item in resources"
            :key="item.href"
            class="ex-card"
            :href="item.href"
            target="_blank"
            rel="noreferrer"
          >
            <h3>{{ t(item.title) }}</h3>
            <p v-html="inlineCode(t(item.body))" />
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.head-row .ex-section-head {
  margin-bottom: 36px;
}

.head-row > a {
  margin-bottom: 40px;
  white-space: nowrap;
}
</style>
